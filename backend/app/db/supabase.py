"""Database engine and session management for Supabase PostgreSQL."""

from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger
from app.db.models import Base

engine = None
SessionLocal = None
is_db_connected: bool = False

def init_db():
    global engine, SessionLocal, is_db_connected
    db_url = settings.effective_database_url
    if not db_url:
        logger.warning("No DATABASE_URL configured. Running with in-memory persistence repository.")
        return

    try:
        connect_args = {"timeout": 4}
        if "pg8000" in db_url:
            import ssl
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            connect_args["ssl_context"] = ssl_ctx
        elif "supabase.com" in db_url or "aws" in db_url:
            connect_args["sslmode"] = "require"

        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args=connect_args,
        )
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Create tables if not exist
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        is_db_connected = True
        logger.info("Successfully connected to Supabase PostgreSQL database.")
    except Exception as e:
        logger.warning(f"Could not connect to Supabase PostgreSQL: {e}. Falling back to resilient in-memory repository.")
        is_db_connected = False
        engine = None
        SessionLocal = None


def get_db() -> Generator[Optional[Session], None, None]:
    """Dependency for obtaining database session."""
    if SessionLocal:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    else:
        yield None
