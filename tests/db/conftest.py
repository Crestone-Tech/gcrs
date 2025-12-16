"""Pytest fixtures for database tests."""

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from gcrs.db.models import Base
from gcrs.db.database import create_views


@pytest.fixture(scope="session")
def postgres_container():
    """Create a PostgreSQL container for testing (session-scoped for performance).
    
    Requires Docker to be running. If Docker is not available, tests will be skipped
    with a clear error message.
    """
    try:
        with PostgresContainer("postgres:15-alpine") as postgres:
            yield postgres
    except Exception as e:
        error_msg = str(e)
        if "CreateFile" in error_msg or "docker" in error_msg.lower():
            pytest.skip(
                "Docker is required for database tests but is not available. "
                "Please ensure Docker Desktop is installed and running."
            )
        raise  # Re-raise if it's a different error


@pytest.fixture(scope="function")
def test_db_engine(postgres_container):
    """Create a PostgreSQL database engine for testing.
    
    Uses testcontainers to spin up a real PostgreSQL instance,
    matching production exactly.
    """
    # Get connection URL from container
    database_url = postgres_container.get_connection_url()
    
    # Create engine
    engine = create_engine(database_url, echo=False)
    
    # Create all tables and views
    Base.metadata.create_all(bind=engine)
    create_views(engine)
    
    yield engine
    
    # Clean up: drop views first, then tables
    # Views depend on tables, so we must drop them in order
    with engine.connect() as connection:
        from sqlalchemy import text
        connection.execute(text("DROP VIEW IF EXISTS repo_summary CASCADE"))
        connection.commit()
    
    # Now we can drop all tables
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a database session for testing."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = SessionLocal()
    try:
        yield session
        session.rollback()  # Rollback any uncommitted changes
    finally:
        session.close()


@pytest.fixture
def sample_repo_path(tmp_path: Path) -> Path:
    """Create a sample git repository directory structure."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    
    # Initialize as a git repo and commit files
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    (repo_path / "test.py").write_text("# test file")
    (repo_path / "README.md").write_text("# Test Repo")
    (repo_path / "src").mkdir()
    (repo_path / "src" / "main.py").write_text("print('hello')")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit for test repo"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    
    return repo_path

