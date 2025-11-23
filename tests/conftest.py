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
    return Path(__file__).parent / "sample_repo"

