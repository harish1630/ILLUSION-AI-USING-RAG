"""Comprehensive Production Authentication Test Suite for Illusion AI.
Tests:
- User Registration with Argon2id password hashing
- Login authentication and password verification
- Google OAuth 2.0 URL generation with PKCE and state validation
- Google OAuth callback and account creation/linking
- Short-lived JWT access tokens and long-lived refresh tokens
- Refresh-token rotation and automatic reuse detection (family revocation)
- Logout and session revocation
- Password reset workflow
- Protected /api/v1/auth/me endpoint
- Role-based access control (RBAC)
- TokenVault encryption and provider token management
"""

import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import hash_password, verify_password, generate_pkce_pair
from app.auth.jwt import jwt_manager
from app.auth.service import auth_service
from app.auth.oauth import google_auth, GoogleUserInfo
from app.integrations.token_vault import token_vault

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Argon2id Password Hashing Tests
# ---------------------------------------------------------------------------

def test_argon2id_hashing_and_verification():
    password = "SuperSecretPassword2026!"
    hashed = hash_password(password)

    # Must be valid Argon2id format
    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_pkce_generation():
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) >= 43
    assert len(challenge) >= 40
    assert "=" not in challenge  # base64url without padding


# ---------------------------------------------------------------------------
# 2. Registration API Tests
# ---------------------------------------------------------------------------

def test_user_registration_success():
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    username = f"user_{uuid.uuid4().hex[:8]}"

    payload = {
        "email": unique_email,
        "username": username,
        "password": "Password123!",
        "full_name": "Test User",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["user"]["email"] == unique_email
    assert data["user"]["username"] == username
    assert "tokens" in data
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]
    # Check cookies
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_user_registration_duplicate_fails():
    unique_email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    username = f"dup_{uuid.uuid4().hex[:8]}"

    payload = {
        "email": unique_email,
        "username": username,
        "password": "Password123!",
    }
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    # Attempt same email
    r2 = client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 400
    assert "already registered" in r2.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 3. Login API Tests
# ---------------------------------------------------------------------------

def test_user_login_success():
    unique_email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    username = f"log_{uuid.uuid4().hex[:8]}"
    pwd = "ValidLoginPass123!"

    # Register
    auth_service.register(email=unique_email, username=username, password=pwd, full_name="Login Guy")

    # Login via username
    resp_user = client.post("/api/v1/auth/login", json={"username_or_email": username, "password": pwd})
    assert resp_user.status_code == 200
    assert resp_user.json()["user"]["email"] == unique_email

    # Login via email
    resp_email = client.post("/api/v1/auth/login", json={"username_or_email": unique_email, "password": pwd})
    assert resp_email.status_code == 200
    assert resp_email.json()["tokens"]["access_token"] is not None


def test_user_login_invalid_password_fails():
    unique_email = f"bad_{uuid.uuid4().hex[:8]}@example.com"
    auth_service.register(email=unique_email, username=f"u_{uuid.uuid4().hex[:6]}", password="CorrectPassword123!")

    resp = client.post("/api/v1/auth/login", json={"username_or_email": unique_email, "password": "WrongPassword!"})
    assert resp.status_code == 401
    assert "invalid username or password" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 4. Google OAuth 2.0 Login Tests
# ---------------------------------------------------------------------------

def test_google_auth_url_generation():
    resp = client.get("/api/v1/auth/google/url")
    assert resp.status_code == 200
    data = resp.json()
    assert "auth_url" in data
    assert "accounts.google.com" in data["auth_url"]
    assert "state" in data
    assert "openid" in data["auth_url"]
    # Ensure strict separation: NOT requesting Gmail or drive scopes on user login
    assert "gmail.readonly" not in data["auth_url"]


@pytest.mark.asyncio
async def test_google_oauth_callback_flow():
    # Generate url & valid state
    _, state = google_auth.generate_login_url()

    # Call canonical callback with test code
    resp = client.get(f"/api/v1/auth/google/callback?code=test_code&state={state}", follow_redirects=False)
    assert resp.status_code == 302
    assert "auth_success=true" in resp.headers["location"]
    assert "access_token" in resp.cookies


# ---------------------------------------------------------------------------
# 5. JWT Tokens, Rotation & Reuse Detection Tests
# ---------------------------------------------------------------------------

