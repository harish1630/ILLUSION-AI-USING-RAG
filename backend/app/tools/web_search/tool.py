"""Web Search Tool using Tavily API for real-time online business & scheme information."""

from typing import Dict, Any, List, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult


class WebSearchTool(BaseTool):
    """
    Real-time web search tool utilizing Tavily Search API.
    Designed specifically for AI agents with answer generation, summaries, and source URLs.
    Includes fallback simulated results if API key is not yet configured, preventing system failure.
    """

    TAVILY_API_ENDPOINT = "https://api.tavily.com/search"

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="web_search",
            display_name="Web Search",
            description=(
                "Performs real-time search across the web for current government notifications, latest scheme updates, "
                "Tamil Nadu gazette changes, market trends, and official portals using Tavily API."
            ),
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="The search query (e.g. 'Tamil Nadu NEEDS scheme subsidy revision 2026', 'Udyam portal circular').",
                    required=True,
                ),
                ToolParameter(
                    name="max_results",
                    type="integer",
                    description="Maximum number of search results to retrieve (default: 5).",
                    required=False,
                    default=5,
                ),
            ],
            category="search",
            requires_auth=False,
            is_available=bool(settings.TAVILY_API_KEY),
        )

    def check_availability(self) -> bool:
        return bool(settings.TAVILY_API_KEY)

    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "").strip()
        max_results = int(kwargs.get("max_results", 5))

        if not query:
            return ToolResult(
                tool_name="web_search",
                success=False,
                error="Search query cannot be empty.",
            )

        api_key = settings.TAVILY_API_KEY
        if not api_key or api_key == "your_tavily_api_key_here":
            logger.warning("Tavily API key not configured or placeholder detected. Returning informational fallback.")
            return ToolResult(
                tool_name="web_search",
                success=True,
                data={
                    "query": query,
                    "answer": f"Simulated web search for: '{query}'. Configure TAVILY_API_KEY in .env for live web search.",
                    "results": [
                        {
                            "title": "Government of Tamil Nadu - MSME Online Services",
                            "url": "https://msmeonline.tn.gov.in/",
                            "content": f"Official single-window portal for NEEDS, UYEGP and capital subsidies in Tamil Nadu relevant to {query}.",
                            "score": 0.95,
                        },
                        {
                            "title": "Ministry of MSME - Government of India",
                            "url": "https://msme.gov.in/",
                            "content": f"Central government portal covering PMEGP, CGTMSE credit guarantee and MSME registration guidelines for {query}.",
                            "score": 0.90,
                        },
                    ],
                },
                metadata={"source": "simulated_fallback", "api_key_configured": False},
            )

        try:
            payload = {
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "max_results": max_results,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.TAVILY_API_ENDPOINT, json=payload)

            if response.status_code != 200:
                logger.error(f"Tavily search API responded with status {response.status_code}: {response.text}")
                return ToolResult(
                    tool_name="web_search",
                    success=False,
                    error=f"Tavily API returned status {response.status_code}",
                    metadata={"status_code": response.status_code},
                )

            res_json = response.json()
            results = res_json.get("results", [])
            answer = res_json.get("answer")

            # Extract clean results for LLM injection
            formatted_results = []
            for item in results:
                formatted_results.append({
                    "title": item.get("title", "Untitled"),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0),
                })

            return ToolResult(
                tool_name="web_search",
                success=True,
                data={
                    "query": query,
                    "answer": answer,
                    "results": formatted_results,
                },
                metadata={"total_results": len(formatted_results), "source": "tavily_live"},
            )

        except httpx.TimeoutException:
            logger.warning(f"Tavily web search timed out for query '{query}'")
            return ToolResult(
                tool_name="web_search",
                success=False,
                error="Web search request timed out.",
            )
        except Exception as e:
            logger.error(f"Tavily search execution failed: {e}")
            return ToolResult(
                tool_name="web_search",
                success=False,
                error=f"Web search error: {str(e)}",
            )
