"""Illusion AI Centralized Production-Ready Authentication Package."""

from app.auth.routes import router as auth_router
from app.auth.jwt import jwt_manager, TokenPair, TokenPayload
from app.auth.service import auth_service
from app.auth.dependencies import (
    get_current_user,
    get_current_user_optional,
    CurrentUser,
    require_roles,
)
from app.auth.oauth import google_auth

__all__ = [
    "auth_router",
    "jwt_manager",
    "TokenPair",
    "TokenPayload",
    "auth_service",
    "get_current_user",
    "get_current_user_optional",
    "CurrentUser",
    "require_roles",
    "google_auth",
]
