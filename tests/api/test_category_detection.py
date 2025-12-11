from fastapi.testclient import TestClient
from pathlib import Path


def test_scan_summary_code_category_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_category"].get("code") == 26


def test_scan_summary_documentation_category_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_category"].get("documentation") == 4
    # Verify documentation includes markdown files
    assert repository_summary["files_by_extension"].get(".md") == 2
    assert repository_summary["files_by_extension"].get(".txt") == 2


def test_scan_summary_data_category_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_category"].get("data") == 10
    # Verify data category includes various data file types
    assert repository_summary["files_by_extension"].get(".csv") == 1
    assert repository_summary["files_by_extension"].get(".jsonl") == 1
    assert repository_summary["files_by_extension"].get(".ndjson") == 1
    assert repository_summary["files_by_extension"].get(".parquet") == 1
    assert repository_summary["files_by_extension"].get(".sqlite") == 1
    assert repository_summary["files_by_extension"].get(".db") == 1
    assert repository_summary["files_by_extension"].get(".tsv") == 1
    assert repository_summary["files_by_extension"].get(".xml") == 3


def test_scan_summary_config_category_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_category"].get("config") == 10
    # Verify config category includes configuration files
    assert repository_summary["files_by_extension"].get(".json") == 3
    assert repository_summary["files_by_extension"].get(".yaml") == 3
    assert repository_summary["files_by_extension"].get(".yml") == 2
    assert repository_summary["files_by_extension"].get(".toml") == 2


def test_scan_summary_infrastructure_category_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_category"].get("infrastructure") == 1
    # Verify infrastructure category includes Terraform files
    assert repository_summary["files_by_extension"].get(".tf") == 1

