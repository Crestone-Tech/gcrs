"""Tests for database service layer functions."""

from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from gcrs.db.models import File, Repo
from gcrs.db.services import (
    add_bom_file,
    complete_bom,
    create_bom,
    get_latest_bom,
    get_or_create_file,
    get_or_create_file_version,
    get_or_create_repo,
    get_or_create_repo_commit,
    get_repo_summary_from_db,
    link_bom_commits,
    persist_scan_results,
)
from gcrs.models import FileRecord, RepositorySummary, ScanParams


class TestGetOrCreateRepo:
    """Tests for get_or_create_repo function."""

    def test_create_new_repo(self, test_db_session: Session):
        """Test creating a new repository."""
        repo = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )

        assert repo.id is not None
        assert repo.uri == "https://github.com/test/repo.git"
        assert repo.git_owner_account == "github.com/test"
        assert repo.name == "test-repo"
        test_db_session.commit()

    def test_get_existing_repo(self, test_db_session: Session):
        """Test getting an existing repository by URI."""
        # Create first repo
        repo1 = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        test_db_session.commit()

        # Try to get the same repo
        repo2 = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )

        assert repo1.id == repo2.id
        assert repo1.uri == repo2.uri

    def test_repo_uri_uniqueness(self, test_db_session: Session):
        """Test that repo URI must be unique."""
        repo1 = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        test_db_session.commit()

        # Try to create another repo with same URI but different name
        repo2 = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="different-name",
        )

        # Should return the same repo
        assert repo1.id == repo2.id


class TestGetOrCreateRepoCommit:
    """Tests for get_or_create_repo_commit function."""

    def test_create_new_commit(self, test_db_session: Session):
        """Test creating a new commit."""
        repo = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        test_db_session.commit()

        commit = get_or_create_repo_commit(
            session=test_db_session,
            repo_id=repo.id,
            commit_hash="a1b2c3d4e5f6789012345678901234567890abcd",
            commit_timestamp=datetime(2025, 1, 15, 14, 30, 0),
        )

        assert commit.id is not None
        assert commit.repo_id == repo.id
        assert commit.hash == "a1b2c3d4e5f6789012345678901234567890abcd"
        assert commit.timestamp == datetime(2025, 1, 15, 14, 30, 0)
        test_db_session.commit()

    def test_get_existing_commit(self, test_db_session: Session):
        """Test getting an existing commit."""
        repo = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        test_db_session.commit()

        commit_hash = "a1b2c3d4e5f6789012345678901234567890abcd"
        commit1 = get_or_create_repo_commit(
            session=test_db_session,
            repo_id=repo.id,
            commit_hash=commit_hash,
            commit_timestamp=datetime(2025, 1, 15, 14, 30, 0),
        )
        test_db_session.commit()

        commit2 = get_or_create_repo_commit(
            session=test_db_session,
            repo_id=repo.id,
            commit_hash=commit_hash,
            commit_timestamp=datetime(2025, 1, 15, 14, 30, 0),
        )

        assert commit1.id == commit2.id


class TestGetOrCreateFile:
    """Tests for get_or_create_file function."""

    def test_create_new_file(self, test_db_session: Session):
        """Test creating a new file."""
        repo = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        test_db_session.commit()

        file = get_or_create_file(
            session=test_db_session,
            repo_id=repo.id,
            file_path="src/main.py",
            file_name="main.py",
        )

        assert file.id is not None
        assert file.repo_id == repo.id
        assert file.path == "src/main.py"
        assert file.name == "main.py"
        test_db_session.commit()

    def test_get_existing_file(self, test_db_session: Session):
        """Test getting an existing file."""
        repo = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        test_db_session.commit()

        file1 = get_or_create_file(
            session=test_db_session,
            repo_id=repo.id,
            file_path="src/main.py",
            file_name="main.py",
        )
        test_db_session.commit()

        file2 = get_or_create_file(
            session=test_db_session,
            repo_id=repo.id,
            file_path="src/main.py",
            file_name="main.py",
        )

        assert file1.id == file2.id


