"""Business onboarding profile endpoints."""

from fastapi import APIRouter, HTTPException
from app.schemas.business import BusinessProfileCreate, BusinessProfileResponse
from app.db.repositories import ProfileRepository

router = APIRouter(prefix="/business", tags=["Business Profile"])


@router.post("/profile", response_model=BusinessProfileResponse)
async def create_profile(profile_data: BusinessProfileCreate):
    """Creates or updates a user business onboarding profile."""
    return ProfileRepository.create_or_update(profile_data)


@router.get("/profile/{profile_id}", response_model=BusinessProfileResponse)
async def get_profile(profile_id: str):
    """Retrieves business onboarding profile by id."""
    profile = ProfileRepository.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

