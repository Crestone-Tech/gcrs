"""Database module for GCRS persistence layer."""

from gcrs.db.database import get_db_session, init_db
from gcrs.db.models import (
    Base,
    BOM,
    BOMCommit,
    BOMFile,
    File,
    FileVersion,
    Repo,
    RepoCommit,
)
from gcrs.db.services import (
    add_bom_file,
    complete_bom,
    create_bom,
    get_latest_bom,
    get_or_create_file,
    get_or_create_file_version,
    get_or_create_repo,
    get_or_create_repo_commit,
    link_bom_commits,
    persist_scan_results,
)

__all__ = [
    "Base",
    "BOM",
    "BOMCommit",
    "BOMFile",
    "File",
    "FileVersion",
    "Repo",
    "RepoCommit",
    "get_db_session",
    "init_db",
    # Service functions
    "get_or_create_repo",
    "get_or_create_repo_commit",
    "get_or_create_file",
    "get_or_create_file_version",
    "create_bom",
    "add_bom_file",
    "link_bom_commits",
    "complete_bom",
    "get_latest_bom",
    "persist_scan_results",
]