class TestGetOrCreateFileVersion:
    """Tests for get_or_create_file_version function."""

    def test_create_new_file_version(self, test_db_session: Session):
        """Test creating a new file version."""
        repo = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        commit = get_or_create_repo_commit(
            session=test_db_session,
            repo_id=repo.id,
            commit_hash="a1b2c3d4e5f6789012345678901234567890abcd",
            commit_timestamp=datetime(2025, 1, 15, 14, 30, 0),
        )
        file = get_or_create_file(
            session=test_db_session,
            repo_id=repo.id,
            file_path="src/main.py",
            file_name="main.py",
        )
        test_db_session.commit()

        file_version = get_or_create_file_version(
            session=test_db_session,
            file_id=file.id,
            commit_id=commit.id,
            file_path="src/main.py",
            size_bytes=1024,
            content_hash=None,
        )

        assert file_version.id is not None
        assert file_version.file_id == file.id
        assert file_version.commit_id == commit.id
        assert file_version.size_bytes == 1024
        test_db_session.commit()

    def test_get_existing_file_version(self, test_db_session: Session):
        """Test getting an existing file version (idempotency)."""
        repo = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        commit = get_or_create_repo_commit(
            session=test_db_session,
            repo_id=repo.id,
            commit_hash="a1b2c3d4e5f6789012345678901234567890abcd",
            commit_timestamp=datetime(2025, 1, 15, 14, 30, 0),
        )
        file = get_or_create_file(
            session=test_db_session,
            repo_id=repo.id,
            file_path="src/main.py",
            file_name="main.py",
        )
        test_db_session.commit()

        file_version1 = get_or_create_file_version(
            session=test_db_session,
            file_id=file.id,
            commit_id=commit.id,
            file_path="src/main.py",
            size_bytes=1024,
        )
        test_db_session.commit()

        file_version2 = get_or_create_file_version(
            session=test_db_session,
            file_id=file.id,
            commit_id=commit.id,
            file_path="src/main.py",
            size_bytes=1024,
        )

        assert file_version1.id == file_version2.id


class TestBOMOperations:
    """Tests for BOM-related operations."""

    def test_create_bom(self, test_db_session: Session):
        """Test creating a new BOM."""
        repo = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        test_db_session.commit()

        scan_config = {
            "output_file_format": "json",
            "skip_dirs": [],
            "respect_gitignore": True,
        }

        bom = create_bom(
            session=test_db_session,
            repo_id=repo.id,
            repo_root="/path/to/repo",
            scan_config=scan_config,
            start_timestamp=datetime(2025, 1, 15, 14, 30, 0),
        )

        assert bom.id is not None
        assert bom.repo_id == repo.id
        assert bom.status == "in_progress"
        assert bom.repo_root == "/path/to/repo"
        assert bom.scan_config == scan_config
        test_db_session.commit()

    def test_complete_bom(self, test_db_session: Session):
        """Test completing a BOM."""
        repo = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        test_db_session.commit()

        bom = create_bom(
            session=test_db_session,
            repo_id=repo.id,
            repo_root="/path/to/repo",
            scan_config={"output_file_format": "json"},
            start_timestamp=datetime(2025, 1, 15, 14, 30, 0),
        )
        test_db_session.commit()

        end_time = datetime(2025, 1, 15, 14, 35, 0)
        completed_bom = complete_bom(
            session=test_db_session,
            bom_id=bom.id,
            status="success",
            end_timestamp=end_time,
        )

        assert completed_bom.status == "success"
        assert completed_bom.end_timestamp == end_time
        assert completed_bom.execution_time_seconds == 300.0  # 5 minutes
        test_db_session.commit()

    def test_get_latest_bom(self, test_db_session: Session):
        """Test getting the latest BOM for a repository."""
        repo = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        test_db_session.commit()

        # Create older BOM
        bom1 = create_bom(
            session=test_db_session,
            repo_id=repo.id,
            repo_root="/path/to/repo",
            scan_config={"output_file_format": "json"},
            start_timestamp=datetime(2025, 1, 15, 14, 30, 0),
        )
        test_db_session.commit()

        # Create newer BOM
        bom2 = create_bom(
            session=test_db_session,
            repo_id=repo.id,
            repo_root="/path/to/repo",
            scan_config={"output_file_format": "json"},
            start_timestamp=datetime(2025, 1, 15, 15, 30, 0),
        )
        test_db_session.commit()

        latest = get_latest_bom(session=test_db_session, repo_id=repo.id)

        assert latest is not None
        assert latest.id == bom2.id


