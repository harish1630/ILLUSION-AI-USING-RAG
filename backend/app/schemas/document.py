"""Pydantic schemas for Document Ingestion and Chunks."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: str
    title: str
    source_url: Optional[str] = None
    language: str
    chunks_count: int
    content_hash: str
    created_at: datetime


class DocumentChunkSchema(BaseModel):
    id: str
    document_id: str
    scheme_id: Optional[str] = None
    chunk_index: int
    content: str
    language: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

