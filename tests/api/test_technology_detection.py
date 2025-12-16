from fastapi.testclient import TestClient
from pathlib import Path


def test_scan_summary_docker_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_technology"].get("Docker") == 1


def test_scan_summary_go_technology_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_technology"].get("Go") == 2
    # Verify Go technology is detected from go.mod and go.sum files
    assert repository_summary["files_by_dependency"].get("go-mod") == 1
    assert repository_summary["files_by_dependency"].get("go-sum") == 1


def test_scan_summary_nodejs_technology_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_technology"].get("Node.js") == 5
    # Verify Node.js technology is detected from various package manager files
    assert repository_summary["files_by_dependency"].get("node-package") == 2
    assert repository_summary["files_by_dependency"].get("node-lock") == 1
    assert repository_summary["files_by_dependency"].get("node-pnpm-lock") == 1
    assert repository_summary["files_by_dependency"].get("node-yarn-lock") == 1


def test_scan_summary_python_technology_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_technology"].get("Python") == 4
    # Verify Python technology is detected from various dependency files
    assert repository_summary["files_by_dependency"].get("python-requirements") == 2
    assert repository_summary["files_by_dependency"].get("python-pipenv") == 1
    assert repository_summary["files_by_dependency"].get("python-pipenv-lock") == 1
    assert repository_summary["files_by_dependency"].get("python-poetry-lock") == 1
    assert repository_summary["files_by_dependency"].get("python-pyproject") == 1


def test_scan_summary_maven_technology_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_technology"].get("Maven") == 2
    # Verify Maven technology is detected from pom.xml files
    assert repository_summary["files_by_dependency"].get("maven-pom") == 2


def test_scan_summary_gradle_technology_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_technology"].get("Gradle") == 1
    # Verify Gradle technology is detected from build.gradle files
    assert repository_summary["files_by_extension"].get(".gradle") == 1

