"""Tests for basic API endpoints.

This module contains tests for the core API endpoints including:
- Root endpoint (API identification)
- Health check endpoint
- Scan summary endpoint (only the most basic test to verify the endppoint is alive. Functional tests are in separate modules.)
"""
from pathlib import Path
from fastapi.testclient import TestClient

def test_root_endpoint(client: TestClient):
    """Test the root endpoint returns the correct API identification message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Green Cloud Repository Scanner"}


def test_health_endpoint(client: TestClient):
    """Test the health check endpoint returns a healthy status."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_scan_summary_endpoint(client: TestClient, sample_repo_path: Path):
    """Test the scan summary endpoint returns a successful response with required fields."""
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path)})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repo_root" in data
    assert "files_scanned" in data
    assert "files_skipped" in data
