"""Pydantic models for the Green Cloud Repository Scanner."""

from pydantic import BaseModel


class FileRecord(BaseModel):
    """Represents a file record with metadata about a file in a repository."""

    relative_dir: str  # e.g., "src/utils" (relative to repo root)
    name: str  # e.g., "scanner.py"
    extension: str  # e.g., ".py"
    category: str  # e.g., "code", "config", "docs", etc.
    language: str | None = None  # e.g., "python"
    technologies: list[str] = []  # e.g., ["docker", "kubernetes"]
    dependency_kind: str | None = None  # e.g., "python-requirements", "npm-package"
    size_bytes: int
    is_binary: bool


class ScanResponse(BaseModel):
    """Response model containing scan results for a repository."""

    records: list[FileRecord]
    root: str
    scanned_count: int
    skipped_count: int
