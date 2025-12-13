"""Database connection and session management for GCRS."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from gcrs.db.models import Base
from gcrs.logger import setup_logging

# Load .env file from project root if it exists
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = setup_logging()


def get_database_url() -> str:
    """Get database URL from environment variable or return default.
    
    Returns:
        Database connection URL in format: postgresql://user:password@host:port/dbname
    """
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/gcrs",
    )
    return database_url


# Global engine and session factory
_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Get or create the database engine.
    
    Returns:
        SQLAlchemy engine instance
    """
    global _engine
    if _engine is None:
        database_url = get_database_url()
        logger.info("Connecting to database: %s", database_url.split("@")[-1] if "@" in database_url else database_url)
        _engine = create_engine(
            database_url,
            pool_pre_ping=True,  # Verify connections before using
            echo=False,  # Set to True for SQL query logging
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Get or create the session factory.
    
    Returns:
        SQLAlchemy sessionmaker instance
    """
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions.
    
    Automatically commits on success, rolls back on error, and closes the session.
    
    Yields:
        SQLAlchemy session instance
        
    Example:
        with get_db_session() as session:
            repo = Repo(name="test", ...)
            session.add(repo)
            # Changes are automatically committed when the block exits successfully
    """
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Initialize the database by creating all tables.
    
    This creates all tables defined in the models if they don't exist.
    For production, use Alembic migrations instead.
    """
    engine = get_engine()
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully")


def close_db() -> None:
    """Close database connections and cleanup resources."""
    global _engine, _SessionLocal
    if _engine:
        _engine.dispose()
        _engine = None
    _SessionLocal = None
    logger.info("Database connections closed")

