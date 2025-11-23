from fastapi.testclient import TestClient
from pathlib import Path


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Green Cloud Repository Scanner"}


def test_health_endpoint(client: TestClient):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_scan_summary_endpoint(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_dir": "output", "output_file": "summary.txt", "output_file_format": "markdown"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repo_root" in data
    assert "files_scanned" in data
    assert "files_skipped" in data
