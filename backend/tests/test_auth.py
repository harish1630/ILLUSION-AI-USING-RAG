"""Automated tests for Google OAuth and JWT Token Manager."""

import pytest
import time
from datetime import timedelta
from fastapi.testclient import TestClient
from app.main import app
from auth.google_oauth import GoogleOAuthService, GoogleUserInfo
from services.token_manager import TokenManager, token_manager, TokenPair, TokenPayload


@pytest.fixture
def client():
    return TestClient(app)


# ===================================================================
# 1. Google OAuth Service Unit Tests
# ===================================================================

def test_google_oauth_auth_url_generation():
    """Verify Google OAuth authorization URL formatting and parameters."""
    service = GoogleOAuthService(
        client_id="test-client-id-123.apps.googleusercontent.com",
        client_secret="test-secret-456",
        redirect_uri="http://localhost:3000/auth/callback",
    )

    url = service.get_authorization_url(state="xyz987state")
    assert "https://accounts.google.com/o/oauth2/v2/auth" in url
    assert "client_id=test-client-id-123.apps.googleusercontent.com" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fauth%2Fcallback" in url
    assert "response_type=code" in url
    assert "state=xyz987state" in url
    assert "openid" in url


def test_google_user_info_schema():
    """Verify GoogleUserInfo validation."""
    info = GoogleUserInfo(
        google_id="google-10928374",
        email="founder@startup.tn.gov.in",
        name="Tamil Entrepreneur",
        given_name="Tamil",
        family_name="Entrepreneur",
        picture="https://lh3.googleusercontent.com/avatar.jpg",
        email_verified=True,
    )
    assert info.google_id == "google-10928374"
    assert info.email == "founder@startup.tn.gov.in"
    assert info.email_verified is True


def test_google_invalid_id_token():
    """Invalid Google ID token should raise ValueError."""
    service = GoogleOAuthService(client_id="test-id")
    with pytest.raises(ValueError, match="Invalid Google ID token"):
        service.verify_id_token("invalid.token.signature")


# ===================================================================
# 2. Token Manager Unit Tests
# ===================================================================

def test_token_manager_create_and_verify_access_token():
    """Verify JWT access token creation and decoding."""
    tm = TokenManager(secret_key="unit_test_secret_key_at_least_32_bytes_long_123456", algorithm="HS256")
    token = tm.create_access_token(
        user_id="user-999",
        email="test@illusion.ai",
        name="John Doe",
        picture="https://example.com/pic.jpg",
        roles=["user", "entrepreneur"],
    )

    assert isinstance(token, str)
    assert len(token) > 20

    payload = tm.verify_token(token, expected_type="access")
    assert payload is not None
    assert payload.sub == "user-999"
    assert payload.email == "test@illusion.ai"
    assert payload.name == "John Doe"
    assert "entrepreneur" in payload.roles
    assert payload.token_type == "access"


def test_token_manager_create_and_verify_refresh_token():
    """Verify JWT refresh token creation and decoding."""
    tm = TokenManager(secret_key="unit_test_secret_key_at_least_32_bytes_long_123456", algorithm="HS256")
    refresh_token = tm.create_refresh_token(
        user_id="user-999",
        email="test@illusion.ai",
    )

    payload = tm.verify_token(refresh_token, expected_type="refresh")
    assert payload is not None
    assert payload.sub == "user-999"
    assert payload.token_type == "refresh"

    # Verifying refresh token as access token must fail
    wrong_type = tm.verify_token(refresh_token, expected_type="access")
    assert wrong_type is None


def test_token_manager_create_token_pair():
    """Verify creation of complete token pair."""
    tm = TokenManager(secret_key="unit_test_secret_key_at_least_32_bytes_long_123456", algorithm="HS256")
    pair = tm.create_token_pair(
        user_id="user-123",
        email="user123@example.com",
        name="Jane Doe",
    )

    assert isinstance(pair, TokenPair)
    assert pair.token_type == "bearer"
    assert pair.expires_in == 3600

    acc_payload = tm.verify_token(pair.access_token, expected_type="access")
    ref_payload = tm.verify_token(pair.refresh_token, expected_type="refresh")

    assert acc_payload is not None
    assert ref_payload is not None
    assert acc_payload.sub == "user-123"
    assert ref_payload.sub == "user-123"


