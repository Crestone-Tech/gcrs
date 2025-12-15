from fastapi.testclient import TestClient
from pathlib import Path

import logging

logger = logging.getLogger(__name__)


def test_scan_summary_c_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "markdown", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("c") == 1
    assert repository_summary["files_by_extension"].get(".c") == 1
    assert repository_summary["files_by_extension"].get(".h") == 1

#@TODO: is c-header a language, or fold into c?
#@TODO: is cpp-header a language, or fold into cpp?


def test_scan_summary_cpp_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "markdown", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("cpp") == 1
    assert repository_summary["files_by_extension"].get(".cpp") == 1
    assert repository_summary["files_by_extension"].get(".hpp") == 1


def test_scan_summary_csharp_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("csharp") == 1
    assert repository_summary["files_by_extension"].get(".cs") == 1


def test_scan_summary_css_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("css") == 1
    assert repository_summary["files_by_extension"].get(".css") == 1


def test_scan_summary_go_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("go") == 1
    assert repository_summary["files_by_extension"].get(".go") == 1


def test_scan_summary_html_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("html") == 1
    assert repository_summary["files_by_extension"].get(".html") == 1


def test_scan_summary_java_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("java") == 1
    assert repository_summary["files_by_extension"].get(".java") == 1


def test_scan_summary_javascript_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "markdown", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    #
    #assert "files_scanned" in data
    #assert "files_skipped" in data
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    
    logger.info("files_by_language: %s", repository_summary["files_by_language"])
    logger.info("javascript detection: %s", repository_summary["files_by_language"].get("javascript"))
    assert repository_summary["files_by_language"].get("javascript") == 2
    assert repository_summary["files_by_extension"].get(".js") == 1
    assert repository_summary["files_by_extension"].get(".jsx") == 1


def test_scan_summary_kotlin_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("kotlin") == 1
    assert repository_summary["files_by_extension"].get(".kt") == 1


def test_scan_summary_markdown_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("markdown") == 2
    assert repository_summary["files_by_extension"].get(".md") == 2


def test_scan_summary_objective_c_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("objective-c") == 1
    assert repository_summary["files_by_extension"].get(".m") == 1


def test_scan_summary_objective_c_plus_plus_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("objective-c++") == 1
    assert repository_summary["files_by_extension"].get(".mm") == 1


def test_scan_summary_php_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("php") == 1
    assert repository_summary["files_by_extension"].get(".php") == 1


def test_scan_summary_python_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "markdown", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("python") == 1
    assert repository_summary["files_by_extension"].get(".py") == 1


def test_scan_summary_ruby_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("ruby") == 1
    assert repository_summary["files_by_extension"].get(".rb") == 1


def test_scan_summary_rust_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("rust") == 1
    assert repository_summary["files_by_extension"].get(".rs") == 1


def test_scan_summary_sass_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("sass") == 1
    assert repository_summary["files_by_extension"].get(".sass") == 1


def test_scan_summary_scala_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("scala") == 1
    assert repository_summary["files_by_extension"].get(".scala") == 1


def test_scan_summary_scss_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("scss") == 1
    assert repository_summary["files_by_extension"].get(".scss") == 1


def test_scan_summary_sql_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("sql") == 1
    assert repository_summary["files_by_extension"].get(".sql") == 1


def test_scan_summary_swift_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("swift") == 1
    assert repository_summary["files_by_extension"].get(".swift") == 1


def test_scan_summary_typescript_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "markdown", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("typescript") == 2
    assert repository_summary["files_by_extension"].get(".ts") == 1
    assert repository_summary["files_by_extension"].get(".tsx") == 1


def test_scan_summary_vb_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    assert repository_summary["files_by_language"].get("vb") == 1
    assert repository_summary["files_by_extension"].get(".vb") == 1

