"""Tests for Git commit information functionality.

This module contains tests for:
- get_git_commit_info function
- FileRecord commit date and hash fields
- Integration with do_the_repo_scan
"""

import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gcrs.core.scanner import do_the_repo_scan, get_git_commit_info
from gcrs.models import FileRecord


class TestGetGitCommitInfo:
    """Tests for the get_git_commit_info function."""

    def test_get_git_commit_info_success(self, tmp_path: Path):
        """Test successful retrieval of Git commit info."""
        # Create a test file and .git directory
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Mock subprocess.run to return successful git log output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "a1b2c3d4e5f6789012345678901234567890abcd 2025-01-15 14:30:00 +0000\n"
        
        with patch("gcrs.core.scanner.subprocess.run", return_value=mock_result):
            commit_date, commit_hash = get_git_commit_info(test_file, tmp_path)
        
        assert commit_date is not None
        assert isinstance(commit_date, datetime)
        assert commit_date.year == 2025
        assert commit_date.month == 1
        assert commit_date.day == 15
        assert commit_hash == "a1b2c3d4e5f6789012345678901234567890abcd"

    def test_get_git_commit_info_no_git_repo(self, tmp_path: Path):
        """Test that None is returned when not in a Git repository."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")
        
        # Mock .git directory not existing
        with patch("pathlib.Path.exists", return_value=False):
            commit_date, commit_hash = get_git_commit_info(test_file, tmp_path)
        
        assert commit_date is None
        assert commit_hash is None

    def test_get_git_commit_info_file_not_tracked(self, tmp_path: Path):
        """Test that None is returned when file is not tracked in Git."""
        # Create a test file and .git directory
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Mock subprocess.run to return non-zero exit code (file not tracked)
        mock_result = MagicMock()
        mock_result.returncode = 128  # Git error code
        mock_result.stdout = ""
        
        with patch("gcrs.core.scanner.subprocess.run", return_value=mock_result):
            commit_date, commit_hash = get_git_commit_info(test_file, tmp_path)
        
        assert commit_date is None
        assert commit_hash is None

    def test_get_git_commit_info_file_not_under_repo_root(self, tmp_path: Path):
        """Test that None is returned when file is not under repo root."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")
        
        # Use a different repo_root that doesn't contain the file
        other_repo = tmp_path.parent / "other_repo"
        other_repo.mkdir()
        
        commit_date, commit_hash = get_git_commit_info(test_file, other_repo)
        
        assert commit_date is None
        assert commit_hash is None

    def test_get_git_commit_info_git_not_installed(self, tmp_path: Path):
        """Test that None is returned when Git is not installed."""
        # Create a test file and .git directory
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Mock FileNotFoundError (git command not found)
        with patch("gcrs.core.scanner.subprocess.run", side_effect=FileNotFoundError()):
            commit_date, commit_hash = get_git_commit_info(test_file, tmp_path)
        
        assert commit_date is None
        assert commit_hash is None

    def test_get_git_commit_info_timeout(self, tmp_path: Path):
        """Test that None is returned when Git command times out."""
        # Create a test file and .git directory
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Mock TimeoutExpired exception
        with patch(
            "gcrs.core.scanner.subprocess.run",
            side_effect=subprocess.TimeoutExpired("git", 1)
        ):
            commit_date, commit_hash = get_git_commit_info(test_file, tmp_path)
        
        assert commit_date is None
        assert commit_hash is None

    def test_get_git_commit_info_invalid_date_format(self, tmp_path: Path):
        """Test that None is returned when date format is invalid."""
        # Create a test file and .git directory
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Mock subprocess.run to return invalid date format
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "a1b2c3d4e5f6789012345678901234567890abcd invalid-date-format\n"
        
        with patch("gcrs.core.scanner.subprocess.run", return_value=mock_result):
            commit_date, commit_hash = get_git_commit_info(test_file, tmp_path)
        
        assert commit_date is None
        assert commit_hash is None

    def test_get_git_commit_info_with_timezone(self, tmp_path: Path):
        """Test parsing commit date with timezone offset."""
        # Create a test file and .git directory
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Mock subprocess.run to return date with timezone
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "a1b2c3d4e5f6789012345678901234567890abcd 2025-01-15 14:30:00 -0500\n"
        
        with patch("gcrs.core.scanner.subprocess.run", return_value=mock_result):
            commit_date, commit_hash = get_git_commit_info(test_file, tmp_path)
        
        assert commit_date is not None
        assert isinstance(commit_date, datetime)
        # Timezone should be stripped, so we get naive datetime
        assert commit_date.year == 2025
        assert commit_date.month == 1
        assert commit_date.day == 15
        assert commit_date.hour == 14
        assert commit_date.minute == 30


