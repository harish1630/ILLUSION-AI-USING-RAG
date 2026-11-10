"""Pydantic schemas for Bilingual AI Chat Assistant and RAG."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatSourceCitation(BaseModel):
    title: str
    url: str
    document_id: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    last_verified_at: Optional[str] = None


class ChatMessageRequest(BaseModel):
    question: str = Field(..., min_length=2, description="User question in Tamil, English, or mixed")
    language: Optional[str] = Field(default="en", description="Preferred response language: en or ta")
    conversation_id: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None  # Profile context (district, budget, category, etc.)


class ChatMessageResponse(BaseModel):
    answer: str
    language: str
    sources: List[ChatSourceCitation] = Field(default_factory=list)
    eligibility_status: Optional[str] = "insufficient_information"
    follow_up_questions: List[str] = Field(default_factory=list)
    matched_schemes: List[Dict[str, Any]] = Field(default_factory=list)
    disclaimer: str
    conversation_id: Optional[str] = None

