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

    # Embeddings
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        description="Configured multilingual embedding model identifier",
    )
    EMBEDDING_DIMENSION: int = Field(
        default=384,
        description="Dimension matching configured embedding model (e.g. 384 for MiniLM-L12, 768 for Gemini)",
    )

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