class TestFileRecordCommitFields:
    """Tests for FileRecord commit date and hash fields."""

    def test_file_record_with_commit_info(self):
        """Test FileRecord creation with commit date and hash."""
        commit_date = datetime(2025, 1, 15, 14, 30, 0)
        commit_hash = "a1b2c3d4e5f6789012345678901234567890abcd"
        
        file_record = FileRecord(
            name="test.py",
            relative_dir=".",
            absolute_filename="/path/to/test.py",
            size_bytes=100,
            is_binary=False,
            most_recent_commit_date=commit_date,
            most_recent_commit_hash=commit_hash,
        )
        
        assert file_record.most_recent_commit_date == commit_date
        assert file_record.most_recent_commit_hash == commit_hash

    def test_file_record_without_commit_info(self):
        """Test FileRecord creation without commit date and hash."""
        file_record = FileRecord(
            name="test.py",
            relative_dir=".",
            absolute_filename="/path/to/test.py",
            size_bytes=100,
            is_binary=False,
            most_recent_commit_date=None,
            most_recent_commit_hash=None,
        )
        
        assert file_record.most_recent_commit_date is None
        assert file_record.most_recent_commit_hash is None

    def test_file_record_commit_info_optional(self):
        """Test that commit fields are optional (default to None)."""
        file_record = FileRecord(
            name="test.py",
            relative_dir=".",
            absolute_filename="/path/to/test.py",
            size_bytes=100,
            is_binary=False,
        )
        
        assert file_record.most_recent_commit_date is None
        assert file_record.most_recent_commit_hash is None

    def test_file_record_json_serialization_with_commit_date(self):
        """Test that FileRecord with commit date can be JSON serialized."""
        commit_date = datetime(2025, 1, 15, 14, 30, 0)
        commit_hash = "a1b2c3d4e5f6789012345678901234567890abcd"
        
        file_record = FileRecord(
            name="test.py",
            relative_dir=".",
            absolute_filename="/path/to/test.py",
            size_bytes=100,
            is_binary=False,
            most_recent_commit_date=commit_date,
            most_recent_commit_hash=commit_hash,
        )
        
        # Test model_dump with mode='json' (used in write_file_records_to_file)
        json_dict = file_record.model_dump(mode='json')
        
        assert "most_recent_commit_date" in json_dict
        assert "most_recent_commit_hash" in json_dict
        # Date should be serialized as ISO format string
        assert isinstance(json_dict["most_recent_commit_date"], str)
        assert json_dict["most_recent_commit_hash"] == commit_hash


class TestDoTheRepoScanWithCommitInfo:
    """Tests for do_the_repo_scan integration with commit info."""

    def test_do_the_repo_scan_includes_commit_info(self, tmp_path: Path):
        """Test that do_the_repo_scan includes commit info in FileRecord objects."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")
        
        # Mock get_git_commit_info to return commit info
        mock_commit_date = datetime(2025, 1, 15, 14, 30, 0)
        mock_commit_hash = "a1b2c3d4e5f6789012345678901234567890abcd"
        
        with patch(
            "gcrs.core.scanner.get_git_commit_info",
            return_value=(mock_commit_date, mock_commit_hash)
        ):
            file_records, _ = do_the_repo_scan(tmp_path, respect_gitignore=False)
        
        assert len(file_records) > 0
        # Find the test.py file record
        test_record = next((r for r in file_records if r.name == "test.py"), None)
        assert test_record is not None
        assert test_record.most_recent_commit_date == mock_commit_date
        assert test_record.most_recent_commit_hash == mock_commit_hash

    def test_do_the_repo_scan_without_commit_info(self, tmp_path: Path):
        """Test that do_the_repo_scan handles missing commit info gracefully."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")
        
        # Mock get_git_commit_info to return None (no Git repo or file not tracked)
        with patch(
            "gcrs.core.scanner.get_git_commit_info",
            return_value=(None, None)
        ):
            file_records, _ = do_the_repo_scan(tmp_path, respect_gitignore=False)
        
        assert len(file_records) > 0
        # Find the test.py file record
        test_record = next((r for r in file_records if r.name == "test.py"), None)
        assert test_record is not None
        assert test_record.most_recent_commit_date is None
        assert test_record.most_recent_commit_hash is None

