"""Government schemes endpoints."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from app.schemas.scheme import SchemeResponse, SchemeListResponse, SchemeMatchRequest
from app.db.repositories import SchemeRepository
from app.core.constants import DISCLAIMER_EN

router = APIRouter(prefix="/schemes", tags=["Schemes"])


@router.get("", response_model=SchemeListResponse)
async def list_schemes(
    state: Optional[str] = Query(None, description="Filter by state (e.g. Tamil Nadu or Central)"),
    scheme_type: Optional[str] = Query(None, description="Filter by type (subsidy, grant, loan, support)"),
    search: Optional[str] = Query(None, description="Search query across name and description"),
):
    """Lists government schemes with optional state, type, and search filters."""
    items = SchemeRepository.list_schemes(state=state, scheme_type=scheme_type, search=search)
    return SchemeListResponse(
        total=len(items),
        items=[SchemeResponse(**s) for s in items],
        disclaimer=DISCLAIMER_EN,
    )


@router.get("/{scheme_id}", response_model=SchemeResponse)
async def get_scheme(scheme_id: str):
    """Retrieves detailed scheme data and official links."""
    scheme = SchemeRepository.get_by_id(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return SchemeResponse(**scheme)


@router.post("/match", response_model=List[SchemeResponse])
async def match_schemes(req: SchemeMatchRequest):
    """
    Deterministic rule-based screening engine.
    Matches user profile against authentic eligibility rules.
    """
    matched = SchemeRepository.match_schemes(req)
    return [SchemeResponse(**s) for s in matched]

