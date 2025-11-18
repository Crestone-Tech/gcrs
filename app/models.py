"""Pydantic models for the Green Cloud Repository Scanner."""

from pydantic import BaseModel


class FileRecord(BaseModel):
    """Represents a file record with metadata about a file in a repository."""

    relative_dir: str  # e.g., "src/utils" (relative to repo root)
    name: str  # e.g., "scanner.py"
    extension: str | None = None # e.g., ".py"
    category: str | None = None # e.g., "code", "config", "docs", etc.
    language: str | None = None  # e.g., "python"
    technologies: list[str] = []  # e.g., ["docker", "kubernetes"]
    dependency_kind: str | None = None  # e.g., "python-requirements", "npm-package"
    size_bytes: int
    is_binary: bool


class ScanResponse(BaseModel):
    """Response model containing scan results for a repository."""

    repo_root: str
    scanned_count: int
    skipped_count: int

class SummaryResponse(BaseModel):
    """Response model containing summary results for a repository."""

    status: str
    summary: str | None = None # summary of the repository contents. If the summary generation failed, this will be None.
    repo_root: str # path to the root of the repository
    files_scanned: int | None = None  # number of files scanned
    files_skipped: int | None = None  # number of files skipped
    error: str | None = None  # error message if the summary generation failed

class RepositorySummary(BaseModel):
    """Information about the repository."""

    language_files: dict[str, int] # number of files by language
    category_files: dict[str, int] # number of files by category
    technology_files: dict[str, int] # number of files by technology
    dependency_files: dict[str, int] # number of files by dependency
    file_extensions: dict[str, int] # number of files by file extension
    total_files: int = 0
    scanned_files: int = 0
    skipped_files: int = 0
    summary: str = ""