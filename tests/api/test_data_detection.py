from fastapi.testclient import TestClient
from pathlib import Path


def test_scan_summary_csv_data_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_dir": "output", "output_file": "summary.json", "output_file_format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["data_files_by_extension"].get("csv") == 1
    assert repository_summary["files_by_extension"].get(".csv") == 1
    assert repository_summary["files_by_category"].get("data") == 10


def test_scan_summary_jsonl_data_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_dir": "output", "output_file": "summary.json", "output_file_format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["data_files_by_extension"].get("jsonl") == 1
    assert repository_summary["files_by_extension"].get(".jsonl") == 1


def test_scan_summary_ndjson_data_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_dir": "output", "output_file": "summary.json", "output_file_format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["data_files_by_extension"].get("ndjson") == 1
    assert repository_summary["files_by_extension"].get(".ndjson") == 1


def test_scan_summary_parquet_data_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_dir": "output", "output_file": "summary.json", "output_file_format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["data_files_by_extension"].get("parquet") == 1
    assert repository_summary["files_by_extension"].get(".parquet") == 1


def test_scan_summary_sqlite_data_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_dir": "output", "output_file": "summary.json", "output_file_format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["data_files_by_extension"].get("sqlite") == 1
    assert repository_summary["files_by_extension"].get(".sqlite") == 1


def test_scan_summary_db_data_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_dir": "output", "output_file": "summary.json", "output_file_format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["data_files_by_extension"].get("db") == 1
    assert repository_summary["files_by_extension"].get(".db") == 1


def test_scan_summary_tsv_data_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_dir": "output", "output_file": "summary.json", "output_file_format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["data_files_by_extension"].get("tsv") == 1
    assert repository_summary["files_by_extension"].get(".tsv") == 1


def test_scan_summary_xml_data_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_dir": "output", "output_file": "summary.json", "output_file_format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["data_files_by_extension"].get("xml") == 3
    assert repository_summary["files_by_extension"].get(".xml") == 3


def test_scan_summary_all_data_files_detection(client: TestClient, sample_repo_path: Path):
    """Test that all data file types are correctly detected and categorized."""
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_dir": "output", "output_file": "summary.json", "output_file_format": "json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    
    # Verify total data files count
    total_data_files = sum(repository_summary["data_files_by_extension"].values())
    assert total_data_files == 10
    assert repository_summary["files_by_category"].get("data") == 10
    
    # Verify all expected data file types are present
    expected_data_types = {"csv", "jsonl", "ndjson", "parquet", "sqlite", "db", "tsv", "xml"}
    detected_data_types = set(repository_summary["data_files_by_extension"].keys())
    assert expected_data_types == detected_data_types

