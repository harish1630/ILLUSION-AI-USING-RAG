"""Canonical Authentication API Endpoints under /api/v1/auth."""

import urllib.parse
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field

from app.core.config import settings
from app.core.logging import logger
from app.auth.jwt import jwt_manager, TokenPair, TokenPayload
from app.auth.service import auth_service
from app.auth.oauth import google_auth
from app.auth.dependencies import get_current_user, get_current_user_optional, CurrentUser

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    username: str
    name: Optional[str] = None
    picture: Optional[str] = None
    roles: List[str] = Field(default_factory=lambda: ["user"])
    is_active: bool = True
    is_verified: bool = False


class AuthResponse(BaseModel):
    user: UserProfileResponse
    tokens: TokenPair
    message: str = "Success"


# ---------------------------------------------------------------------------
# Helper: Cookie Management
# ---------------------------------------------------------------------------

def _set_auth_cookies(response: Response, tokens: TokenPair):
    """Sets secure HttpOnly session cookies for seamless client authentication."""
    is_prod = settings.APP_ENV == "production"
    # Access token cookie (1 hour)
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    # Refresh token cookie (7 days)
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )


def _clear_auth_cookies(response: Response):
    """Clears authentication cookies."""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")


# ---------------------------------------------------------------------------
# 1. Registration & Login
# ---------------------------------------------------------------------------

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, response: Response):
    """Registers a new user using Argon2id password hashing and returns token bundle."""
    try:
        user_dict, tokens = auth_service.register(
            email=req.email,
            username=req.username,
            password=req.password,
            full_name=req.full_name,
        )
        _set_auth_cookies(response, tokens)
        return AuthResponse(
            user=UserProfileResponse(
                user_id=user_dict["id"],
                email=user_dict["email"],
                username=user_dict["username"],
                name=user_dict.get("full_name"),
                picture=user_dict.get("picture"),
                roles=user_dict.get("roles", ["user"]),
                is_active=user_dict.get("is_active", True),
                is_verified=user_dict.get("is_verified", False),
            ),
            tokens=tokens,
            message="User registered successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed")


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, request: Request, response: Response):
    """Authenticates user with username/email and password using Argon2id verification."""
    try:
        ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        user_dict, tokens = auth_service.login(
            username_or_email=req.username_or_email,
            password=req.password,
            ip_address=ip,
            user_agent=user_agent,
        )
        _set_auth_cookies(response, tokens)
        return AuthResponse(
            user=UserProfileResponse(
                user_id=user_dict["id"],
                email=user_dict["email"],
                username=user_dict["username"],
                name=user_dict.get("full_name"),
                picture=user_dict.get("picture"),
                roles=user_dict.get("roles", ["user"]),
                is_active=user_dict.get("is_active", True),
                is_verified=user_dict.get("is_verified", False),
            ),
            tokens=tokens,
            message="Login successful",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")


# ---------------------------------------------------------------------------
# 2. Google OAuth 2.0 (Strictly for User Authentication)
# ---------------------------------------------------------------------------

@router.get("/google/url")
async def get_google_auth_url(redirect_uri: Optional[str] = Query(None)):
    """Generates a secure Google OAuth login authorization URL with PKCE."""
    auth_url, state = google_auth.generate_login_url(redirect_uri)
    return {
        "auth_url": auth_url,
        "state": state,
        "provider": "google",
        "scopes": google_auth.LOGIN_SCOPES,
    }


@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    code: str = Query(...),
    state: str = Query(...),
):
    """Canonical Google OAuth callback endpoint. Validates state, logs in, sets cookies."""
    try:
        google_info = await google_auth.exchange_code(code, state)
        ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        user_dict, tokens = auth_service.login_with_google(
            info=google_info,
            ip_address=ip,
            user_agent=user_agent,
        )

        frontend_base = settings.FRONTEND_URL
        if "localhost:5173" in frontend_base:
            frontend_base = "http://localhost:3000"
        frontend_redirect = f"{frontend_base}/chat?auth_success=true"
        redirect_resp = RedirectResponse(url=frontend_redirect, status_code=status.HTTP_302_FOUND)
        _set_auth_cookies(redirect_resp, tokens)
        return redirect_resp
    except ValueError as e:
        logger.error(f"Google OAuth callback validation failed: {e}")
        frontend_base = settings.FRONTEND_URL
        if "localhost:5173" in frontend_base:
            frontend_base = "http://localhost:3000"
        error_url = f"{frontend_base}/login?error={urllib.parse.quote(str(e))}"
        return RedirectResponse(url=error_url, status_code=status.HTTP_302_FOUND)
    except Exception as e:
        logger.error(f"Unexpected Google OAuth error: {e}")
        frontend_base = settings.FRONTEND_URL
        if "localhost:5173" in frontend_base:
            frontend_base = "http://localhost:3000"
        return RedirectResponse(
            url=f"{frontend_base}/login?error=oauth_failed",
            status_code=status.HTTP_302_FOUND,
        )


# ---------------------------------------------------------------------------
# 3. Refresh-Token Rotation & Reuse Detection
# ---------------------------------------------------------------------------

@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(req: RefreshRequest, request: Request, response: Response):
    """Refreshes access token with rotation and automatic reuse detection."""
    refresh_token = req.refresh_token or request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required in request body or cookie",
        )

    new_tokens = jwt_manager.rotate_refresh_token(refresh_token)
    if not new_tokens:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or reused refresh token. Please sign in again.",
        )

    _set_auth_cookies(response, new_tokens)
    return new_tokens


# ---------------------------------------------------------------------------
# 4. Logout & Session Revocation
# ---------------------------------------------------------------------------

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Revokes session and clears all authentication cookies."""
    # Revoke tokens from headers and cookies
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        jwt_manager.revoke_token(auth_header.split(" ", 1)[1])

    cookie_refresh = request.cookies.get("refresh_token")
    if cookie_refresh:
        jwt_manager.revoke_token(cookie_refresh)

    if current_user and current_user.session_id:
        jwt_manager.revoke_session(current_user.session_id)

    _clear_auth_cookies(response)
    return {"message": "Successfully logged out", "status": "revoked"}


# ---------------------------------------------------------------------------
# 5. Password Reset Workflow
# ---------------------------------------------------------------------------

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    """Initiates secure password reset workflow without exposing user existence."""
    token = auth_service.request_password_reset(req.email)
    return {
        "message": "If an account exists with that email, a password reset link has been dispatched.",
        "status": "dispatched",
        # In non-production, return token for developer test ease
        "debug_token": token if settings.APP_ENV != "production" else None,
    }


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    """Resets user password with valid reset token and Argon2id hashing."""
    try:
        auth_service.reset_password(token=req.token, new_password=req.new_password)
        return {"message": "Password has been successfully updated. You may now log in.", "status": "updated"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# 6. Authenticated User Profile
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user: CurrentUser = Depends(get_current_user)):
    """Returns the profile of the currently authenticated user."""
    profile = auth_service.get_user_profile(current_user.sub)
    if not profile:
        return UserProfileResponse(
            user_id=current_user.sub,
            email=current_user.email,
            username=current_user.email.split("@")[0],
            name=current_user.name,
            picture=current_user.picture,
            roles=current_user.roles,
            is_active=True,
            is_verified=True,
        )
    return UserProfileResponse(**profile)