class TestBOMFileOperations:
    """Tests for BOM file operations."""

    def test_add_bom_file(self, test_db_session: Session):
        """Test adding a file to a BOM."""
        repo = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        commit = get_or_create_repo_commit(
            session=test_db_session,
            repo_id=repo.id,
            commit_hash="a1b2c3d4e5f6789012345678901234567890abcd",
            commit_timestamp=datetime(2025, 1, 15, 14, 30, 0),
        )
        file = get_or_create_file(
            session=test_db_session,
            repo_id=repo.id,
            file_path="src/main.py",
            file_name="main.py",
        )
        file_version = get_or_create_file_version(
            session=test_db_session,
            file_id=file.id,
            commit_id=commit.id,
            file_path="src/main.py",
            size_bytes=1024,
        )
        bom = create_bom(
            session=test_db_session,
            repo_id=repo.id,
            repo_root="/path/to/repo",
            scan_config={"output_file_format": "json"},
        )
        test_db_session.commit()

        bom_file = add_bom_file(
            session=test_db_session,
            bom_id=bom.id,
            file_version_id=file_version.id,
            absolute_filename="/absolute/path/to/main.py",
            extension=".py",
            is_binary=False,
            category="code",
            language="python",
        )

        assert bom_file.id is not None
        assert bom_file.bom_id == bom.id
        assert bom_file.file_version_id == file_version.id
        assert bom_file.language == "python"
        assert bom_file.category == "code"
        test_db_session.commit()


class TestLinkBOMCommits:
    """Tests for linking commits to BOMs."""

    def test_link_bom_commits(self, test_db_session: Session):
        """Test linking commits to a BOM."""
        repo = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        commit1 = get_or_create_repo_commit(
            session=test_db_session,
            repo_id=repo.id,
            commit_hash="a1b2c3d4e5f6789012345678901234567890abcd",
            commit_timestamp=datetime(2025, 1, 15, 14, 30, 0),
        )
        commit2 = get_or_create_repo_commit(
            session=test_db_session,
            repo_id=repo.id,
            commit_hash="b2c3d4e5f6789012345678901234567890abcdef",
            commit_timestamp=datetime(2025, 1, 15, 15, 30, 0),
        )
        bom = create_bom(
            session=test_db_session,
            repo_id=repo.id,
            repo_root="/path/to/repo",
            scan_config={"output_file_format": "json"},
        )
        test_db_session.commit()

        bom_commits = link_bom_commits(
            session=test_db_session,
            bom_id=bom.id,
            commit_ids=[commit1.id, commit2.id],
        )

        assert len(bom_commits) == 2
        assert all(bc.bom_id == bom.id for bc in bom_commits)
        assert {bc.commit_id for bc in bom_commits} == {commit1.id, commit2.id}
        test_db_session.commit()


