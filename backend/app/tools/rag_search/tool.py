"""RAG Search Tool combining Google Gemini Embeddings and Vector Search with in-memory resilient fallback."""

from typing import Dict, Any, List, Optional
import numpy as np
from app.core.config import settings
from app.core.logging import logger
from app.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult
from app.db.repositories import DocumentChunkRepository
from app.db.supabase import is_db_connected, SessionLocal
from sqlalchemy import text


class RAGSearchTool(BaseTool):
    """
    RAG Search tool for querying verified schemes, policy gazettes, guidelines,
    and official eligibility criteria via Gemini embeddings and pgvector (or resilient chunk search).
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="rag_search",
            display_name="RAG Knowledge Search",
            description=(
                "Retrieves verified, authentic government scheme documentation, Tamil Nadu MSME rules, "
                "subsidies, and eligibility guidelines from internal vector storage."
            ),
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="The search or question query (e.g. 'NEEDS scheme 25% subsidy maximum limit', 'UYEGP eligibility age').",
                    required=True,
                ),
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="Maximum number of relevant knowledge chunks to retrieve (default: 4).",
                    required=False,
                    default=4,
                ),
            ],
            category="retrieval",
            requires_auth=False,
            is_available=True,
        )

    async def get_gemini_embedding(self, text_input: str) -> Optional[List[float]]:
        """Generates embeddings using Google Gemini API if configured."""
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            return None

        try:
            # Try new google-genai client first
            from google import genai
            client = genai.Client(api_key=api_key)
            result = client.models.embed_content(
                model=settings.EMBEDDING_MODEL if "embedding" in settings.EMBEDDING_MODEL else "text-embedding-004",
                contents=text_input,
            )
            if hasattr(result, "embeddings") and result.embeddings:
                return result.embeddings[0].values
        except Exception:
            pass

        try:
            # Fallback to google.generativeai
            import google.generativeai as gai
            gai.configure(api_key=api_key)
            model_name = settings.EMBEDDING_MODEL if "embedding" in settings.EMBEDDING_MODEL else "models/text-embedding-004"
            res = gai.embed_content(
                model=model_name,
                content=text_input,
                task_type="retrieval_query",
            )
            if "embedding" in res:
                return res["embedding"]
        except Exception as e:
            logger.warning(f"Gemini embedding generation failed: {e}")

        return None

    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "").strip()
        limit = int(kwargs.get("limit", 4))

        if not query:
            return ToolResult(
                tool_name="rag_search",
                success=False,
                error="Query cannot be empty for RAG search.",
            )

        # 1. Attempt Supabase pgvector search if connected
        chunks_found = []
        source_mode = "in_memory_repository"

        if is_db_connected and SessionLocal:
            try:
                embedding = await self.get_gemini_embedding(query)
                if embedding:
                    with SessionLocal() as db:
                        # Query document_chunks using pgvector cosine distance if column exists
                        sql = text("""
                            SELECT id, scheme_id, content, metadata
                            FROM document_chunks
                            ORDER BY embedding <=> :embedding
                            LIMIT :limit;
                        """)
                        rows = db.execute(sql, {"embedding": str(embedding), "limit": limit}).fetchall()
                        for row in rows:
                            chunks_found.append({
                                "id": row[0],
                                "scheme_id": row[1],
                                "content": row[2],
                                "metadata": row[3] or {},
                            })
                        if chunks_found:
                            source_mode = "supabase_pgvector"
            except Exception as dbe:
                logger.info(f"Supabase pgvector query bypassed or failed: {dbe}. Falling back to internal chunk repository.")

        # 2. Resilient fallback to DocumentChunkRepository
        if not chunks_found:
            repo_chunks = DocumentChunkRepository.search(query=query, limit=limit)
            for c in repo_chunks:
                chunks_found.append({
                    "id": c.get("id"),
                    "title": c.get("title"),
                    "url": c.get("url"),
                    "content": c.get("content"),
                    "state": c.get("state"),
                    "category": c.get("category"),
                })

        return ToolResult(
            tool_name="rag_search",
            success=True,
            data={
                "query": query,
                "matches_count": len(chunks_found),
                "chunks": chunks_found,
            },
            metadata={"source": source_mode, "retrieved_chunks": len(chunks_found)},
        )
