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


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for pure OAuth accounts
    full_name = Column(String(255), nullable=True)
    picture = Column(String(500), nullable=True)
    google_id = Column(String(100), unique=True, nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    reset_token = Column(String(255), nullable=True, index=True)
    reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    roles = relationship("UserRoleModel", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSessionModel", back_populates="user", cascade="all, delete-orphan")


class UserRoleModel(Base):
    __tablename__ = "user_roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="user")  # 'user', 'admin', 'developer'
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("UserModel", back_populates="roles")


class UserSessionModel(Base):
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    is_active = Column(Boolean, default=True)
    last_active_at = Column(DateTime(timezone=True), default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("UserModel", back_populates="sessions")
    refresh_tokens = relationship("RefreshTokenModel", back_populates="session", cascade="all, delete-orphan")


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("user_sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256 of token
    jti = Column(String(100), nullable=False, unique=True, index=True)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    session = relationship("UserSessionModel", back_populates="refresh_tokens")


class OAuthAccountModel(Base):
    __tablename__ = "oauth_accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # 'google'
    provider_user_id = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    encrypted_access_token = Column(Text, nullable=True)
    encrypted_refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class ConnectedIntegrationModel(Base):
    __tablename__ = "connected_integrations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plugin_id = Column(String(100), nullable=False, index=True)
    account_id = Column(String(255), nullable=True)
    account_email = Column(String(255), nullable=True)
    account_username = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    status = Column(String(50), default="connected")  # 'connected', 'expired', 'revoked'
    scopes = Column(JSON, default=list)
    connected_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class IntegrationTokenModel(Base):
    __tablename__ = "integration_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    integration_id = Column(String(36), ForeignKey("connected_integrations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plugin_id = Column(String(100), nullable=False, index=True)
    encrypted_access_token = Column(Text, nullable=False)
    encrypted_refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class PluginPermissionModel(Base):
    __tablename__ = "plugin_permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plugin_id = Column(String(100), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    permission_level = Column(String(50), default="DENY")  # 'ALLOW', 'APPROVAL_REQUIRED', 'DENY'
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)  # 'auth', 'plugin', 'mcp', 'router'
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(45), nullable=True)
    status = Column(String(50), default="SUCCESS")  # 'SUCCESS', 'FAILED', 'DENIED', 'APPROVAL_REQUIRED'
    created_at = Column(DateTime(timezone=True), default=utc_now)


class OAuthStateModel(Base):
    __tablename__ = "oauth_states"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    state = Column(String(255), unique=True, nullable=False, index=True)
    flow_type = Column(String(50), nullable=False, default="login")  # 'login' or 'plugin'
    plugin_id = Column(String(100), nullable=True)
    user_id = Column(String(36), nullable=True)
    redirect_uri = Column(String(500), nullable=False)
    code_verifier = Column(String(255), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)


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


class GitHubConnectionModel(Base):
    """GitHub OAuth connections and encrypted access tokens."""
    __tablename__ = "github_connections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    github_user_id = Column(String(100), nullable=False, index=True)
    github_username = Column(String(100), nullable=False)
    github_email = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    encrypted_access_token = Column(Text, nullable=False)
    connected_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class MCPServerModel(Base):
    """Configured MCP servers and connection parameters."""
    __tablename__ = "mcp_servers"

    id = Column(String(100), primary_key=True)
    user_id = Column(String(36), default="system", index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    transport = Column(String(50), nullable=False)
    command = Column(String(255), nullable=True)
    args = Column(JSON, default=list)
    url = Column(String(500), nullable=True)
    status = Column(String(50), default="disconnected")
    config = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class MCPToolModel(Base):
    """Dynamically discovered MCP tools and schemas."""
    __tablename__ = "mcp_tools"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(100), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    qualified_name = Column(String(200), nullable=False, index=True)
    description = Column(Text, default="")
    input_schema = Column(JSON, default=dict)
    is_enabled = Column(Boolean, default=True)
    discovered_at = Column(DateTime(timezone=True), default=utc_now)


class MCPPermissionModel(Base):
    """User and tool-level permissions (ALLOW, APPROVAL_REQUIRED, DENY)."""
    __tablename__ = "mcp_permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    server_id = Column(String(100), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    permission_level = Column(String(50), default="DENY")
    created_at = Column(DateTime(timezone=True), default=utc_now)


class MCPApprovalModel(Base):
    """Human-in-the-loop approval requests."""
    __tablename__ = "mcp_approvals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    server_id = Column(String(100), nullable=False)
    tool_name = Column(String(100), nullable=False)
    arguments = Column(JSON, default=dict)
    status = Column(String(50), default="PENDING")
    reviewer_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)


class MCPExecutionLogModel(Base):
    """Audit log of MCP tool executions."""
    __tablename__ = "mcp_execution_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    server_id = Column(String(100), nullable=False)
    tool_name = Column(String(100), nullable=False)
    arguments = Column(JSON, default=dict)
    status = Column(String(50), nullable=False)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Float, default=0.0)
    executed_at = Column(DateTime(timezone=True), default=utc_now)

