"""SQLAlchemy 2.x Database Models."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SchemeModel(Base):
    __tablename__ = "schemes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    department = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    state = Column(String(100), default="Tamil Nadu", index=True)
    scheme_type = Column(String(100), default="subsidy", index=True)
    official_url = Column(String(500), nullable=False)
    application_url = Column(String(500), nullable=True)
    benefits_summary = Column(Text, nullable=False)
    eligibility_summary = Column(Text, nullable=False)
    exclusions = Column(JSON, default=list)
    required_documents = Column(JSON, default=list)
    application_steps = Column(JSON, default=list)
    last_verified_at = Column(DateTime(timezone=True), default=utc_now)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    rules = relationship("SchemeRuleModel", back_populates="scheme", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunkModel", back_populates="scheme")


class SchemeRuleModel(Base):
    __tablename__ = "scheme_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scheme_id = Column(String(36), ForeignKey("schemes.id"), nullable=False, index=True)
    rule_type = Column(String(100), nullable=False)  # age, budget, category, first_gen, education, state
    field_name = Column(String(100), nullable=False)
    operator = Column(String(50), nullable=False)  # eq, lte, gte, in, contains
    expected_value = Column(JSON, nullable=False)
    source_reference = Column(String(500), nullable=True)
    verified_at = Column(DateTime(timezone=True), default=utc_now)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    scheme = relationship("SchemeModel", back_populates="rules")


class SourceDocumentModel(Base):
    __tablename__ = "source_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scheme_id = Column(String(36), ForeignKey("schemes.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    source_url = Column(String(500), nullable=True)
    source_type = Column(String(50), default="pdf")  # pdf, html, gazette
    language = Column(String(10), default="en")
    content_hash = Column(String(64), nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), default=utc_now)
    last_verified_at = Column(DateTime(timezone=True), default=utc_now)
    ingestion_status = Column(String(50), default="completed")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    chunks = relationship("DocumentChunkModel", back_populates="document", cascade="all, delete-orphan")


class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("source_documents.id"), nullable=False, index=True)
    scheme_id = Column(String(36), ForeignKey("schemes.id"), nullable=True, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    chunk_metadata = Column("metadata", JSON, default=dict)
    embedding = Column(JSON, nullable=True)  # Stored as serialized float array / pgvector compatible
    created_at = Column(DateTime(timezone=True), default=utc_now)

    document = relationship("SourceDocumentModel", back_populates="chunks")
    scheme = relationship("SchemeModel", back_populates="chunks")


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    preferred_language = Column(String(10), default="en")
    state = Column(String(100), default="Tamil Nadu")
    district = Column(String(100), nullable=False)
    business_idea = Column(Text, nullable=False)
    business_category = Column(String(100), nullable=False)
    investment_budget = Column(Float, default=0.0)
    business_stage = Column(String(100), default="idea")
    age_range = Column(String(50), nullable=True)
    first_generation_entrepreneur = Column(Boolean, nullable=True)
    primary_need = Column(String(100), default="general_guidance")
    education_qualification = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class UserRoadmapModel(Base):
    __tablename__ = "user_roadmaps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), default="guest", index=True)
    title = Column(String(255), nullable=False)
    business_summary = Column(Text, nullable=False)
    status = Column(String(50), default="active")  # active, completed
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    tasks = relationship("RoadmapTaskModel", back_populates="roadmap", cascade="all, delete-orphan")


class RoadmapTaskModel(Base):
    __tablename__ = "roadmap_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    roadmap_id = Column(String(36), ForeignKey("user_roadmaps.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(50), default="medium")  # high, medium, low
    status = Column(String(50), default="pending")  # pending, in_progress, completed
    due_date = Column(DateTime(timezone=True), nullable=True)
    prerequisites = Column(JSON, default=list)
    required_documents = Column(JSON, default=list)
    official_url = Column(String(500), nullable=True)
    source_references = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    roadmap = relationship("UserRoadmapModel", back_populates="tasks")

