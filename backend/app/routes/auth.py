"""Authentication Router and Compatibility Module for Illusion AI.
Exports canonical routes from app.auth package.
"""

from app.auth.routes import router
from app.auth.dependencies import (
    get_current_user,
    get_current_user_optional,
    CurrentUser,
    require_roles,
)
from app.auth.jwt import TokenPayload, TokenPair, jwt_manager
from app.auth.service import auth_service

__all__ = [
    "router",
    "get_current_user",
    "get_current_user_optional",
    "CurrentUser",
    "require_roles",
    "TokenPayload",
    "TokenPair",
    "jwt_manager",
    "auth_service",
]
