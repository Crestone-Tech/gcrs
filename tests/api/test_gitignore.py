"""Tests for .gitignore support in repository scanning.

This module contains tests for verifying that the scanner correctly
respects .gitignore files when the respect_gitignore parameter is enabled.
"""
import subprocess
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient


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
    
    # Add all files and commit
    subprocess.run(
        ["git", "add", "-A"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )


def test_respect_gitignore_enabled_skips_ignored_files(client: TestClient):
    """Test that when respect_gitignore=True, files matching .gitignore patterns are skipped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        # Create a .gitignore file
        gitignore_path = repo_root / ".gitignore"
        gitignore_path.write_text("*.log\n*.tmp\nignored_dir/\n", encoding="utf-8")
        
        # Create files that should be ignored
        (repo_root / "app.log").write_text("log content", encoding="utf-8")
        (repo_root / "temp.tmp").write_text("temp content", encoding="utf-8")
        ignored_dir = repo_root / "ignored_dir"
        ignored_dir.mkdir()
        (ignored_dir / "file.txt").write_text("ignored file", encoding="utf-8")
        
        # Create files that should NOT be ignored
        (repo_root / "app.py").write_text("python code", encoding="utf-8")
        (repo_root / "readme.md").write_text("readme content", encoding="utf-8")
        included_dir = repo_root / "included_dir"
        included_dir.mkdir()
        (included_dir / "file.txt").write_text("included file", encoding="utf-8")
        
        # Initialize as git repository (required for scanning)
        _init_git_repo(repo_root)
        
        # Scan with respect_gitignore=True (default)
        response = client.post(
            "/scan/summary",
            json={
                "repo_root": str(repo_root),
                "respect_gitignore": True,
                "output_file_format": "json",
                "persist_to_db": False,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        summary = data["repository_summary"]
        
        # Verify ignored files are not in the scan
        # Should find: .gitignore, app.py, readme.md, included_dir/file.txt
        # Should NOT find: app.log, temp.tmp, ignored_dir/file.txt
        assert summary["scanned_files"] == 4, f"Expected 4 files (.gitignore + 3 others), got {summary['scanned_files']}"
        
        # Verify specific files are present/absent
        files_by_extension = summary["files_by_extension"]
        assert files_by_extension.get(".py") == 1, "app.py should be scanned"
        assert files_by_extension.get(".md") == 1, "readme.md should be scanned"
        assert files_by_extension.get(".txt") == 1, "included_dir/file.txt should be scanned"
        assert ".log" not in files_by_extension, "app.log should be ignored"
        assert ".tmp" not in files_by_extension, "temp.tmp should be ignored"


def test_respect_gitignore_disabled_includes_ignored_files(client: TestClient):
    """Test that when respect_gitignore=False, files matching .gitignore patterns are included."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        # Create a .gitignore file
        gitignore_path = repo_root / ".gitignore"
        gitignore_path.write_text("*.log\n*.tmp\nignored_dir/\n", encoding="utf-8")
        
        # Create files that would be ignored if respect_gitignore=True
        (repo_root / "app.log").write_text("log content", encoding="utf-8")
        (repo_root / "temp.tmp").write_text("temp content", encoding="utf-8")
        ignored_dir = repo_root / "ignored_dir"
        ignored_dir.mkdir()
        (ignored_dir / "file.txt").write_text("ignored file", encoding="utf-8")
        
        # Create files that should always be included
        (repo_root / "app.py").write_text("python code", encoding="utf-8")
        (repo_root / "readme.md").write_text("readme content", encoding="utf-8")
        
        # Initialize as git repository (required for scanning)
        _init_git_repo(repo_root)
        
        # Scan with respect_gitignore=False
        response = client.post(
            "/scan/summary",
            json={
                "repo_root": str(repo_root),
                "respect_gitignore": False,
                "output_file_format": "json",
                "persist_to_db": False,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        summary = data["repository_summary"]
        
        # Verify all files are scanned (including those that would be ignored)
        # Should find: .gitignore, app.py, readme.md, app.log, temp.tmp, ignored_dir/file.txt
        assert summary["scanned_files"] == 6, f"Expected 6 files (.gitignore + 5 others), got {summary['scanned_files']}"
        
        # Verify all file types are present
        files_by_extension = summary["files_by_extension"]
        assert files_by_extension.get(".py") == 1, "app.py should be scanned"
        assert files_by_extension.get(".md") == 1, "readme.md should be scanned"
        assert files_by_extension.get(".log") == 1, "app.log should be scanned when respect_gitignore=False"
        assert files_by_extension.get(".tmp") == 1, "temp.tmp should be scanned when respect_gitignore=False"
        assert files_by_extension.get(".txt") == 1, "ignored_dir/file.txt should be scanned when respect_gitignore=False"


def test_respect_gitignore_no_gitignore_file(client: TestClient):
    """Test that when respect_gitignore=True but no .gitignore exists, all files are scanned."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        # Create files without a .gitignore file
        (repo_root / "app.py").write_text("python code", encoding="utf-8")
        (repo_root / "readme.md").write_text("readme content", encoding="utf-8")
        (repo_root / "app.log").write_text("log content", encoding="utf-8")
        
        # Initialize as git repository (required for scanning)
        _init_git_repo(repo_root)
        
        # Scan with respect_gitignore=True but no .gitignore file
        response = client.post(
            "/scan/summary",
            json={
                "repo_root": str(repo_root),
                "respect_gitignore": True,
                "output_file_format": "json",
                "persist_to_db": False,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        summary = data["repository_summary"]
        
        # Verify all files are scanned when no .gitignore exists
        assert summary["scanned_files"] == 3, f"Expected 3 files, got {summary['scanned_files']}"
        
        files_by_extension = summary["files_by_extension"]
        assert files_by_extension.get(".py") == 1, "app.py should be scanned"
        assert files_by_extension.get(".md") == 1, "readme.md should be scanned"
        assert files_by_extension.get(".log") == 1, "app.log should be scanned when no .gitignore exists"


def test_respect_gitignore_default_behavior(client: TestClient):
    """Test that respect_gitignore defaults to True when not specified."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        # Create a .gitignore file
        gitignore_path = repo_root / ".gitignore"
        gitignore_path.write_text("*.log\n", encoding="utf-8")
        
        # Create files
        (repo_root / "app.py").write_text("python code", encoding="utf-8")
        (repo_root / "app.log").write_text("log content", encoding="utf-8")
        
        # Initialize as git repository (required for scanning)
        _init_git_repo(repo_root)
        
        # Scan without specifying respect_gitignore (should default to True)
        response = client.post(
            "/scan/summary",
            json={
                "repo_root": str(repo_root),
                "output_file_format": "json",
                "persist_to_db": False,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        summary = data["repository_summary"]
        
        # Verify .log file is ignored (default behavior)
        # Should find: .gitignore, app.py
        assert summary["scanned_files"] == 2, f"Expected 2 files (.gitignore + app.py), got {summary['scanned_files']}"
        
        files_by_extension = summary["files_by_extension"]
        assert files_by_extension.get(".py") == 1, "app.py should be scanned"
        assert ".log" not in files_by_extension, "app.log should be ignored by default"

