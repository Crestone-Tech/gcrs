from pathlib import Path
import logging
import pytest
from fastapi.testclient import TestClient

from gcrs.api.main import app

# Configure logging for tests - this ensures pytest captures and displays logs
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] [%(name)s] - %(message)s",
    force=True  # Override any existing configuration
)

@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)

@pytest.fixture(scope="session")
def sample_repo_path() -> Path:
    """Return the path to the sample repository for testing.
    
    The sample_repo must be a git repository (initialized with git init).
    This is a session-scoped fixture that returns the same path for all tests.
    """
    repo_path = Path(__file__).parent / "sample_repo"
    
    # Verify it's a git repository
    git_dir = repo_path / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        raise RuntimeError(
            f"tests/sample_repo is not a git repository. "
            f"Please run 'git init' in {repo_path} and commit the files."
        )
    
    return repo_path

