"""Database connection and session management for GCRS."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
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
    """Initialize the database by creating all tables and views.
    
    This creates all tables defined in the models if they don't exist,
    then creates database views.
    For production, use Alembic migrations instead.
    """
    engine = get_engine()
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    create_views()  # Create views after tables
    logger.info("Database schema initialized successfully")

def create_views() -> None:
    """Create database views.
    
    Views are not part of SQLAlchemy models, so we execute raw SQL.
    Uses CREATE OR REPLACE VIEW so it's safe to run multiple times.
    """
    engine = get_engine()
    logger.info("Creating database views...")
    
    # Define the repo_summary view SQL
    # This aggregates repository statistics from BOM data
    repo_summary_view_sql = """
    CREATE OR REPLACE VIEW repo_summary AS
    SELECT 
        r.id AS repo_id,
        r.git_owner_account,
        r.name AS repo_name,
        r.uri AS repo_uri,
        b.id AS latest_bom_id,
        b.start_timestamp AS latest_scan_timestamp,
        b.status AS latest_scan_status,
        COUNT(DISTINCT b.id) AS total_scans,
        COUNT(DISTINCT bf.id) AS total_files_scanned,
        COUNT(DISTINCT CASE WHEN bf.category IS NOT NULL THEN bf.id END) AS files_with_category,
        COUNT(DISTINCT CASE WHEN bf.language IS NOT NULL THEN bf.id END) AS files_with_language,
        -- Aggregated counts by category
        COUNT(DISTINCT CASE WHEN bf.category = 'code' THEN bf.id END) AS code_files,
        COUNT(DISTINCT CASE WHEN bf.category = 'config' THEN bf.id END) AS config_files,
        COUNT(DISTINCT CASE WHEN bf.category = 'docs' THEN bf.id END) AS docs_files,
        -- Aggregated counts by language
        COUNT(DISTINCT CASE WHEN bf.language = 'python' THEN bf.id END) AS python_files,
        COUNT(DISTINCT CASE WHEN bf.language = 'javascript' THEN bf.id END) AS javascript_files,
        -- Add more aggregations as needed
        MAX(b.end_timestamp) AS last_scan_completed_at
    FROM repo r
    LEFT JOIN bom b ON r.id = b.repo_id
    LEFT JOIN bom_file bf ON b.id = bf.bom_id
    GROUP BY r.id, r.git_owner_account, r.name, r.uri, b.id, b.start_timestamp, b.status
    HAVING b.id = (
        SELECT id FROM bom 
        WHERE repo_id = r.id 
        ORDER BY start_timestamp DESC 
        LIMIT 1
    );
    """
    
    # Execute the SQL using the engine's connection
    # Using text() to properly handle the SQL string
    with engine.connect() as connection:
        # Execute the view creation
        connection.execute(text(repo_summary_view_sql))
        # Commit the transaction (DDL statements need to be committed)
        connection.commit()
    
    logger.info("Database views created successfully")

def close_db() -> None:
    """Close database connections and cleanup resources."""
    global _engine, _SessionLocal
    if _engine:
        _engine.dispose()
        _engine = None
    _SessionLocal = None
    logger.info("Database connections closed")