def test_jwt_access_and_refresh_flow():
    pair = jwt_manager.create_token_pair(
        user_id="user_123",
        email="user123@example.com",
        name="User One",
        roles=["user"],
    )

    # Verify access token
    access_payload = jwt_manager.verify_token(pair.access_token, expected_type="access")
    assert access_payload is not None
    assert access_payload.sub == "user_123"
    assert access_payload.email == "user123@example.com"

    # Verify refresh token
    refresh_payload = jwt_manager.verify_token(pair.refresh_token, expected_type="refresh")
    assert refresh_payload is not None
    assert refresh_payload.sub == "user_123"


def test_refresh_token_rotation_and_reuse_detection():
    # 1. Create initial pair
    initial_pair = jwt_manager.create_token_pair(
        user_id="user_rotation_test",
        email="rotate@example.com",
    )
    old_refresh = initial_pair.refresh_token

    # 2. First rotation (valid)
    resp_rot1 = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp_rot1.status_code == 200
    new_pair_data = resp_rot1.json()
    new_refresh = new_pair_data["refresh_token"]
    assert new_refresh != old_refresh

    # 3. REUSE ATTACK: Attempting to use old_refresh again must be REJECTED!
    resp_reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp_reuse.status_code == 401

    # 4. Token family revoked: Even the new_refresh should now be invalidated because reuse was detected
    resp_family_revoked = client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert resp_family_revoked.status_code == 401


# ---------------------------------------------------------------------------
# 6. Logout & Session Revocation Tests
# ---------------------------------------------------------------------------

def test_user_logout_clears_cookies_and_revokes():
    tokens = jwt_manager.create_token_pair(user_id="logout_user", email="logout@example.com")
    resp = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {tokens.access_token}"},
        cookies={"refresh_token": tokens.refresh_token},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "revoked"

    # Verify token is revoked and cannot be verified
    assert jwt_manager.verify_token(tokens.access_token) is None
    with pytest.raises(ValueError, match="Token has been revoked"):
        jwt_manager.decode_token(tokens.access_token)


# ---------------------------------------------------------------------------
# 7. Password Reset Workflow Tests
# ---------------------------------------------------------------------------

def test_password_reset_workflow():
    email = f"reset_{uuid.uuid4().hex[:6]}@example.com"
    auth_service.register(email=email, username=f"reset_{uuid.uuid4().hex[:6]}", password="InitialPassword123!")

    # Request reset
    req_resp = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert req_resp.status_code == 200
    token = req_resp.json().get("debug_token")
    assert token is not None

    # Reset password
    new_pwd = "BrandNewPassword2026!"
    reset_resp = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": new_pwd})
    assert reset_resp.status_code == 200

    # Login with new password
    login_resp = client.post("/api/v1/auth/login", json={"username_or_email": email, "password": new_pwd})
    assert login_resp.status_code == 200


# ---------------------------------------------------------------------------
# 8. Protected /api/v1/auth/me Endpoint Tests
# ---------------------------------------------------------------------------

def test_auth_me_requires_authentication():
    client.cookies.clear()
    # Without token
    resp_unauth = client.get("/api/v1/auth/me")
    assert resp_unauth.status_code == 401

    # With valid token
    tokens = jwt_manager.create_token_pair(
        user_id="default_user",
        email="founder@illusion.ai",
        name="Entrepreneur Founder",
        roles=["user", "founder"],
    )
    resp_auth = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens.access_token}"})
    assert resp_auth.status_code == 200
    data = resp_auth.json()
    assert data["email"] == "founder@illusion.ai"
    assert "founder" in data["roles"]


# ---------------------------------------------------------------------------
# 9. Token Vault Tests
# ---------------------------------------------------------------------------

def test_token_vault_encryption_and_retrieval():
    user_id = "test_vault_user_456"
    plugin_id = "gmail"
    plain_token = "ya29.sample_google_gmail_oauth_token_12345"

    # Store
    token_vault.store_tokens(
        user_id=user_id,
        plugin_id=plugin_id,
        access_token=plain_token,
        account_email="founder@startup.com",
    )

    # Verify is_connected
    assert token_vault.is_connected(user_id, plugin_id) is True

    # Retrieve and verify decrypted
    stored = token_vault.get_token(user_id, plugin_id)
    assert stored is not None
    assert stored.access_token == plain_token
    assert stored.account_email == "founder@startup.com"

    # Disconnect & verify revoked
    token_vault.revoke_tokens(user_id, plugin_id)
    assert token_vault.is_connected(user_id, plugin_id) is False
    assert token_vault.get_token(user_id, plugin_id) is None
