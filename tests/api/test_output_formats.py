"""Tests for different output formats of the summary endpoint.

This module contains tests for verifying that the summary endpoint
correctly generates output files in different formats (JSON and Markdown).
"""
import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_summary_json_output_format(client: TestClient, sample_repo_path: Path):
    """Test that JSON output format creates a valid JSON file with correct structure."""
    response = client.post(
        "/scan/summary",
        json={
            "repo_root": str(sample_repo_path),
            "output_file_format": "json",
            "persist_to_db": False,
            "skip_git_commit_info": True,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    
    # Verify the output file was created (find the generated file)
    output_dir = sample_repo_path / "output"
    json_files = list(output_dir.glob("*.summary.json"))
    assert len(json_files) > 0, f"No JSON output file found in {output_dir}"
    output_path = json_files[-1]  # Get the most recent one
    
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
    response = client.post(
        "/scan/summary",
        json={
            "repo_root": str(sample_repo_path),
            "output_file_format": "markdown",
            "persist_to_db": False,
            "skip_git_commit_info": True,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "repository_summary" in data
    
    # Verify the output file was created (find the generated file)
    output_dir = sample_repo_path / "output"
    md_files = list(output_dir.glob("*.summary.md"))
    assert len(md_files) > 0, f"No Markdown output file found in {output_dir}"
    output_path = md_files[-1]  # Get the most recent one
    
    # Verify the file contains markdown content
    with open(output_path, "r", encoding="utf-8") as f:
        file_content = f.read()
        lines = file_content.splitlines()
    
    # Verify it's not empty
    assert len(file_content) > 0, "Markdown file should not be empty"
    
    # Verify the markdown structure matches expected format
    assert lines[0].strip() == "# Repository Summary", f"First line should be '# Repository Summary', got: {lines[0]}"
    assert lines[1].strip().startswith("## Total Files:"), f"Second line should start with '## Total Files:', got: {lines[1]}"
    assert lines[2].strip().startswith("## Scanned Files:"), f"Third line should start with '## Scanned Files:', got: {lines[2]}"
    assert lines[3].strip().startswith("## Skipped Files:"), f"Fourth line should start with '## Skipped Files:', got: {lines[3]}"
    assert lines[4].strip().startswith("## Files without Extension:"), f"Fifth line should start with '## Files without Extension:', got: {lines[4]}"
    assert lines[5].strip().startswith("## Files with Extension:"), f"Sixth line should start with '## Files with Extension:', got: {lines[5]}"
    assert lines[6].strip() == "## Files by Language:", f"Seventh line should be '## Files by Language:', got: {lines[6]}"
    
    # Verify the language list items start with proper indentation and bullet
    assert lines[7].strip().startswith("- "), f"Eighth line should start with '- ', got: {lines[7]}"
    assert lines[8].strip().startswith("- "), f"Ninth line should start with '- ', got: {lines[8]}"
    
    # Verify the values in the markdown match the API response
    summary = data["repository_summary"]
    assert f"## Total Files: {summary['total_files']}" in file_content
    assert f"## Scanned Files: {summary['scanned_files']}" in file_content
    assert f"## Skipped Files: {summary['skipped_files']}" in file_content
    assert f"## Files without Extension: {summary['files_without_extension']}" in file_content
    assert f"## Files with Extension: {summary['files_with_extension']}" in file_content



def test_summary_default_output_format(client: TestClient, sample_repo_path: Path):
    """Test that default output format (json) is used when format is not specified."""
    response = client.post(
        "/scan/summary",
        json={
            "repo_root": str(sample_repo_path),
            "persist_to_db": False,
            "skip_git_commit_info": True,
            # output_file_format not specified - should default to json
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Verify the output file was created (find the generated file)
    output_dir = sample_repo_path / "output"
    json_files = list(output_dir.glob("*.summary.json"))
    assert len(json_files) > 0, f"No JSON output file found in {output_dir}"
    output_path = json_files[-1]  # Get the most recent one
    
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
            "output_file_format": "json",
            "persist_to_db": False,
            "skip_git_commit_info": True,
        },
    )
    
    markdown_response = client.post(
        "/scan/summary",
        json={
            "repo_root": str(sample_repo_path),
            "output_file_format": "markdown",
            "persist_to_db": False,
            "skip_git_commit_info": True,
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
    response = client.post(
        "/scan/summary",
        json={
            "repo_root": str(sample_repo_path),
            "output_file_format": "json",
            "persist_to_db": False,
            "skip_git_commit_info": True,
        },
    )
    
    assert response.status_code == 200
    
    # Find the generated output file
    output_dir = sample_repo_path / "output"
    json_files = list(output_dir.glob("*.summary.json"))
    assert len(json_files) > 0, f"No JSON output file found in {output_dir}"
    output_path = json_files[-1]  # Get the most recent one
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


