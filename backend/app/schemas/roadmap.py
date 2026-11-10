"""Pydantic schemas for Personalized Launch Roadmap and Tasks."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RoadmapTaskBase(BaseModel):
    title: str
    description: str
    priority: str = Field(default="medium", description="high, medium, low")
    status: str = Field(default="pending", description="pending, in_progress, completed")
    prerequisites: Optional[List[str]] = Field(default_factory=list)
    required_documents: Optional[List[str]] = Field(default_factory=list)
    official_url: Optional[str] = None
    source_references: Optional[List[str]] = Field(default_factory=list)


class RoadmapTaskUpdate(BaseModel):
    status: str = Field(..., description="pending, in_progress, completed")


class RoadmapTaskResponse(RoadmapTaskBase):
    id: str
    roadmap_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class RoadmapCreate(BaseModel):
    user_id: Optional[str] = "guest"
    title: str
    business_summary: str
    category: str
    district: str
    budget: float
    stage: str


class RoadmapResponse(BaseModel):
    id: str
    user_id: str
    title: str
    business_summary: str
    status: str  # active, completed, archived
    progress_percentage: float = 0.0
    tasks: List[RoadmapTaskResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None

