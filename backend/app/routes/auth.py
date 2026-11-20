"""FastAPI Authentication Routes for Google OAuth and Token Management."""

from typing import Optional, Dict, Any
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException, Depends, status, Header, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from auth.google_oauth import google_oauth_service, GoogleUserInfo
from services.token_manager import token_manager, TokenPair, TokenPayload
from app.core.config import settings
from app.core.logging import logger
from app.core.security import hash_password, verify_password, generate_reset_token
from app.db.repositories import UserRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])
security_bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class GoogleAuthUrlResponse(BaseModel):
    authorization_url: str
    client_id_configured: bool


class GoogleAuthCodeRequest(BaseModel):
    code: str = Field(..., min_length=1, description="Google OAuth authorization code")
    redirect_uri: Optional[str] = Field(default=None, description="Matching redirect URI")


class GoogleAuthResponse(BaseModel):
    user: GoogleUserInfo
    tokens: TokenPair


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=6, description="Password (at least 6 characters)")
    full_name: Optional[str] = Field(default=None, description="Full name or company name")


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=1, description="Username or Email ID")
    password: str = Field(..., min_length=1, description="Account password")


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=3, description="Registered email ID")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1, description="Password reset token")
    new_password: str = Field(..., min_length=6, description="New password (at least 6 characters)")


class AuthUser(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    picture: Optional[str] = None


class UserAuthResponse(BaseModel):
    user: AuthUser
    tokens: TokenPair


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="Valid JWT refresh token")


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    roles: list[str]