def test_token_manager_revocation_blacklist():
    """Verify that revoked tokens cannot be used again."""
    tm = TokenManager(secret_key="unit_test_secret_key_at_least_32_bytes_long_123456", algorithm="HS256")
    token = tm.create_access_token(user_id="user-revoked", email="revoked@illusion.ai")

    # Valid before revocation
    assert tm.verify_token(token) is not None

    # Revoke
    revoked = tm.revoke_token(token)
    assert revoked is True

    # After revocation, decode and verify must fail
    assert tm.verify_token(token) is None


def test_token_manager_refresh_cycle():
    """Verify token rotation when refreshing access token."""
    tm = TokenManager(secret_key="unit_test_secret_key_at_least_32_bytes_long_123456", algorithm="HS256")
    pair = tm.create_token_pair(
        user_id="user-refresh-test",
        email="refresh@illusion.ai",
        name="Refresh User",
    )

    old_refresh = pair.refresh_token

    # Use refresh token to get new tokens
    new_pair = tm.refresh_access_token(old_refresh)
    assert new_pair is not None
    assert new_pair.access_token != pair.access_token
    assert new_pair.refresh_token != old_refresh

    # Old refresh token should now be revoked (rotated)
    second_attempt = tm.refresh_access_token(old_refresh)
    assert second_attempt is None


def test_token_manager_expired_token():
    """Expired token must raise error during verification."""
    tm = TokenManager(secret_key="unit_test_secret_key_at_least_32_bytes_long_123456", algorithm="HS256")
    # Token that expired 1 second ago
    token = tm.create_access_token(
        user_id="user-exp",
        email="exp@illusion.ai",
        expires_delta=timedelta(seconds=-1),
    )

    assert tm.verify_token(token) is None


# ===================================================================
# 3. Auth API Endpoint Tests
# ===================================================================

def test_api_google_auth_url(client):
    """GET /api/auth/google/url should return authorization URL."""
    resp = client.get("/api/auth/google/url?state=test_state_123")
    assert resp.status_code == 200
    data = resp.json()
    assert "authorization_url" in data
    assert "https://accounts.google.com" in data["authorization_url"]
    assert "test_state_123" in data["authorization_url"]


def test_api_auth_protected_route_unauthorized(client):
    """GET /api/auth/me without token should return 401."""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
    assert "Missing Bearer" in resp.json()["detail"]


def test_api_auth_protected_route_authorized(client):
    """GET /api/auth/me with valid Bearer token should return profile."""
    # Generate valid test token
    token = token_manager.create_access_token(
        user_id="test-google-sub-777",
        email="director@msme.tn.gov.in",
        name="Dr. Director",
        picture="https://example.com/dir.png",
        roles=["user", "admin"],
    )

    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    profile = resp.json()
    assert profile["user_id"] == "test-google-sub-777"
    assert profile["email"] == "director@msme.tn.gov.in"
    assert profile["name"] == "Dr. Director"
    assert "admin" in profile["roles"]


def test_api_auth_refresh_endpoint(client):
    """POST /api/auth/refresh should issue new tokens."""
    pair = token_manager.create_token_pair(
        user_id="refresh-api-user",
        email="api@illusion.ai",
    )

    resp = client.post("/api/auth/refresh", json={"refresh_token": pair.refresh_token})
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["access_token"] != pair.access_token


