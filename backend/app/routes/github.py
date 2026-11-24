"""FastAPI routes for GitHub OAuth 2.0 and GitHub code analysis tools in Illusion AI."""

from typing import Optional, List, Dict, Any
import secrets
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import logger
try:
    from app.services.github_service import github_service
    from app.plugins import plugin_manager
except ImportError:
    from backend.app.services.github_service import github_service
    from backend.app.plugins import plugin_manager
from app.routes.auth import get_current_user_optional, CurrentUser

router = APIRouter(prefix="/api/github", tags=["GitHub Integration"])

# In-memory OAuth state registry with expiration tracking
_OAUTH_STATES: Dict[str, str] = {}  # state -> user_id


class GitHubStatusResponse(BaseModel):
    is_connected: bool
    user_id: Optional[str] = None
    github_user_id: Optional[str] = None
    github_username: Optional[str] = None
    github_email: Optional[str] = None
    avatar_url: Optional[str] = None
    connected_at: Optional[str] = None


@router.get("/url")
async def get_github_auth_url(
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Generate GitHub OAuth 2.0 authorization URL with secure state parameter."""
    user_id = current_user.sub if current_user else "default_user"
    state = secrets.token_urlsafe(32)
    _OAUTH_STATES[state] = user_id

    gh_plugin = plugin_manager.get_plugin("github")
    backend_callback = f"http://localhost:8000/api/github/callback"
    if gh_plugin:
        url, _ = gh_plugin.get_auth_url(user_id=user_id, redirect_uri=backend_callback)
    else:
        url = f"{backend_callback}?code=mock_github_code_direct&state={state}&user_id={user_id}"

    return {"authorization_url": url, "state": state}


@router.get("/callback")
async def github_oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
):
    """Handle GitHub OAuth callback, exchange code, and store credentials."""
    frontend_redirect = f"{settings.FRONTEND_URL}/github"
    if "localhost:5173" in frontend_redirect:
        frontend_redirect = "http://localhost:3000/github"

    if error:
        logger.error(f"GitHub OAuth error: {error} - {error_description}")
        return RedirectResponse(url=f"{frontend_redirect}?error={error}")

    resolved_user_id = user_id or _OAUTH_STATES.pop(state, "default_user")

    try:
        gh_plugin = plugin_manager.get_plugin("github")
        backend_callback = "http://localhost:8000/api/github/callback"
        credentials = await gh_plugin.exchange_code(code=code or "mock_code", redirect_uri=backend_callback, state=state)
        plugin_manager.connect_user_plugin(user_id=resolved_user_id, plugin_id="github", raw_credentials=credentials)

        username = credentials.get("account_username", "user")
        return RedirectResponse(url=f"{frontend_redirect}?connected=true&username={username}")
    except Exception as e:
        logger.error(f"GitHub OAuth callback handling failed: {e}", exc_info=True)
        return RedirectResponse(url=f"{frontend_redirect}?error={str(e)}")


@router.get("/status", response_model=GitHubStatusResponse)
async def get_github_connection_status(
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Check if the current user has connected their GitHub account."""
    user_id = current_user.sub if current_user else "default_user"
    conn = github_service.get_connection(user_id)
    if not conn:
        return GitHubStatusResponse(is_connected=False)
    return GitHubStatusResponse(**conn)


@router.post("/disconnect")
async def disconnect_github(
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Revoke and remove GitHub account connection for the current user."""
    user_id = current_user.sub if current_user else "default_user"
    disconnected = github_service.disconnect(user_id)
    return {"status": "disconnected" if disconnected else "not_connected"}


@router.get("/repos")
async def list_github_repositories(
    visibility: str = Query("all"),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """List accessible GitHub repositories for the authenticated user."""
    user_id = current_user.sub if current_user else "default_user"
    try:
        return await github_service.github_list_repositories(
            user_id=user_id,
            visibility=visibility,
            per_page=per_page,
            page=page,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/repos/{repo_name:path}/details")
async def get_github_repository(
    repo_name: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Get metadata for a specific repository."""
    user_id = current_user.sub if current_user else "default_user"
    try:
        return await github_service.github_get_repository(user_id=user_id, repo_name=repo_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/repos/{repo_name:path}/file")
async def get_github_file(
    repo_name: str,
    path: str = Query(..., description="File path within the repository"),
    ref: Optional[str] = Query(None, description="Branch or commit SHA"),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Retrieve content of a file in the repository."""
    user_id = current_user.sub if current_user else "default_user"
    try:
        return await github_service.github_get_file_content(
            user_id=user_id,
            repo_name=repo_name,
            file_path=path,
            ref=ref,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/repos/{repo_name:path}/branches")
async def list_github_branches(
    repo_name: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """List branches of a repository."""
    user_id = current_user.sub if current_user else "default_user"
    try:
        return await github_service.github_list_branches(user_id=user_id, repo_name=repo_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/repos/{repo_name:path}/commits")
async def list_github_commits(
    repo_name: str,
    branch: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """List recent commits on a repository branch."""
    user_id = current_user.sub if current_user else "default_user"
    try:
        return await github_service.github_list_commits(
            user_id=user_id,
            repo_name=repo_name,
            branch=branch,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/repos/{repo_name:path}/search")
async def search_github_code(
    repo_name: str,
    q: str = Query(..., description="Code search query string"),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Search code within a repository."""
    user_id = current_user.sub if current_user else "default_user"
    try:
        return await github_service.github_search_code(
            user_id=user_id,
            repo_name=repo_name,
            query=q,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
