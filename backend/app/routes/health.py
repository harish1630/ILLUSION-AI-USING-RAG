"""Health check endpoint."""

from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """Returns application status and dependency connectivity status without exposing sensitive credentials."""
    db_configured = bool(settings.effective_database_url)
    groq_configured = bool(settings.GROQ_API_KEY)
    gemini_configured = bool(settings.GOOGLE_API_KEY)
    
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "services": {
            "database_configured": db_configured,
            "groq_configured": groq_configured,
            "gemini_configured": gemini_configured,
            "embedding_model": settings.EMBEDDING_MODEL,
            "embedding_dimension": settings.EMBEDDING_DIMENSION,
        },
    }