# ---------------------------------------------------------------------------
# FastAPI Dependencies for Protected Endpoints
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> TokenPayload:
    """Dependency that requires a valid, unexpired JWT bearer access token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = token_manager.verify_token(token, expected_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Optional[TokenPayload]:
    """Optional authentication dependency; returns None if guest/unauthenticated."""
    if not credentials or not credentials.credentials:
        return None
    return token_manager.verify_token(credentials.credentials, expected_type="access")


# ---------------------------------------------------------------------------
# Auth Endpoints
# ---------------------------------------------------------------------------

@router.get("/google/url", response_model=GoogleAuthUrlResponse)
async def get_google_auth_url(state: Optional[str] = None):
    """Generates the Google OAuth 2.0 login URL for frontend redirection."""
    auth_url = google_oauth_service.get_authorization_url(state=state)
    has_id = bool(google_oauth_service.client_id)

    return GoogleAuthUrlResponse(
        authorization_url=auth_url,
        client_id_configured=has_id,
    )


@router.get("/google/callback")
async def google_auth_callback_get(
    code: str = Query(..., description="Google OAuth authorization code"),
    state: Optional[str] = Query(None, description="Optional OAuth state"),
    format: Optional[str] = Query("redirect", description="'redirect' to frontend or 'json' for raw output"),
):
    """
    GET handler for Google OAuth redirect flow.
    Exchanges code for tokens, extracts user info, and redirects browser to FRONTEND_URL.
    """
    try:
        # Exchange authorization code using the configured redirect URI
        google_tokens = await google_oauth_service.exchange_code_for_tokens(
            code=code,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )

        id_token_str = google_tokens.get("id_token")
        access_token_str = google_tokens.get("access_token")

        if id_token_str:
            try:
                user_info = google_oauth_service.verify_id_token(id_token_str)
            except Exception:
                user_info = await google_oauth_service.get_user_info_from_access_token(access_token_str)
        elif access_token_str:
            user_info = await google_oauth_service.get_user_info_from_access_token(access_token_str)
        else:
            raise ValueError("No id_token or access_token received from Google.")

        tokens = token_manager.create_token_pair(
            user_id=user_info.google_id,
            email=user_info.email,
            name=user_info.name,
            picture=user_info.picture,
        )

        if format == "json":
            return {"user": user_info.model_dump(), "tokens": tokens.model_dump()}

        # Redirect browser back to FRONTEND_URL
        redirect_params = {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "user_id": user_info.google_id,
            "email": user_info.email,
        }
        target_url = f"{settings.FRONTEND_URL}/auth/callback?{urlencode(redirect_params)}"
        return RedirectResponse(url=target_url, status_code=status.HTTP_302_FOUND)

    except Exception as e:
        logger.error(f"Google OAuth GET callback error: {e}")
        if format == "json":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        err_url = f"{settings.FRONTEND_URL}/auth/error?{urlencode({'error': str(e)})}"
        return RedirectResponse(url=err_url, status_code=status.HTTP_302_FOUND)


@router.post("/google/callback", response_model=GoogleAuthResponse)
async def google_auth_callback(req: GoogleAuthCodeRequest):
    """
    Exchanges Google authorization code for tokens, retrieves user profile,
    and returns Illusion AI JWT access & refresh tokens.
    """
    try:
        # 1. Exchange authorization code for Google tokens
        google_tokens = await google_oauth_service.exchange_code_for_tokens(
            code=req.code,
            redirect_uri=req.redirect_uri,
        )

        id_token_str = google_tokens.get("id_token")
        access_token_str = google_tokens.get("access_token")

        # 2. Extract verified user profile
        if id_token_str:
            try:
                user_info = google_oauth_service.verify_id_token(id_token_str)
            except Exception:
                # Fallback to userinfo API if direct verification needs public JWKS access
                user_info = await google_oauth_service.get_user_info_from_access_token(access_token_str)
        elif access_token_str:
            user_info = await google_oauth_service.get_user_info_from_access_token(access_token_str)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No id_token or access_token received from Google.",
            )

        # 3. Issue Illusion AI JWT tokens
        tokens = token_manager.create_token_pair(
            user_id=user_info.google_id,
            email=user_info.email,
            name=user_info.name,
            picture=user_info.picture,
        )

        return GoogleAuthResponse(user=user_info, tokens=tokens)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}",
        )


@router.post("/register", response_model=UserAuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(req: RegisterRequest):
    """
    Register a new user account with Email ID, Username, and Password.
    """
    clean_email = req.email.strip().lower()
    clean_username = req.username.strip().lower()

    # Basic validations
    if "@" not in clean_email or "." not in clean_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format.",
        )

    if UserRepository.get_by_email(clean_email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    if UserRepository.get_by_username(clean_username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken. Please choose another.",
        )

    # Securely hash password
    hashed = hash_password(req.password)

    # Persist user
    user = UserRepository.create_user(
        email=clean_email,
        username=clean_username,
        hashed_password=hashed,
        full_name=req.full_name,
    )

    # Generate JWT token pair
    tokens = token_manager.create_token_pair(
        user_id=user["id"],
        email=user["email"],
        name=user.get("full_name"),
    )

    return UserAuthResponse(
        user=AuthUser(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            full_name=user.get("full_name"),
            picture=user.get("picture"),
        ),
        tokens=tokens,
    )


@router.post("/login", response_model=UserAuthResponse)
async def login_user(req: LoginRequest):
    """
    Authenticate using Username OR Email ID + Password.
    """
    identifier = req.username_or_email.strip()
    user = UserRepository.get_by_identifier(identifier)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
        )

    stored_hash = user.get("hashed_password")
    if not stored_hash or not verify_password(req.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
        )

    # Generate JWT token pair
    tokens = token_manager.create_token_pair(
        user_id=user["id"],
        email=user["email"],
        name=user.get("full_name"),
        picture=user.get("picture"),
    )

    return UserAuthResponse(
        user=AuthUser(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            full_name=user.get("full_name"),
            picture=user.get("picture"),
        ),
        tokens=tokens,
    )


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    """
    Initiate password reset. Generates a secure reset token valid for 15 minutes.
    """
    clean_email = req.email.strip().lower()
    user = UserRepository.get_by_email(clean_email)

    # Security best practice: don't reveal whether user exists to prevent email enumeration,
    # but for development and demo, return token when user exists.
    if not user:
        return {
            "status": "success",
            "message": "If this email is registered, you will receive password reset instructions.",
            "reset_token": None,
        }

    reset_token = generate_reset_token()
    UserRepository.set_reset_token(clean_email, reset_token, expires_in_minutes=15)

    logger.info(f"Generated password reset token for {clean_email}")
    return {
        "status": "success",
        "message": "Password reset token generated successfully (valid for 15 minutes).",
        "reset_token": reset_token,
    }


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    """
    Reset password using a valid reset token.
    """
    new_hashed = hash_password(req.new_password)
    success = UserRepository.reset_password(req.token, new_hashed)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    return {
        "status": "success",
        "message": "Password has been reset successfully. You can now log in with your new password.",
    }


@router.post("/refresh", response_model=TokenPair)
async def refresh_access_token(req: RefreshTokenRequest):
    """Refreshes an expired access token using a valid refresh token."""
    new_tokens = token_manager.refresh_access_token(req.refresh_token)
    if not new_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or already used refresh token.",
        )
    return new_tokens


@router.post("/logout")
async def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
):
    """Revokes the current access token."""
    if credentials and credentials.credentials:
        token_manager.revoke_token(credentials.credentials)
    return {"status": "logged_out", "message": "Token revoked successfully"}


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(current_user: TokenPayload = Depends(get_current_user)):
    """Returns the authenticated user's profile claims from their active session."""
    return UserProfileResponse(
        user_id=current_user.sub,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        roles=current_user.roles,
    )
