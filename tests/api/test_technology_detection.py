from fastapi.testclient import TestClient
from pathlib import Path


def test_scan_summary_docker_detection(client: TestClient, sample_repo_path: Path):
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    # Docker should be detected from Dockerfile and docker-compose files
    assert repository_summary["files_by_technology"].get("Docker") >= 1


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


def test_scan_summary_terraform_technology_detection(client: TestClient, sample_repo_path: Path):
    """Test that Terraform technology is detected from .tf files."""
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    # Terraform should be detected from .tf extension files (main.tf, variables.tf, outputs.tf)
    assert repository_summary["files_by_technology"].get("Terraform") >= 3


def test_scan_summary_kubernetes_technology_detection(client: TestClient, sample_repo_path: Path):
    """Test that Kubernetes technology is detected from files with 'k8s' in the name."""
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    # Kubernetes should be detected from files with 'k8s' in the name
    assert repository_summary["files_by_technology"].get("Kubernetes") >= 2


def test_scan_summary_ansible_technology_detection(client: TestClient, sample_repo_path: Path):
    """Test that Ansible technology is detected from ansible.cfg and files with 'ansible' in the name."""
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    # Ansible should be detected from ansible.cfg and files with 'ansible' in the name
    assert repository_summary["files_by_technology"].get("Ansible") >= 2


def test_scan_summary_ruby_technology_detection(client: TestClient, sample_repo_path: Path):
    """Test that Ruby technology is detected from Gemfile and Gemfile.lock files."""
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    # Ruby should be detected from Gemfile and Gemfile.lock files
    assert repository_summary["files_by_technology"].get("Ruby") >= 2
    assert repository_summary["files_by_dependency"].get("ruby-gemfile") >= 1
    assert repository_summary["files_by_dependency"].get("ruby-gem-lock") >= 1


def test_scan_summary_rust_technology_detection(client: TestClient, sample_repo_path: Path):
    """Test that Rust technology is detected from Cargo.toml and Cargo.lock files."""
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    # Rust should be detected from Cargo.toml and Cargo.lock files
    assert repository_summary["files_by_technology"].get("Rust") >= 2
    assert repository_summary["files_by_dependency"].get("rust-cargo") >= 1
    assert repository_summary["files_by_dependency"].get("rust-cargo-lock") >= 1


def test_scan_summary_python_config_files_detection(client: TestClient, sample_repo_path: Path):
    """Test that Python technology is detected from Python config files (setup.cfg, tox.ini, pytest.ini)."""
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    # Python should be detected from setup.cfg, tox.ini, pytest.ini, and dependency files
    # The count should include config files plus dependency files
    assert repository_summary["files_by_technology"].get("Python") >= 7


def test_scan_summary_docker_compose_variants_detection(client: TestClient, sample_repo_path: Path):
    """Test that Docker technology is detected from all docker-compose variants."""
    response = client.post("/scan/summary", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    repository_summary = data["repository_summary"]
    # Docker should be detected from Dockerfile and all docker-compose variants
    # docker-compose.yml, docker-compose.yaml, docker-compose.override.yml, docker-compose.override.yaml
    assert repository_summary["files_by_technology"].get("Docker") >= 5


def test_scan_file_records_technologies_field(client: TestClient, sample_repo_path: Path):
    """Test that FileRecord objects have technologies field populated correctly."""
    response = client.post("/scan", json={"repo_root": str(sample_repo_path), "output_file_format": "json", "persist_to_db": False, "write_output_file": False, "skip_git_commit_info": True})
    assert response.status_code == 200
    data = response.json()
    
    # Find a Dockerfile record
    dockerfile_record = next((r for r in data if r.get("name") == "Dockerfile"), None)
    assert dockerfile_record is not None
    assert "technologies" in dockerfile_record
    assert "Docker" in dockerfile_record["technologies"]
    
    # Find a Terraform file record
    terraform_record = next((r for r in data if r.get("name") == "main.tf"), None)
    assert terraform_record is not None
    assert "technologies" in terraform_record
    assert "Terraform" in terraform_record["technologies"]
    
    # Find a Kubernetes file record
    k8s_record = next((r for r in data if "k8s" in r.get("name", "").lower()), None)
    assert k8s_record is not None
    assert "technologies" in k8s_record
    assert "Kubernetes" in k8s_record["technologies"]
    
    # Find a Python dependency file record
    python_record = next((r for r in data if r.get("name") == "requirements.txt"), None)
    assert python_record is not None
    assert "technologies" in python_record
    assert "Python" in python_record["technologies"]

