"""Authentication Compatibility Module for Illusion AI.
User authentication has been disabled per user requirement.
All endpoints run with default open access.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TokenPayload(BaseModel):
    sub: str = "default_user"
    user_id: str = "default_user"
    email: str = "founder@illusion.ai"
    roles: List[str] = Field(default_factory=lambda: ["user", "founder"])


CurrentUser = TokenPayload


async def get_current_user() -> TokenPayload:
    """Pass-through user provider returning default active user."""
    return TokenPayload()


async def get_current_user_optional() -> Optional[TokenPayload]:
    """Pass-through optional user provider returning default active user."""
    return TokenPayload()


@router.get("/me")
async def get_my_profile():
    return {
        "user_id": "default_user",
        "email": "founder@illusion.ai",
        "name": "Entrepreneur",
        "roles": ["user", "founder"],
    }
