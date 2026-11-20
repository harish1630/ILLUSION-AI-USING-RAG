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


class ChatExecutedTool(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class ChatMessageRequest(BaseModel):
    question: str = Field(..., min_length=2, description="User question in Tamil, English, or mixed")
    language: Optional[str] = Field(default="en", description="Preferred response language: en or ta")
    conversation_id: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None  # Profile context (district, budget, category, etc.)
    # Hybrid Tool Calling fields
    tool_mode: Optional[str] = Field(default="auto", description="Tool selection mode: 'auto', 'manual', 'hybrid'")
    selected_tools: Optional[List[str]] = Field(default=None, description="Tools to use in manual or hybrid mode")
    tool_args: Optional[Dict[str, Dict[str, Any]]] = Field(default=None, description="Explicit arguments for tools")


class ChatMessageResponse(BaseModel):
    answer: str
    language: str
    sources: List[ChatSourceCitation] = Field(default_factory=list)
    eligibility_status: Optional[str] = "insufficient_information"
    follow_up_questions: List[str] = Field(default_factory=list)
    matched_schemes: List[Dict[str, Any]] = Field(default_factory=list)
    disclaimer: str
    conversation_id: Optional[str] = None
    executed_tools: List[ChatExecutedTool] = Field(default_factory=list)
    tool_mode_used: Optional[str] = None

