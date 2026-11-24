"""Authentication dependencies for FastAPI route handlers."""

from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt import jwt_manager, TokenPayload
from app.auth.service import auth_service

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> TokenPayload:
    """Extracts and verifies JWT access token from Authorization header or HttpOnly cookie."""
    token: Optional[str] = None

    # 1. Check Bearer Authorization header
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials

    # 2. Check HttpOnly cookie
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token or session cookie.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = jwt_manager.verify_token(token, expected_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Optional[TokenPayload]:
    """Optional user dependency. Returns active user payload if valid token is provided, or None."""
    token: Optional[str] = None

    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials

    if not token:
        token = request.cookies.get("access_token")

    if not token:
        return None

    return jwt_manager.verify_token(token, expected_type="access")


def require_roles(required_roles: List[str]) -> Callable:
    """Dependency factory enforcing Role-Based Access Control (RBAC)."""
    async def role_checker(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        user_roles = set(current_user.roles)
        if not any(req in user_roles for req in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {required_roles}",
            )
        return current_user

    return role_checker


CurrentUser = TokenPayload
