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
            "persist_to_db": False,
            "skip_git_commit_info": True,
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
            "persist_to_db": False,
            "skip_git_commit_info": True,
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
            "persist_to_db": False,
            "skip_git_commit_info": True,
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
            "persist_to_db": False,
            "skip_git_commit_info": True,
        },
    )
    
    json_response = client.post(
        "/scan",
        json={
            "repo_root": str(sample_repo_path),
            "output_file_format": "json",
            "persist_to_db": False,
            "skip_git_commit_info": True,
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


def test_sarif_output_multiple_technologies():
    """Test that SARIF output handles multiple technologies correctly."""
    file_records = [
        FileRecord(
            name="docker-compose.yml",
            relative_dir=".",
            absolute_filename="/path/to/repo/docker-compose.yml",
            size_bytes=1024,
            is_binary=False,
            technologies=["docker", "kubernetes", "terraform"],
        )
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    result = sarif_data["runs"][0]["results"][0]
    assert "properties" in result
    assert result["properties"]["technologies"] == ["docker", "kubernetes", "terraform"]


def test_sarif_output_empty_technologies_list():
    """Test that empty technologies list is not included in properties."""
    file_records = [
        FileRecord(
            name="test.py",
            relative_dir="src",
            absolute_filename="/path/to/repo/src/test.py",
            size_bytes=1024,
            is_binary=False,
            technologies=[],  # Empty list
        )
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    result = sarif_data["runs"][0]["results"][0]
    # Properties should exist but technologies should not be included
    if "properties" in result:
        assert "technologies" not in result["properties"]


def test_sarif_output_message_with_zero_size():
    """Test that message does not include size when size_bytes is 0."""
    file_records = [
        FileRecord(
            name="empty.txt",
            relative_dir=".",
            absolute_filename="/path/to/repo/empty.txt",
            size_bytes=0,  # Zero size
            is_binary=False,
            language="python",
        )
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    result = sarif_data["runs"][0]["results"][0]
    message_text = result["message"]["text"]
    
    # Should not include "Size: 0 bytes" in message
    assert "Size: 0 bytes" not in message_text
    assert "File: empty.txt" in message_text
    # But sizeBytes should still be in properties
    if "properties" in result:
        assert result["properties"]["sizeBytes"] == 0


def test_sarif_output_different_data_types():
    """Test that different data types are correctly included in properties."""
    data_types = ["csv", "jsonl", "xml", "tsv", "parquet", "sqlite"]
    
    for data_type in data_types:
        file_records = [
            FileRecord(
                name=f"data.{data_type}",
                relative_dir="data",
                absolute_filename=f"/path/to/repo/data/data.{data_type}",
                size_bytes=1024,
                is_binary=False,
                data_type=data_type,
            )
        ]
        
        sarif_output = format_file_records_as_sarif(file_records)
        sarif_data = json.loads(sarif_output)
        
        result = sarif_data["runs"][0]["results"][0]
        assert "properties" in result
        assert result["properties"]["dataType"] == data_type


def test_sarif_output_different_dependency_kinds():
    """Test that different dependency kinds are correctly included in properties."""
    dependency_kinds = [
        "python-requirements",
        "node-package",
        "go-mod",
        "rust-cargo",
        "maven-pom",
    ]
    
    for dep_kind in dependency_kinds:
        file_records = [
            FileRecord(
                name="dependency.file",
                relative_dir=".",
                absolute_filename="/path/to/repo/dependency.file",
                size_bytes=512,
                is_binary=False,
                dependency_kind=dep_kind,
            )
        ]
        
        sarif_output = format_file_records_as_sarif(file_records)
        sarif_data = json.loads(sarif_output)
        
        result = sarif_data["runs"][0]["results"][0]
        assert "properties" in result
        assert result["properties"]["dependencyKind"] == dep_kind


def test_sarif_output_special_characters_in_filename():
    """Test that special characters in file names are handled correctly."""
    file_records = [
        FileRecord(
            name="test file with spaces.py",
            relative_dir="src",
            absolute_filename="/path/to/repo/src/test file with spaces.py",
            size_bytes=1024,
            is_binary=False,
        ),
        FileRecord(
            name="file-with-dashes.js",
            relative_dir="src",
            absolute_filename="/path/to/repo/src/file-with-dashes.js",
            size_bytes=2048,
            is_binary=False,
        ),
        FileRecord(
            name="file_with_underscores.ts",
            relative_dir="src",
            absolute_filename="/path/to/repo/src/file_with_underscores.ts",
            size_bytes=3072,
            is_binary=False,
        ),
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    results = sarif_data["runs"][0]["results"]
    assert len(results) == 3
    
    # Check that file names appear correctly in messages
    assert "test file with spaces.py" in results[0]["message"]["text"]
    assert "file-with-dashes.js" in results[1]["message"]["text"]
    assert "file_with_underscores.ts" in results[2]["message"]["text"]


def test_sarif_output_unicode_characters():
    """Test that Unicode characters in file names are handled correctly."""
    file_records = [
        FileRecord(
            name="测试文件.py",
            relative_dir="src",
            absolute_filename="/path/to/repo/src/测试文件.py",
            size_bytes=1024,
            is_binary=False,
        ),
        FileRecord(
            name="файл.js",
            relative_dir="src",
            absolute_filename="/path/to/repo/src/файл.js",
            size_bytes=2048,
            is_binary=False,
        ),
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    # Should be valid JSON with Unicode
    assert isinstance(sarif_data, dict)
    
    results = sarif_data["runs"][0]["results"]
    assert len(results) == 2
    
    # Check that Unicode appears in messages
    assert "测试文件.py" in results[0]["message"]["text"]
    assert "файл.js" in results[1]["message"]["text"]


def test_sarif_output_uri_mixed_slashes():
    """Test that URIs with mixed slashes are normalized correctly."""
    file_records = [
        FileRecord(
            name="test.py",
            relative_dir="src",
            absolute_filename="C:\\path\\to\\repo\\src\\test.py",  # Windows path
            size_bytes=1024,
            is_binary=False,
        ),
        FileRecord(
            name="test2.py",
            relative_dir="src",
            absolute_filename="C:/path/to/repo/src/test2.py",  # Mixed slashes
            size_bytes=2048,
            is_binary=False,
        ),
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    results = sarif_data["runs"][0]["results"]
    
    # All URIs should use forward slashes
    for result in results:
        location = result["locations"][0]
        uri = location["physical_location"]["artifact_location"]["uri"]
        assert "\\" not in uri
        assert "/" in uri


def test_sarif_output_properties_only_when_non_empty():
    """Test that properties dict is only included when it has content."""
    # Record with minimal fields (only required)
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
    # Properties should exist because sizeBytes and isBinary are always added
    assert "properties" in result
    assert "sizeBytes" in result["properties"]
    assert "isBinary" in result["properties"]


def test_sarif_output_all_optional_fields_populated():
    """Test SARIF output with all optional fields populated."""
    commit_date = datetime(2025, 1, 15, 10, 30, 45)
    file_records = [
        FileRecord(
            name="comprehensive.py",
            relative_dir="src/utils",
            absolute_filename="/path/to/repo/src/utils/comprehensive.py",
            size_bytes=5432,
            is_binary=False,
            extension=".py",
            category="code",
            language="python",
            data_type=None,
            dependency_kind="python-requirements",
            technologies=["docker", "kubernetes"],
            most_recent_commit_hash="a1b2c3d4e5f6789012345678901234567890abcd",
            most_recent_commit_date=commit_date,
        )
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    result = sarif_data["runs"][0]["results"][0]
    assert "properties" in result
    
    props = result["properties"]
    assert props["gitCommit"] == "a1b2c3d4e5f6789012345678901234567890abcd"
    assert props["gitDate"] == commit_date.isoformat()
    assert props["language"] == "python"
    assert props["category"] == "code"
    assert props["extension"] == ".py"
    assert props["sizeBytes"] == 5432
    assert props["isBinary"] is False
    assert props["technologies"] == ["docker", "kubernetes"]
    assert props["dependencyKind"] == "python-requirements"


def test_sarif_output_large_number_of_records():
    """Test that SARIF output handles a large number of file records."""
    file_records = [
        FileRecord(
            name=f"file_{i}.py",
            relative_dir="src",
            absolute_filename=f"/path/to/repo/src/file_{i}.py",
            size_bytes=1024 + i,
            is_binary=False,
            language="python",
            category="code",
        )
        for i in range(100)
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    # Should have valid SARIF structure
    assert sarif_data["version"] == "2.1.0"
    assert len(sarif_data["runs"]) == 1
    
    run = sarif_data["runs"][0]
    assert len(run["results"]) == 100
    
    # Validate with sarif-pydantic
    sarif_log = Sarif.model_validate(sarif_data)
    assert len(sarif_log.runs[0].results) == 100


def test_sarif_output_json_formatting():
    """Test that SARIF output is properly formatted JSON with indentation."""
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
    
    # Should be valid JSON
    sarif_data = json.loads(sarif_output)
    assert isinstance(sarif_data, dict)
    
    # Should have proper indentation (check for newlines and spaces)
    lines = sarif_output.split("\n")
    assert len(lines) > 1  # Should be multi-line
    
    # Should start with opening brace and version
    assert sarif_output.strip().startswith("{")
    assert '"version"' in sarif_output
    assert '"2.1.0"' in sarif_output


def test_sarif_output_message_ordering():
    """Test that message parts are in the correct order."""
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
    
    # Message should start with "File:"
    assert message_text.startswith("File: test.py")
    # Should contain all parts in order
    parts = message_text.split(" | ")
    assert parts[0] == "File: test.py"
    assert "Language: python" in parts
    assert "Category: code" in parts
    assert "Size: 1024 bytes" in parts


def test_sarif_output_no_properties_when_all_optional_none():
    """Test that properties dict structure is correct even when optional fields are None."""
    file_records = [
        FileRecord(
            name="test.txt",
            relative_dir=".",
            absolute_filename="/path/to/repo/test.txt",
            size_bytes=100,
            is_binary=False,
            # All optional fields are None or empty
            extension=None,
            category=None,
            language=None,
            data_type=None,
            dependency_kind=None,
            technologies=[],
            most_recent_commit_hash=None,
            most_recent_commit_date=None,
        )
    ]
    
    sarif_output = format_file_records_as_sarif(file_records)
    sarif_data = json.loads(sarif_output)
    
    result = sarif_data["runs"][0]["results"][0]
    # Properties should exist with only required fields
    assert "properties" in result
    props = result["properties"]
    assert "sizeBytes" in props
    assert "isBinary" in props
    # Optional fields should not be present
    assert "gitCommit" not in props
    assert "gitDate" not in props
    assert "language" not in props
    assert "category" not in props
    assert "extension" not in props
    assert "technologies" not in props
    assert "dependencyKind" not in props
    assert "dataType" not in props

