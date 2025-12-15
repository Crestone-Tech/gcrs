"""Pytest fixtures for database tests."""

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from gcrs.db.models import Base


@pytest.fixture(scope="function")
def test_db_engine():
    """Create an in-memory SQLite database for testing."""
    # Use SQLite in-memory database for fast tests
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
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
    """Create a sample repository directory structure."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    
    # Create a .git directory to make it a git repo
    (repo_path / ".git").mkdir()
    
    # Create some test files
    (repo_path / "test.py").write_text("# test file")
    (repo_path / "README.md").write_text("# Test Repo")
    (repo_path / "src" / "main.py").mkdir(parents=True)
    (repo_path / "src" / "main.py").write_text("print('hello')")
    
    return repo_path

