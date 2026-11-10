"""Pydantic schemas for Business Profile and Onboarding Questionnaire."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class BusinessProfileCreate(BaseModel):
    user_id: Optional[str] = "guest"
    preferred_language: str = Field(default="en", description="Preferred language: en or ta")
    state: str = Field(default="Tamil Nadu", description="State")
    district: str = Field(..., description="District in Tamil Nadu")
    business_idea: str = Field(..., min_length=3, description="Description of business idea or activity")
    business_category: str = Field(
        ...,
        description="Category: manufacturing, services, trading, agriculture_allied, other",
    )
    investment_budget: float = Field(..., ge=0, description="Estimated startup investment budget in INR")
    business_stage: str = Field(
        default="idea",
        description="Stage: idea, planning, registration, operating",
    )
    age_range: Optional[str] = Field(default=None, description="Age bracket: 18-35, 36-45, 46+")
    first_generation_entrepreneur: Optional[bool] = Field(
        default=None,
        description="Is the founder a first-generation entrepreneur?",
    )
    primary_need: Optional[str] = Field(
        default="general_guidance",
        description="loans, subsidies, registration, general_guidance",
    )
    education_qualification: Optional[str] = None


class BusinessProfileResponse(BusinessProfileCreate):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

