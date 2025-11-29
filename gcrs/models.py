"""Pydantic models for the Green Cloud Repository Scanner."""

from typing import Literal

from pydantic import BaseModel, Field

class FileRecord(BaseModel):
    """Represents a file record with metadata about a file in a repository."""

    relative_dir: str = Field(
        description="Directory path relative to repository root (e.g., 'src/utils')",
        json_schema_extra={"example": "src/utils"},
    )
    absolute_filename: str = Field(
        description="Absolute filename (e.g., '/path/to/repository/src/utils/scanner.py')",
        json_schema_extra={"example": "C:\\absolute\\path\\to\\sample_repo\\src\\utils\\scanner.py"},
    )
    name: str = Field(
        description="Filename (e.g., 'scanner.py')",
        json_schema_extra={"example": "scanner.py"},
    )
    extension: str | None = Field(
        default=None,
        description="File extension in lowercase (e.g., '.py', '.js')",
        json_schema_extra={"examples": [".py", ".js", ".md", ".txt", ".log"]},
    )
    category: str | None = Field(
        default=None,
        description="File category (e.g., 'code', 'config', 'docs')",
        json_schema_extra={"examples": ["code", "config", "docs"]},
    )
    language: str | None = Field(
        default=None,
        description="Programming language detected (e.g., 'python', 'javascript')",
        json_schema_extra={"examples": ["python", "javascript"]},
    )
    technologies: list[str] = Field(
        default_factory=list,
        description="List of technologies detected (e.g., ['docker', 'kubernetes'])",
        json_schema_extra={"examples": ["docker", "kubernetes", "terraform", "ansible"]},
    )
    data_type: str | None = Field(
        default=None,
        description="Data file type (e.g., 'csv', 'jsonl', 'xml', 'tsv', 'parquet', 'sqlite')",
        json_schema_extra={"examples": ["csv", "jsonl", "xml", "tsv", "parquet", "sqlite"]},
    )
    dependency_kind: str | None = Field(
        default=None,
        description="Dependency management system type (e.g., 'python-requirements', 'node-package')",
        json_schema_extra={"examples": ["python-requirements", "node-package"]},
    )
    size_bytes: int = Field(
        description="File size in bytes",
        json_schema_extra={"example": 1024},
    )
    is_binary: bool = Field(
        description="Boolean, True if the file is binary, False otherwise",
        json_schema_extra={"example": False},
    )

class ScanParams(BaseModel):
    """Parameters for repository scan request."""
    
    repo_root: str = Field(
        default=".",
        description="Path to the repository root directory to scan",
        json_schema_extra={"examples": [".", "/path/to/repository","../../relative/path/to/repository", "C:\\absolute\\path\\to\\sample_repo"]},
    )
    output_file_format: Literal["json", "markdown", "csv"] = Field(
        default="json",
        description="Format of the output file. Defaults to json if blank/not provided. Other options are markdown and csv. Markdown and csv output tables.",
        json_schema_extra={"examples": ["json", "markdown", "csv"]},
    )

class RepositorySummary(BaseModel):
    """Information about the repository."""

    files_by_language: dict[str, int] = Field(
        default_factory=dict,
        description="Number of files grouped by programming language",
        json_schema_extra={"example": {"python": 50, "javascript": 30}},
    )
    files_by_category: dict[str, int] = Field(
        default_factory=dict,
        description="Number of files grouped by category (code, config, docs, etc.)",
        json_schema_extra={"example": {"code": 80, "config": 10, "docs": 5}},
    )
    files_by_technology: dict[str, int] = Field(
        default_factory=dict,
        description="Number of files grouped by technology (Docker, Kubernetes, etc.)",
        json_schema_extra={"example": {"Docker": 3, "Kubernetes": 2}},
    )
    files_by_dependency: dict[str, int] = Field(
        default_factory=dict,
        description="Number of files grouped by dependency management system",
        json_schema_extra={"example": {"python-requirements": 1, "node-package": 1}},
    )
    files_by_extension: dict[str, int] = Field(
        default_factory=dict,
        description="Number of files grouped by file extension",
        json_schema_extra={"example": {".py": 50, ".js": 30, ".md": 5}},
    )
    binary_files_by_extension: dict[str, int] = Field(
        default_factory=dict,
        description="Number of binary files grouped by file extension",
        json_schema_extra={"example": {".png": 10, ".jpg": 5, ".pdf": 2}},
    )
    files_without_extension: int = Field(
        default=0,
        description="Number of files without a file extension",
        json_schema_extra={"example": 3},
    )
    files_with_extension: int = Field(
        default=0,
        description="Number of files with a file extension",
        json_schema_extra={"example": 147},
    )
    data_files_by_extension: dict[str, int] = Field(
        default_factory=dict,
        description="Number of data files grouped by extension (csv, jsonl, xml, etc.)",
        json_schema_extra={"example": {"csv": 5, "jsonl": 2}},
    )
    total_files: int = Field(
        default=0,
        description="Total number of files in the repository",
        json_schema_extra={"example": 150},
    )
    scanned_files: int = Field(
        default=0,
        description="Number of files successfully scanned",
        json_schema_extra={"example": 145},
    )
    skipped_files: int = Field(
        default=0,
        description="Number of files skipped during scanning",
        json_schema_extra={"example": 5},
    )

class SummaryResponse(BaseModel):
    """Response model containing summary results for a repository."""
    
    status: Literal["success", "error"] = Field(
        description="Status of the scan operation: 'success' or 'error'",
        json_schema_extra={"example": "success"},
    )
    repository_summary: RepositorySummary = Field(
        description="Summary of the repository contents",
        #json_schema_extra={"example": RepositorySummary(self, files_by_language={"javascript": 1}, files_by_category={"code": 1}, files_by_technology={"Docker": 1}, files_by_dependency={"python-requirements": 1}, files_by_extension={".js": 1}, binary_files_by_extension={".png": 1}, files_without_extension=0, files_with_extension=1, data_files_by_extension={"csv": 1}, total_files=1, scanned_files=1, skipped_files=0)},
    )
    error: str | None = Field(
        default=None,
        description="Error message if the scan operation failed (status='error')",
        json_schema_extra={"example": None},
    )
    # TODO: consider adding the output file path to the response

class ScanResponse(BaseModel):
    """Response model containing scan results for a repository."""

    status: Literal["success", "error"] = Field(
        description="Status of the scan operation: 'success' or 'error'",
        json_schema_extra={"example": "success"},
    )
    error: str | None = Field(
        default=None,
        description="Error message if the scan operation failed (status='error')",
        json_schema_extra={"example": None},
    )
    # TODO: Add output_file?