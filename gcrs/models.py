"""Pydantic models for the Green Cloud Repository Scanner."""

from pydantic import BaseModel, Field


class FileRecord(BaseModel):
    """Represents a file record with metadata about a file in a repository."""

    relative_dir: str  # e.g., "src/utils" (relative to repo root)
    name: str  # e.g., "scanner.py"
    extension: str | None = None # e.g., ".py"
    category: str | None = None # e.g., "code", "config", "docs", etc.
    language: str | None = None  # e.g., "python"
    technologies: list[str] = []  # e.g., ["docker", "kubernetes"]
    data_type: str | None = None # e.g., "csv", "jsonl", "xml", "tsv", "parquet", "sqlite", "db", "ndjson"
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
    
    status: str = Field(
        description="Status of the scan operation: 'success' or 'error'",
        example="success",
    )
    summary: str | None = Field(
        default=None,
        description="Summary of the repository contents. If the summary generation failed, this will be None.",
        example=None,
    )
    repo_root: str = Field(
        description="Absolute path to the root of the scanned repository",
        example="/path/to/repository",
    )
    files_scanned: int | None = Field(
        default=None,
        description="Number of files successfully scanned",
        example=150,
    )
    files_skipped: int | None = Field(
        default=None,
        description="Number of files skipped during scanning (e.g., binary files, excluded directories)",
        example=5,
    )
    error: str | None = Field(
        default=None,
        description="Error message if the scan operation failed (status='error')",
        example=None,
    )

class RepositorySummary(BaseModel):
    """Information about the repository."""

    files_by_language: dict[str, int]  # number of files by language
    files_by_category: dict[str, int]  # number of files by category
    files_by_technology: dict[str, int]  # number of files by technology
    files_by_dependency: dict[str, int]  # number of files by dependency
    files_by_extension: dict[str, int]  # number of files by file extension
    files_without_extension: int = 0 # number of files without an extension
    files_with_extension: int = 0 # number of files with an extension
    data_files_by_extension: dict[str, int]  # number of data files by extension
    total_files: int = 0
    scanned_files: int = 0
    skipped_files: int = 0

