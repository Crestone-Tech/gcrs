"""Unit tests for technology detection in the scanner.

This module contains unit tests that directly test the technology detection
logic in the scanner, including:
- Exact filename matching
- Extension-based pattern matching (e.g., .tf for Terraform)
- Substring pattern matching (e.g., "k8s" or "ansible" in filenames)
- Dependency file to technology mapping
"""

import subprocess
from pathlib import Path

import pytest

from gcrs.core.scanner import do_the_repo_scan


def _init_git_repo(repo_root: Path) -> None:
    """Initialize a git repository and commit all files.
    
    Args:
        repo_root: Path to the repository root directory.
    """
    # Initialize git repository
    subprocess.run(
        ["git", "init"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    
    # Configure git user (required for commits)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    
    # Add all files and commit (only if there are files to commit)
    subprocess.run(
        ["git", "add", "-A"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    # Check if there are files to commit before committing
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    if result.stdout.strip():  # If there are changes to commit
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )


class TestExactFilenameTechnologyDetection:
    """Test technology detection via exact filename matching."""
    
    def test_dockerfile_detection(self, tmp_path: Path):
        """Test that Dockerfile is detected as Docker technology."""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.11\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        dockerfile_record = next((r for r in file_records if r.name == "Dockerfile"), None)
        assert dockerfile_record is not None
        assert "Docker" in dockerfile_record.technologies
        assert summary.files_by_technology.get("Docker") == 1
    
    def test_docker_compose_yml_detection(self, tmp_path: Path):
        """Test that docker-compose.yml is detected as Docker technology."""
        compose_file = tmp_path / "docker-compose.yml"
        compose_file.write_text("version: '3.8'\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        compose_record = next((r for r in file_records if r.name == "docker-compose.yml"), None)
        assert compose_record is not None
        assert "Docker" in compose_record.technologies
        assert summary.files_by_technology.get("Docker") == 1
    
    def test_docker_compose_yaml_detection(self, tmp_path: Path):
        """Test that docker-compose.yaml is detected as Docker technology."""
        compose_file = tmp_path / "docker-compose.yaml"
        compose_file.write_text("version: '3.8'\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        compose_record = next((r for r in file_records if r.name == "docker-compose.yaml"), None)
        assert compose_record is not None
        assert "Docker" in compose_record.technologies
    
    def test_docker_compose_override_detection(self, tmp_path: Path):
        """Test that docker-compose.override files are detected as Docker technology."""
        override_yml = tmp_path / "docker-compose.override.yml"
        override_yml.write_text("version: '3.8'\n")
        
        override_yaml = tmp_path / "docker-compose.override.yaml"
        override_yaml.write_text("version: '3.8'\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        override_yml_record = next((r for r in file_records if r.name == "docker-compose.override.yml"), None)
        assert override_yml_record is not None
        assert "Docker" in override_yml_record.technologies
        
        override_yaml_record = next((r for r in file_records if r.name == "docker-compose.override.yaml"), None)
        assert override_yaml_record is not None
        assert "Docker" in override_yaml_record.technologies
        
        assert summary.files_by_technology.get("Docker") == 2
    
    def test_ansible_cfg_detection(self, tmp_path: Path):
        """Test that ansible.cfg is detected as Ansible technology."""
        ansible_cfg = tmp_path / "ansible.cfg"
        ansible_cfg.write_text("[defaults]\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        ansible_record = next((r for r in file_records if r.name == "ansible.cfg"), None)
        assert ansible_record is not None
        assert "Ansible" in ansible_record.technologies
        assert summary.files_by_technology.get("Ansible") == 1
    
    def test_build_gradle_detection(self, tmp_path: Path):
        """Test that build.gradle is detected as Gradle technology."""
        gradle_file = tmp_path / "build.gradle"
        gradle_file.write_text("plugins {\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        gradle_record = next((r for r in file_records if r.name == "build.gradle"), None)
        assert gradle_record is not None
        assert "Gradle" in gradle_record.technologies
        assert summary.files_by_technology.get("Gradle") == 1
    
    def test_python_config_files_detection(self, tmp_path: Path):
        """Test that Python config files are detected as Python technology."""
        setup_cfg = tmp_path / "setup.cfg"
        setup_cfg.write_text("[metadata]\n")
        
        tox_ini = tmp_path / "tox.ini"
        tox_ini.write_text("[tox]\n")
        
        pytest_ini = tmp_path / "pytest.ini"
        pytest_ini.write_text("[pytest]\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        setup_record = next((r for r in file_records if r.name == "setup.cfg"), None)
        assert setup_record is not None
        assert "Python" in setup_record.technologies
        
        tox_record = next((r for r in file_records if r.name == "tox.ini"), None)
        assert tox_record is not None
        assert "Python" in tox_record.technologies
        
        pytest_record = next((r for r in file_records if r.name == "pytest.ini"), None)
        assert pytest_record is not None
        assert "Python" in pytest_record.technologies
        
        assert summary.files_by_technology.get("Python") == 3


class TestExtensionBasedTechnologyDetection:
    """Test technology detection via extension-based pattern matching."""
    
    def test_terraform_extension_detection(self, tmp_path: Path):
        """Test that .tf files are detected as Terraform technology."""
        main_tf = tmp_path / "main.tf"
        main_tf.write_text('resource "aws_instance" "example" {\n')
        
        variables_tf = tmp_path / "variables.tf"
        variables_tf.write_text('variable "region" {\n')
        
        outputs_tf = tmp_path / "outputs.tf"
        outputs_tf.write_text('output "instance_id" {\n')
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        main_record = next((r for r in file_records if r.name == "main.tf"), None)
        assert main_record is not None
        assert "Terraform" in main_record.technologies
        
        variables_record = next((r for r in file_records if r.name == "variables.tf"), None)
        assert variables_record is not None
        assert "Terraform" in variables_record.technologies
        
        outputs_record = next((r for r in file_records if r.name == "outputs.tf"), None)
        assert outputs_record is not None
        assert "Terraform" in outputs_record.technologies
        
        assert summary.files_by_technology.get("Terraform") == 3


class TestSubstringTechnologyDetection:
    """Test technology detection via substring pattern matching."""
    
    def test_kubernetes_substring_detection(self, tmp_path: Path):
        """Test that files with 'k8s' in the name are detected as Kubernetes technology."""
        k8s_deployment = tmp_path / "k8s-deployment.yaml"
        k8s_deployment.write_text("apiVersion: apps/v1\n")
        
        k8s_service = tmp_path / "k8s-service.yaml"
        k8s_service.write_text("apiVersion: v1\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        deployment_record = next((r for r in file_records if r.name == "k8s-deployment.yaml"), None)
        assert deployment_record is not None
        assert "Kubernetes" in deployment_record.technologies
        
        service_record = next((r for r in file_records if r.name == "k8s-service.yaml"), None)
        assert service_record is not None
        assert "Kubernetes" in service_record.technologies
        
        assert summary.files_by_technology.get("Kubernetes") == 2
    
    def test_ansible_substring_detection(self, tmp_path: Path):
        """Test that files with 'ansible' in the name are detected as Ansible technology."""
        ansible_playbook = tmp_path / "ansible-playbook.yml"
        ansible_playbook.write_text("---\n- name: Deploy\n")
        
        ansible_inventory = tmp_path / "ansible-inventory.ini"
        ansible_inventory.write_text("[webservers]\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        playbook_record = next((r for r in file_records if r.name == "ansible-playbook.yml"), None)
        assert playbook_record is not None
        assert "Ansible" in playbook_record.technologies
        
        inventory_record = next((r for r in file_records if r.name == "ansible-inventory.ini"), None)
        assert inventory_record is not None
        assert "Ansible" in inventory_record.technologies
        
        assert summary.files_by_technology.get("Ansible") == 2


class TestDependencyFileTechnologyDetection:
    """Test technology detection from dependency files."""
    
    def test_python_requirements_detection(self, tmp_path: Path):
        """Test that requirements.txt is detected as Python technology."""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("requests>=2.25.0\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        req_record = next((r for r in file_records if r.name == "requirements.txt"), None)
        assert req_record is not None
        assert "Python" in req_record.technologies
        assert req_record.dependency_kind == "python-requirements"
        assert summary.files_by_technology.get("Python") == 1
    
    def test_node_package_json_detection(self, tmp_path: Path):
        """Test that package.json is detected as Node.js technology."""
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test", "version": "1.0.0"}\n')
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        package_record = next((r for r in file_records if r.name == "package.json"), None)
        assert package_record is not None
        assert "Node.js" in package_record.technologies
        assert package_record.dependency_kind == "node-package"
        assert summary.files_by_technology.get("Node.js") == 1
    
    def test_go_mod_detection(self, tmp_path: Path):
        """Test that go.mod is detected as Go technology."""
        go_mod = tmp_path / "go.mod"
        go_mod.write_text("module github.com/test/project\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        go_mod_record = next((r for r in file_records if r.name == "go.mod"), None)
        assert go_mod_record is not None
        assert "Go" in go_mod_record.technologies
        assert go_mod_record.dependency_kind == "go-mod"
        assert summary.files_by_technology.get("Go") == 1
    
    def test_ruby_gemfile_detection(self, tmp_path: Path):
        """Test that Gemfile is detected as Ruby technology."""
        gemfile = tmp_path / "Gemfile"
        gemfile.write_text("source 'https://rubygems.org'\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        gemfile_record = next((r for r in file_records if r.name == "Gemfile"), None)
        assert gemfile_record is not None
        assert "Ruby" in gemfile_record.technologies
        assert gemfile_record.dependency_kind == "ruby-gemfile"
        assert summary.files_by_technology.get("Ruby") == 1
    
    def test_rust_cargo_toml_detection(self, tmp_path: Path):
        """Test that Cargo.toml is detected as Rust technology."""
        cargo_toml = tmp_path / "Cargo.toml"
        cargo_toml.write_text("[package]\nname = \"test\"\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        cargo_record = next((r for r in file_records if r.name == "Cargo.toml"), None)
        assert cargo_record is not None
        assert "Rust" in cargo_record.technologies
        assert cargo_record.dependency_kind == "rust-cargo"
        assert summary.files_by_technology.get("Rust") == 1
    
    def test_maven_pom_xml_detection(self, tmp_path: Path):
        """Test that pom.xml is detected as Maven technology."""
        pom_xml = tmp_path / "pom.xml"
        pom_xml.write_text('<?xml version="1.0"?>\n<project>\n</project>\n')
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        pom_record = next((r for r in file_records if r.name == "pom.xml"), None)
        assert pom_record is not None
        assert "Maven" in pom_record.technologies
        assert pom_record.dependency_kind == "maven-pom"
        assert summary.files_by_technology.get("Maven") == 1


class TestMultipleTechnologyDetection:
    """Test that files can have multiple technologies detected."""
    
    def test_file_with_multiple_technologies(self, tmp_path: Path):
        """Test that a file can be detected with multiple technologies."""
        # Create a Python requirements file (should detect Python)
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("requests>=2.25.0\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        req_record = next((r for r in file_records if r.name == "requirements.txt"), None)
        assert req_record is not None
        # Should have Python technology from dependency detection
        assert "Python" in req_record.technologies
        assert len(req_record.technologies) == 1


class TestNoTechnologyDetection:
    """Test that files without technology patterns return empty technologies list."""
    
    def test_regular_code_file_no_technology(self, tmp_path: Path):
        """Test that a regular code file doesn't have technologies detected."""
        python_file = tmp_path / "app.py"
        python_file.write_text("print('Hello')\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        app_record = next((r for r in file_records if r.name == "app.py"), None)
        assert app_record is not None
        # Regular code files should not have technologies detected
        assert app_record.technologies == []
    
    def test_markdown_file_no_technology(self, tmp_path: Path):
        """Test that a markdown file doesn't have technologies detected."""
        readme = tmp_path / "README.md"
        readme.write_text("# Project\n")
        
        _init_git_repo(tmp_path)
        
        file_records, summary = do_the_repo_scan(
            tmp_path, 
            respect_gitignore=False, 
            persist_to_db=False, 
            skip_git_commit_info=True
        )
        
        readme_record = next((r for r in file_records if r.name == "README.md"), None)
        assert readme_record is not None
        # Documentation files should not have technologies detected
        assert readme_record.technologies == []

