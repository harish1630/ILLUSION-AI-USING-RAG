"""Pydantic schemas for Government Schemes and Eligibility Rules."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SchemeRuleSchema(BaseModel):
    id: str
    scheme_id: str
    rule_type: str  # e.g., 'age', 'budget', 'category', 'first_gen', 'education'
    field_name: str
    operator: str  # 'eq', 'lte', 'gte', 'in', 'contains'
    expected_value: Any
    source_reference: Optional[str] = None
    verified_at: Optional[datetime] = None


class SchemeBase(BaseModel):
    name: str
    department: str
    description: str
    state: str = "Tamil Nadu"  # or "Central"
    scheme_type: str = "subsidy"  # subsidy, loan, grant, support
    official_url: str
    application_url: Optional[str] = None
    benefits_summary: str
    eligibility_summary: str
    exclusions: Optional[List[str]] = Field(default_factory=list)
    required_documents: Optional[List[str]] = Field(default_factory=list)
    application_steps: Optional[List[str]] = Field(default_factory=list)
    last_verified_at: Optional[datetime] = None


class SchemeResponse(SchemeBase):
    id: str
    rules: List[SchemeRuleSchema] = Field(default_factory=list)
    eligibility_status: Optional[str] = "verification_required"
    match_reasons: List[str] = Field(default_factory=list)
    missing_criteria: List[str] = Field(default_factory=list)


class SchemeListResponse(BaseModel):
    total: int
    items: List[SchemeResponse]
    disclaimer: str


class SchemeMatchRequest(BaseModel):
    preferred_language: str = "en"
    state: str = "Tamil Nadu"
    district: Optional[str] = None
    business_activity: str
    business_category: str  # manufacturing, services, trading, agriculture_allied, other
    investment_budget: float = Field(default=0.0, ge=0)
    business_stage: str = "idea"  # idea, planning, registration, operating
    age: Optional[int] = None
    first_generation_entrepreneur: Optional[bool] = None
    gender: Optional[str] = None
    community: Optional[str] = None
    education_qualification: Optional[str] = None
    needs_financial_assistance: bool = True

