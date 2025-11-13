"""Pydantic models for the Green Cloud Repository Scanner."""

from typing import Optional, List
from pydantic import BaseModel

class FileRecord(BaseModel):
    """Represents a file record with metadata about a file in a repository."""

    relative_dir: str              # e.g., "src/utils" (relative to repo root)
    name: str                      # e.g., "scanner.py"
    extension: str                 # e.g., ".py"
    category: str                  # e.g., "code", "config", "docs", etc.
    language: Optional[str] = None # e.g., "python"
    technologies: List[str] = []   # e.g., ["docker", "kubernetes"]
    dependency_kind: Optional[str] = None  # e.g., "python-requirements", "npm-package"
    size_bytes: int
    is_binary: bool

class ScanResponse(BaseModel):
    """Response model containing scan results for a repository."""

    records: List[FileRecord]
    root: str
    scanned_count: int
    skipped_count: int
