"""Languages endpoint."""

from typing import List, Dict, Any
from fastapi import APIRouter
from app.core.constants import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

router = APIRouter(prefix="/languages", tags=["Languages"])


@router.get("", response_model=Dict[str, Any])
async def get_supported_languages() -> Dict[str, Any]:
    """Returns list of supported languages and metadata."""
    return {
        "supported_languages": [
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "ta", "name": "Tamil", "native_name": "தமிழ்"},
        ],
        "default": DEFAULT_LANGUAGE,
    }