def test_api_auth_logout_revokes_token(client):
    """POST /api/auth/logout should revoke token, making /me unauthorized."""
    token = token_manager.create_access_token(
        user_id="logout-user",
        email="logout@illusion.ai",
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Verify access works first
    resp1 = client.get("/api/auth/me", headers=headers)
    assert resp1.status_code == 200

    # Logout
    resp2 = client.post("/api/auth/logout", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "logged_out"

    # Subsequent access with same token must fail with 401
    resp3 = client.get("/api/auth/me", headers=headers)
    assert resp3.status_code == 401


def test_token_manager_fernet_encryption():
    """Verify Fernet encryption and decryption of secrets."""
    tm = TokenManager()
    plain = "google_refresh_token_secret_12345"
    encrypted = tm.encrypt_secret(plain)
    assert encrypted != plain
    decrypted = tm.decrypt_secret(encrypted)
    assert decrypted == plain


def test_api_root_auth_google_url(client):
    """Verify direct root /auth/google/url works without /api/v1 prefix."""
    resp = client.get("/auth/google/url")
    assert resp.status_code == 200
    assert "88954870386" in resp.json()["authorization_url"]
    assert "http%3A%2F%2Flocalhost%3A8000%2Fauth%2Fgoogle%2Fcallback" in resp.json()["authorization_url"]


# ===================================================================
# 4. Email / Username / Password & Reset Password Tests
# ===================================================================

def test_api_register_user(client):
    """POST /api/auth/register should create user and return tokens."""
    payload = {
        "email": "entrepreneur@tn.gov.in",
        "username": "tn_founder",
        "password": "SecurePassword123!",
        "full_name": "Karthik Raja",
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "user" in data
    assert "tokens" in data
    assert data["user"]["email"] == "entrepreneur@tn.gov.in"
    assert data["user"]["username"] == "tn_founder"
    assert "access_token" in data["tokens"]


def test_api_register_duplicate_email_or_username(client):
    """Duplicate email or username must return 409 conflict."""
    payload = {
        "email": "duplicate@tn.gov.in",
        "username": "dup_user",
        "password": "password123",
    }
    resp1 = client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    # Same email
    resp2 = client.post("/api/auth/register", json={
        "email": "duplicate@tn.gov.in",
        "username": "different_username",
        "password": "password123",
    })
    assert resp2.status_code == 409
    assert "email" in resp2.json()["detail"]

    # Same username
    resp3 = client.post("/api/auth/register", json={
        "email": "different@tn.gov.in",
        "username": "dup_user",
        "password": "password123",
    })
    assert resp3.status_code == 409
    assert "username" in resp3.json()["detail"]


def test_api_login_with_username_and_email(client):
    """User should be able to log in using either Username OR Email."""
    # Register first
    client.post("/api/auth/register", json={
        "email": "dual_login@tn.gov.in",
        "username": "dual_pilot",
        "password": "MySecretPassword99!",
        "full_name": "Pilot User",
    })

    # 1. Login with Username
    resp_user = client.post("/api/auth/login", json={
        "username_or_email": "dual_pilot",
        "password": "MySecretPassword99!",
    })
    assert resp_user.status_code == 200
    assert resp_user.json()["user"]["username"] == "dual_pilot"
    assert "access_token" in resp_user.json()["tokens"]

    # 2. Login with Email
    resp_email = client.post("/api/auth/login", json={
        "username_or_email": "dual_login@tn.gov.in",
        "password": "MySecretPassword99!",
    })
    assert resp_email.status_code == 200
    assert resp_email.json()["user"]["email"] == "dual_login@tn.gov.in"

    # 3. Wrong password
    resp_bad = client.post("/api/auth/login", json={
        "username_or_email": "dual_pilot",
        "password": "WrongPassword!",
    })
    assert resp_bad.status_code == 401


def test_api_forgot_and_reset_password_flow(client):
    """Verify forgot password token generation and password reset."""
    # Register user
    client.post("/api/auth/register", json={
        "email": "reset_test@tn.gov.in",
        "username": "reset_user",
        "password": "OldPassword123!",
    })

    # Request password reset
    forgot_resp = client.post("/api/auth/forgot-password", json={"email": "reset_test@tn.gov.in"})
    assert forgot_resp.status_code == 200
    token = forgot_resp.json()["reset_token"]
    assert token is not None

    # Reset password with token
    reset_resp = client.post("/api/auth/reset-password", json={
        "token": token,
        "new_password": "BrandNewPassword2026!",
    })
    assert reset_resp.status_code == 200

    # Old password must now fail
    old_login = client.post("/api/auth/login", json={
        "username_or_email": "reset_user",
        "password": "OldPassword123!",
    })
    assert old_login.status_code == 401

    # New password must succeed
    new_login = client.post("/api/auth/login", json={
        "username_or_email": "reset_user",
        "password": "BrandNewPassword2026!",
    })
    assert new_login.status_code == 200
    assert new_login.json()["user"]["username"] == "reset_user"
