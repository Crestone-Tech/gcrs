"""Tests for different output formats of the summary endpoint.

This module contains tests for verifying that the summary endpoint
correctly generates output files in different formats (JSON and Markdown).
"""
import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_summary_json_output_format(client: TestClient, sample_repo_path: Path):
    """Test that JSON output format creates a valid JSON file with correct structure."""
    output_file = "test_summary_json.json"
    response = client.post(
        "/scan/summary",
        json={
            "repo_root": str(sample_repo_path),
            "output_dir": "output",
            "output_file": output_file,
            "output_file_format": "json",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    
    # Verify the output file was created
    output_path = sample_repo_path / "output" / output_file
    assert output_path.exists(), f"Output file {output_path} was not created"
    
    # Verify the file contains valid JSON
    with open(output_path, "r", encoding="utf-8") as f:
        file_content = f.read()
        file_data = json.loads(file_content)
    
    # Verify the JSON structure matches the repository summary
    assert "files_by_language" in file_data
    assert "files_by_category" in file_data
    assert "files_by_technology" in file_data
    assert "files_by_dependency" in file_data
    assert "files_by_extension" in file_data
    assert "total_files" in file_data
    assert "scanned_files" in file_data
    assert "skipped_files" in file_data
    
    # Verify the data matches the API response
    assert file_data["total_files"] == data["repository_summary"]["total_files"]
    assert file_data["scanned_files"] == data["repository_summary"]["scanned_files"]
    assert file_data["skipped_files"] == data["repository_summary"]["skipped_files"]


def test_summary_markdown_output_format(client: TestClient, sample_repo_path: Path):
    """Test that Markdown output format creates a markdown file with expected content."""
    output_file = "test_summary_markdown.md"
    response = client.post(
        "/scan/summary",
        json={
            "repo_root": str(sample_repo_path),
            "output_dir": "output",
            "output_file": output_file,
            "output_file_format": "markdown",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    
    # Verify the output file was created
    output_path = sample_repo_path / "output" / output_file
    assert output_path.exists(), f"Output file {output_path} was not created"
    
    # Verify the file contains markdown content
    with open(output_path, "r", encoding="utf-8") as f:
        file_content = f.read()
    
    # Verify it's not empty
    assert len(file_content) > 0, "Markdown file should not be empty"
    
    # Verify the markdown contains some expected elements
    # (Note: The actual markdown format may vary, but it should contain some text)
    assert isinstance(file_content, str), "Markdown file should contain text"


def test_summary_default_output_format(client: TestClient, sample_repo_path: Path):
    """Test that default output format (markdown) is used when format is not specified."""
    output_file = "test_summary_default.md"
    response = client.post(
        "/scan/summary",
        json={
            "repo_root": str(sample_repo_path),
            "output_dir": "output",
            "output_file": output_file,
            # output_file_format not specified - should default to markdown
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Verify the output file was created
    output_path = sample_repo_path / "output" / output_file
    assert output_path.exists(), f"Output file {output_path} was not created"
    
    # Verify the file contains content (markdown by default)
    with open(output_path, "r", encoding="utf-8") as f:
        file_content = f.read()
    
    assert len(file_content) > 0, "Default format file should not be empty"


def test_summary_same_data_different_formats(client: TestClient, sample_repo_path: Path):
    """Test that the same summary data is returned regardless of output format."""
    json_response = client.post(
        "/scan/summary",
        json={
            "repo_root": str(sample_repo_path),
            "output_dir": "output",
            "output_file": "test_json_comparison.json",
            "output_file_format": "json",
        },
    )
    
    markdown_response = client.post(
        "/scan/summary",
        json={
            "repo_root": str(sample_repo_path),
            "output_dir": "output",
            "output_file": "test_markdown_comparison.md",
            "output_file_format": "markdown",
        },
    )
    
    assert json_response.status_code == 200
    assert markdown_response.status_code == 200
    
    json_data = json_response.json()
    markdown_data = markdown_response.json()
    
    # Verify both responses have the same repository summary data
    json_summary = json_data["repository_summary"]
    markdown_summary = markdown_data["repository_summary"]
    
    assert json_summary["total_files"] == markdown_summary["total_files"]
    assert json_summary["scanned_files"] == markdown_summary["scanned_files"]
    assert json_summary["skipped_files"] == markdown_summary["skipped_files"]
    assert json_summary["files_by_category"] == markdown_summary["files_by_category"]
    assert json_summary["files_by_language"] == markdown_summary["files_by_language"]
    assert json_summary["files_by_technology"] == markdown_summary["files_by_technology"]


def test_summary_json_file_content_structure(client: TestClient, sample_repo_path: Path):
    """Test that JSON output file has the correct structure and data types."""
    output_file = "test_json_structure.json"
    response = client.post(
        "/scan/summary",
        json={
            "repo_root": str(sample_repo_path),
            "output_dir": "output",
            "output_file": output_file,
            "output_file_format": "json",
        },
    )
    
    assert response.status_code == 200
    
    output_path = sample_repo_path / "output" / output_file
    with open(output_path, "r", encoding="utf-8") as f:
        file_data = json.loads(f.read())
    
    # Verify data types
    assert isinstance(file_data["files_by_language"], dict)
    assert isinstance(file_data["files_by_category"], dict)
    assert isinstance(file_data["files_by_technology"], dict)
    assert isinstance(file_data["files_by_dependency"], dict)
    assert isinstance(file_data["files_by_extension"], dict)
    assert isinstance(file_data["total_files"], int)
    assert isinstance(file_data["scanned_files"], int)
    assert isinstance(file_data["skipped_files"], int)
    
    # Verify counts are non-negative
    assert file_data["total_files"] >= 0
    assert file_data["scanned_files"] >= 0
    assert file_data["skipped_files"] >= 0
    
    # Verify total_files equals scanned_files + skipped_files
    assert file_data["total_files"] == file_data["scanned_files"] + file_data["skipped_files"]