class TestPersistScanResults:
    """Tests for persist_scan_results function."""

    def test_persist_scan_results(self, test_db_session: Session, tmp_path: Path):
        """Test persisting scan results to database."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        file_records = [
            FileRecord(
                name="test.py",
                relative_dir=".",
                absolute_filename=str(repo_path / "test.py"),
                size_bytes=100,
                is_binary=False,
                extension=".py",
                category="code",
                language="python",
                most_recent_commit_hash="a1b2c3d4e5f6789012345678901234567890abcd",
                most_recent_commit_date=datetime(2025, 1, 15, 14, 30, 0),
            ),
            FileRecord(
                name="README.md",
                relative_dir=".",
                absolute_filename=str(repo_path / "README.md"),
                size_bytes=50,
                is_binary=False,
                extension=".md",
                category="docs",
                language="markdown",
                most_recent_commit_hash="a1b2c3d4e5f6789012345678901234567890abcd",
                most_recent_commit_date=datetime(2025, 1, 15, 14, 30, 0),
            ),
        ]

        scan_params = ScanParams(
            repo_root=str(repo_path),
            output_file_format="json",
            skip_dirs=[],
            respect_gitignore=True,
        )

        bom = persist_scan_results(
            session=test_db_session,
            repo_root=repo_path,
            file_records=file_records,
            scan_params=scan_params,
            repo_uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
        )

        assert bom.id is not None
        assert bom.status == "success"
        assert bom.end_timestamp is not None
        test_db_session.commit()

        # Verify repo was created
        from gcrs.db.models import Repo
        from sqlalchemy import select

        stmt = select(Repo).where(Repo.uri == "https://github.com/test/repo.git")
        repo = test_db_session.scalar(stmt)
        assert repo is not None

        # Verify files were created
        stmt = select(File).where(File.repo_id == repo.id)
        files = test_db_session.scalars(stmt).all()
        assert len(files) == 2

    def test_persist_scan_results_missing_commit_hash(self, test_db_session: Session, tmp_path: Path):
        """Test that persist_scan_results raises error for files without commit hash."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        file_records = [
            FileRecord(
                name="test.py",
                relative_dir=".",
                absolute_filename=str(repo_path / "test.py"),
                size_bytes=100,
                is_binary=False,
                most_recent_commit_hash=None,  # Missing commit hash
                most_recent_commit_date=None,
            ),
        ]

        scan_params = ScanParams(
            repo_root=str(repo_path),
            output_file_format="json",
        )

        with pytest.raises(ValueError, match="has no commit hash"):
            persist_scan_results(
                session=test_db_session,
                repo_root=repo_path,
                file_records=file_records,
                scan_params=scan_params,
            )


class TestGetRepoSummaryFromDB:
    """Tests for get_repo_summary_from_db function."""

    def test_get_repo_summary_from_db(self, test_db_session: Session):
        """Test getting repository summary from database."""
        repo = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        commit = get_or_create_repo_commit(
            session=test_db_session,
            repo_id=repo.id,
            commit_hash="a1b2c3d4e5f6789012345678901234567890abcd",
            commit_timestamp=datetime(2025, 1, 15, 14, 30, 0),
        )
        file = get_or_create_file(
            session=test_db_session,
            repo_id=repo.id,
            file_path="src/main.py",
            file_name="main.py",
        )
        file_version = get_or_create_file_version(
            session=test_db_session,
            file_id=file.id,
            commit_id=commit.id,
            file_path="src/main.py",
            size_bytes=1024,
        )
        bom = create_bom(
            session=test_db_session,
            repo_id=repo.id,
            repo_root="/path/to/repo",
            scan_config={"output_file_format": "json"},
        )
        add_bom_file(
            session=test_db_session,
            bom_id=bom.id,
            file_version_id=file_version.id,
            absolute_filename="/path/to/main.py",
            extension=".py",
            is_binary=False,
            category="code",
            language="python",
        )
        complete_bom(session=test_db_session, bom_id=bom.id, status="success")
        test_db_session.commit()

        summary = get_repo_summary_from_db(
            session=test_db_session,
            repo_id=repo.id,
            bom_id=bom.id,
        )

        assert summary is not None
        assert isinstance(summary, RepositorySummary)
        assert summary.total_files == 1
        assert summary.scanned_files == 1
        assert summary.files_by_language.get("python") == 1
        assert summary.files_by_category.get("code") == 1

    def test_get_repo_summary_from_db_no_bom(self, test_db_session: Session):
        """Test getting summary when no BOM exists."""
        repo = get_or_create_repo(
            session=test_db_session,
            uri="https://github.com/test/repo.git",
            git_owner_account="github.com/test",
            repo_name="test-repo",
        )
        test_db_session.commit()

        summary = get_repo_summary_from_db(
            session=test_db_session,
            repo_id=repo.id,
        )

        assert summary is None

