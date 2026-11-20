"""Application configuration using Pydantic Settings."""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration settings."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = Field(default="ILLUSION AI", description="Application name")
    APP_ENV: str = Field(default="development", description="Environment: development, test, production")
    API_V1_PREFIX: str = Field(default="/api/v1", description="Prefix for API v1 endpoints")
    HOST: str = Field(default="0.0.0.0", description="Backend host")
    PORT: int = Field(default=8000, description="Backend port")

    # CORS
    FRONTEND_URL: str = Field(default="http://localhost:3000", description="Frontend URL for CORS")
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Database & Supabase
    DATABASE_URL: Optional[str] = Field(default=None, description="PostgreSQL / Supabase connection string")
    SUPABASE_URL: Optional[str] = Field(default=None, description="Supabase DB connection or project URL")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(default=None, description="Supabase service role secret")
    SUPABASE_ANON_KEY: Optional[str] = Field(default=None, description="Supabase public anon key")

    # LLM Settings
    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq API key")
    GROQ_MODEL: str = Field(default="qwen/qwen3.8-27b", description="Default Groq LLM model")

    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    GOOGLE_MODEL: str = Field(default="gemini-1.5-flash", description="Default Gemini model")

    # Search & Tool Providers
    TAVILY_API_KEY: Optional[str] = Field(default=None, description="Tavily Web Search API key")
    MAX_UPLOAD_SIZE_BYTES: int = Field(default=15 * 1024 * 1024, description="Max upload size (15MB)")
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]

    # Embeddings
    EMBEDDING_MODEL: str = Field(
        default="models/text-embedding-004",
        description="Configured embedding model identifier (e.g. models/text-embedding-004 for Gemini)",
    )
    EMBEDDING_DIMENSION: int = Field(
        default=768,
        description="Dimension matching configured embedding model (e.g. 768 for Gemini text-embedding-004)",
    )

    # Intelligent Router
    ROUTER_MAX_STEPS: int = Field(default=5, description="Maximum tool execution steps per request")
    ROUTER_TOOL_TIMEOUT: float = Field(default=15.0, description="Timeout in seconds for each tool execution")
    MCP_DISCOVERY_ENABLED: bool = Field(default=False, description="Enable MCP server discovery (Phase 2)")

    # Google OAuth & Authentication
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None, description="Google OAuth 2.0 Client ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None, description="Google OAuth 2.0 Client Secret")
    GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:8000/auth/google/callback",
        description="Google OAuth 2.0 authorized redirect URI",
    )
    SESSION_SECRET: Optional[str] = Field(default=None, description="Session secret key")
    TOKEN_ENCRYPTION_KEY: Optional[str] = Field(default=None, description="Fernet token encryption key")

    # JWT Session Management
    JWT_SECRET_KEY: str = Field(
        default="illusion_ai_super_secret_jwt_key_2026_change_in_production",
        description="Cryptographic secret key for signing JWT tokens",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT cryptographic signature algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration in days")

    @property
    def effective_database_url(self) -> Optional[str]:
        """Returns normalized PostgreSQL connection URL using pure Python pg8000 driver."""
        url = self.DATABASE_URL or self.SUPABASE_URL
        if not url:
            return None
        
        # Remove brackets if password was wrapped in [brackets]
        cleaned = url.replace("[", "").replace("]", "")
        
        # Prefer pure-python pg8000 driver to avoid Windows DLL restrictions
        if cleaned.startswith("postgresql://"):
            return cleaned.replace("postgresql://", "postgresql+pg8000://", 1)
        elif cleaned.startswith("postgres://"):
            return cleaned.replace("postgres://", "postgresql+pg8000://", 1)
        elif cleaned.startswith("postgresql+psycopg://"):
            return cleaned.replace("postgresql+psycopg://", "postgresql+pg8000://", 1)
        return cleaned

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


settings = Settings()

