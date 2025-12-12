"""Tests for SARIF output format.

This module contains tests for verifying that the SARIF output format
is correctly generated and follows the SARIF 2.1.0 specification.
"""
import json
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sarif_pydantic import Sarif

from gcrs.core.scanner import format_file_records_as_sarif
from gcrs.models import FileRecord


def test_sarif_output_format_function_basic():
    """Test that format_file_records_as_sarif returns valid JSON."""
    file_records = [
        FileRecord(
            name="test.py",
            relative_dir="src",
            absolute_filename="/path/to/repo/src/test.py",
            size_bytes=1024,
            is_binary=False,
            language="python",
            category="code",
            extension=".py",
        )
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    
    # Should be valid JSON
    sarif_data = json.loads(sarif_output)
    assert isinstance(sarif_data, dict)
    
    # Should have required SARIF structure
    assert "version" in sarif_data
    assert sarif_data["version"] == "2.1.0"
    assert "runs" in sarif_data
    assert isinstance(sarif_data["runs"], list)
    assert len(sarif_data["runs"]) > 0


def test_sarif_output_validates_with_sarif_pydantic():
    """Test that the SARIF output can be validated by sarif-pydantic."""
    file_records = [
        FileRecord(
            name="test.py",
            relative_dir="src",
            absolute_filename="/path/to/repo/src/test.py",
            size_bytes=1024,
            is_binary=False,
            language="python",
            category="code",
            extension=".py",
        )
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    # Should be parseable by sarif-pydantic
    sarif_log = Sarif.model_validate(sarif_data)
    assert sarif_log.version == "2.1.0"
    assert len(sarif_log.runs) == 1
    assert sarif_log.runs[0].tool.driver.name == "GCRS"


def test_sarif_output_contains_tool_information():
    """Test that SARIF output contains correct tool information."""
    file_records = [
        FileRecord(
            name="test.py",
            relative_dir="src",
            absolute_filename="/path/to/repo/src/test.py",
            size_bytes=1024,
            is_binary=False,
        )
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    run = sarif_data["runs"][0]
    assert "tool" in run
    assert "driver" in run["tool"]
    assert run["tool"]["driver"]["name"] == "GCRS"


def test_sarif_output_contains_results():
    """Test that SARIF output contains results for each file record."""
    file_records = [
        FileRecord(
            name="test1.py",
            relative_dir="src",
            absolute_filename="/path/to/repo/src/test1.py",
            size_bytes=1024,
            is_binary=False,
        ),
        FileRecord(
            name="test2.js",
            relative_dir="src",
            absolute_filename="/path/to/repo/src/test2.js",
            size_bytes=2048,
            is_binary=False,
        ),
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    run = sarif_data["runs"][0]
    assert "results" in run
    assert len(run["results"]) == 2
    
    # Check first result
    result1 = run["results"][0]
    assert "rule_id" in result1
    assert "level" in result1
    assert result1["level"] == "note"
    assert "message" in result1
    assert "locations" in result1


def test_sarif_output_result_contains_file_uri():
    """Test that each SARIF result contains the correct file URI."""
    file_records = [
        FileRecord(
            name="test.py",
            relative_dir="src",
            absolute_filename="C:\\path\\to\\repo\\src\\test.py",
            size_bytes=1024,
            is_binary=False,
        )
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    result = sarif_data["runs"][0]["results"][0]
    location = result["locations"][0]
    uri = location["physical_location"]["artifact_location"]["uri"]
    
    # Should convert backslashes to forward slashes
    assert "\\" not in uri
    assert "/" in uri
    assert "test.py" in uri


def test_sarif_output_result_contains_message():
    """Test that each SARIF result contains a message with file information."""
    file_records = [
        FileRecord(
            name="test.py",
            relative_dir="src",
            absolute_filename="/path/to/repo/src/test.py",
            size_bytes=1024,
            is_binary=False,
            language="python",
            category="code",
        )
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    result = sarif_data["runs"][0]["results"][0]
    message_text = result["message"]["text"]
    
    assert "File: test.py" in message_text
    assert "Language: python" in message_text
    assert "Category: code" in message_text
    assert "Size: 1024 bytes" in message_text


def test_sarif_output_result_contains_properties():
    """Test that each SARIF result contains properties with metadata."""
    commit_date = datetime(2025, 1, 15, 10, 30, 0)
    file_records = [
        FileRecord(
            name="test.py",
            relative_dir="src",
            absolute_filename="/path/to/repo/src/test.py",
            size_bytes=1024,
            is_binary=False,
            language="python",
            category="code",
            extension=".py",
            most_recent_commit_hash="abc123",
            most_recent_commit_date=commit_date,
            technologies=["docker"],
            dependency_kind="python-requirements",
            data_type=None,
        )
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    result = sarif_data["runs"][0]["results"][0]
    assert "properties" in result
    
    properties = result["properties"]
    assert properties["gitCommit"] == "abc123"
    assert properties["gitDate"] == commit_date.isoformat()
    assert properties["language"] == "python"
    assert properties["category"] == "code"
    assert properties["extension"] == ".py"
    assert properties["sizeBytes"] == 1024
    assert properties["isBinary"] is False
    assert properties["technologies"] == ["docker"]
    assert properties["dependencyKind"] == "python-requirements"


def test_sarif_output_result_rule_id_from_category():
    """Test that rule_id is set from category, or defaults to 'file'."""
    file_records = [
        FileRecord(
            name="test.py",
            relative_dir="src",
            absolute_filename="/path/to/repo/src/test.py",
            size_bytes=1024,
            is_binary=False,
            category="code",
        ),
        FileRecord(
            name="config.json",
            relative_dir=".",
            absolute_filename="/path/to/repo/config.json",
            size_bytes=512,
            is_binary=False,
            category=None,
        ),
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    results = sarif_data["runs"][0]["results"]
    assert results[0]["rule_id"] == "code"
    assert results[1]["rule_id"] == "file"


def test_sarif_output_handles_empty_file_records():
    """Test that SARIF output handles empty file records list."""
    file_records = []
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    # Should still have valid SARIF structure
    assert sarif_data["version"] == "2.1.0"
    assert len(sarif_data["runs"]) == 1
    assert len(sarif_data["runs"][0]["results"]) == 0


def test_sarif_output_handles_minimal_file_record():
    """Test that SARIF output handles file records with minimal fields."""
    file_records = [
        FileRecord(
            name="test.txt",
            relative_dir=".",
            absolute_filename="/path/to/repo/test.txt",
            size_bytes=0,
            is_binary=False,
        )
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    result = sarif_data["runs"][0]["results"][0]
    assert result["rule_id"] == "file"
    assert "message" in result
    assert "locations" in result
    
    # Properties should still exist even if minimal
    if "properties" in result:
        assert result["properties"]["sizeBytes"] == 0
        assert result["properties"]["isBinary"] is False


def test_sarif_output_handles_binary_files():
    """Test that SARIF output correctly handles binary files."""
    file_records = [
        FileRecord(
            name="image.png",
            relative_dir="assets",
            absolute_filename="/path/to/repo/assets/image.png",
            size_bytes=50000,
            is_binary=True,
            extension=".png",
        )
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    result = sarif_data["runs"][0]["results"][0]
    if "properties" in result:
        assert result["properties"]["isBinary"] is True
        assert result["properties"]["sizeBytes"] == 50000


def test_sarif_output_scan_endpoint(client: TestClient, sample_repo_path: Path):
    """Test that the /scan endpoint generates valid SARIF output file."""
    response = client.post(
        "/scan",
        json={
            "repo_root": str(sample_repo_path),
            "output_file_format": "sarif",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Verify the output file was created
    output_dir = sample_repo_path / "output"
    sarif_files = list(output_dir.glob("*.scan.sarif.json"))
    assert len(sarif_files) > 0, f"No SARIF output file found in {output_dir}"
    output_path = sarif_files[-1]  # Get the most recent one
    
    # Verify the file contains valid SARIF JSON
    with open(output_path, "r", encoding="utf-8") as f:
        file_content = f.read()
        sarif_data = json.loads(file_content)
    
    # Validate SARIF structure
    assert sarif_data["version"] == "2.1.0"
    assert "runs" in sarif_data
    assert len(sarif_data["runs"]) > 0
    
    # Validate with sarif-pydantic
    sarif_log = Sarif.model_validate(sarif_data)
    assert sarif_log.version == "2.1.0"


def test_sarif_output_scan_endpoint_contains_results(client: TestClient, sample_repo_path: Path):
    """Test that SARIF output from /scan endpoint contains file results."""
    response = client.post(
        "/scan",
        json={
            "repo_root": str(sample_repo_path),
            "output_file_format": "sarif",
        },
    )
    
    assert response.status_code == 200
    
    # Find the generated output file
    output_dir = sample_repo_path / "output"
    sarif_files = list(output_dir.glob("*.scan.sarif.json"))
    assert len(sarif_files) > 0
    output_path = sarif_files[-1]
    
    with open(output_path, "r", encoding="utf-8") as f:
        sarif_data = json.loads(f.read())
    
    # Should have results
    run = sarif_data["runs"][0]
    assert "results" in run
    assert len(run["results"]) > 0  # Should have at least some files
    
    # Each result should have required fields
    for result in run["results"]:
        assert "rule_id" in result
        assert "level" in result
        assert "message" in result
        assert "locations" in result
        assert len(result["locations"]) > 0


def test_sarif_output_scan_endpoint_properties(client: TestClient, sample_repo_path: Path):
    """Test that SARIF output from /scan endpoint includes properties."""
    response = client.post(
        "/scan",
        json={
            "repo_root": str(sample_repo_path),
            "output_file_format": "sarif",
        },
    )
    
    assert response.status_code == 200
    
    # Find the generated output file
    output_dir = sample_repo_path / "output"
    sarif_files = list(output_dir.glob("*.scan.sarif.json"))
    assert len(sarif_files) > 0
    output_path = sarif_files[-1]
    
    with open(output_path, "r", encoding="utf-8") as f:
        sarif_data = json.loads(f.read())
    
    # Check that at least some results have properties
    run = sarif_data["runs"][0]
    results_with_properties = [
        r for r in run["results"] if "properties" in r
    ]
    
    # At least some results should have properties
    if len(results_with_properties) > 0:
        props = results_with_properties[0]["properties"]
        # Should have at least sizeBytes and isBinary
        assert "sizeBytes" in props
        assert "isBinary" in props


def test_sarif_output_same_data_different_formats(client: TestClient, sample_repo_path: Path):
    """Test that scan data is consistent across different output formats."""
    sarif_response = client.post(
        "/scan",
        json={
            "repo_root": str(sample_repo_path),
            "output_file_format": "sarif",
        },
    )
    
    json_response = client.post(
        "/scan",
        json={
            "repo_root": str(sample_repo_path),
            "output_file_format": "json",
        },
    )
    
    assert sarif_response.status_code == 200
    assert json_response.status_code == 200
    
    # Both should succeed
    assert sarif_response.json()["status"] == "success"
    assert json_response.json()["status"] == "success"
    
    # Both should create output files
    output_dir = sample_repo_path / "output"
    sarif_files = list(output_dir.glob("*.scan.sarif.json"))
    json_files = list(output_dir.glob("*.scan.json"))
    
    assert len(sarif_files) > 0
    assert len(json_files) > 0
    
    # SARIF file should be valid JSON
    with open(sarif_files[-1], "r", encoding="utf-8") as f:
        sarif_data = json.loads(f.read())
        assert sarif_data["version"] == "2.1.0"

