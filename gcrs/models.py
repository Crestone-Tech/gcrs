"""Pydantic models for the Green Cloud Repository Scanner."""

from typing import Literal

from pydantic import BaseModel, Field


class FileRecord(BaseModel):
    """Represents a file record with metadata about a file in a repository."""

    relative_dir: str = Field(
        description="Directory path relative to repository root (e.g., 'src/utils')",
        example="src/utils",
    )
    name: str = Field(
        description="Filename (e.g., 'scanner.py')",
        example="scanner.py",
    )
    extension: str | None = Field(
        default=None,
        description="File extension in lowercase (e.g., '.py', '.js')",
        examples=[".py", ".js", ".md", ".txt", ".log"],
    )
    category: str | None = Field(
        default=None,
        description="File category (e.g., 'code', 'config', 'docs')",
        examples=["code", "config", "docs"],
    )
    language: str | None = Field(
        default=None,
        description="Programming language detected (e.g., 'python', 'javascript')",
        examples=["python", "javascript"],
    )
    technologies: list[str] = Field(
        default_factory=list,
        description="List of technologies detected (e.g., ['docker', 'kubernetes'])",
        examples=["docker", "kubernetes", "terraform", "ansible"],
    )
    data_type: str | None = Field(
        default=None,
        description="Data file type (e.g., 'csv', 'jsonl', 'xml', 'tsv', 'parquet', 'sqlite')",
        examples=["csv", "jsonl", "xml", "tsv", "parquet", "sqlite"],
    )
    dependency_kind: str | None = Field(
        default=None,
        description="Dependency management system type (e.g., 'python-requirements', 'node-package')",
        examples=["python-requirements", "node-package"],
    )
    size_bytes: int = Field(
        description="File size in bytes",
        example=1024,
    )
    is_binary: bool = Field(
        description="Boolean, True if the file is binary, False otherwise",
        example=False,
    )


class ScanResponse(BaseModel):
    """Response model containing scan results for a repository."""

    repo_root: str = Field(
        description="Absolute (recommended) or relative (if relative path is provided) path to the root of the scanned repository",
        examples=["/path/to/repository", "../../relative/path/to/repository", "C:\\absolute\\path\\to\\sample_repo"],
    )
    scanned_count: int = Field(
        description="Number of files successfully scanned",
        example=150,
    )
    skipped_count: int = Field(
        description="Number of files that were not scanned due to being binary or excluded.",
        example=5,
    )


class SummaryParams(BaseModel):
    """Parameters for repository summary scan request."""
    
    repo_root: str = Field(
        default=".",
        description="Path to the repository root directory to scan",
        examples=[".", "/path/to/repository","../../relative/path/to/repository", "C:\\absolute\\path\\to\\sample_repo"],
    )
    output_dir: str = Field(
        default="output",
        description="Directory relative to repo_root where the summary JSON file will be written",
        examples=["output", "../../relative/path/to/output", "C:\\absolute\\path\\to\\sample_repo\\output"],
    )
    output_file: str | None = Field(
        default=None,
        description="Optional filename for the summary JSON file. If not provided, a default name will be generated based on repository name and timestamp",
        example="sample_repo_YYYYmmdd_HHMMSS.summary.txt",
    )


class SummaryResponse(BaseModel):
    """Response model containing summary results for a repository."""
    
    status: Literal["success", "error"] = Field(
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

    files_by_language: dict[str, int] = Field(
        default_factory=dict,
        description="Number of files grouped by programming language",
        example={"python": 50, "javascript": 30},
    )
    files_by_category: dict[str, int] = Field(
        default_factory=dict,
        description="Number of files grouped by category (code, config, docs, etc.)",
        example={"code": 80, "config": 10, "docs": 5},
    )
    files_by_technology: dict[str, int] = Field(
        default_factory=dict,
        description="Number of files grouped by technology (Docker, Kubernetes, etc.)",
        example={"Docker": 3, "Kubernetes": 2},
    )
    files_by_dependency: dict[str, int] = Field(
        default_factory=dict,
        description="Number of files grouped by dependency management system",
        example={"python-requirements": 1, "node-package": 1},
    )
    files_by_extension: dict[str, int] = Field(
        default_factory=dict,
        description="Number of files grouped by file extension",
        example={".py": 50, ".js": 30, ".md": 5},
    )
    binary_files_by_extension: dict[str, int] = Field(
        default_factory=dict,
        description="Number of binary files grouped by file extension",
        example={".png": 10, ".jpg": 5, ".pdf": 2},
    )
    files_without_extension: int = Field(
        default=0,
        description="Number of files without a file extension",
        example=3,
    )
    files_with_extension: int = Field(
        default=0,
        description="Number of files with a file extension",
        example=147,
    )
    data_files_by_extension: dict[str, int] = Field(
        default_factory=dict,
        description="Number of data files grouped by extension (csv, jsonl, xml, etc.)",
        example={"csv": 5, "jsonl": 2},
    )
    total_files: int = Field(
        default=0,
        description="Total number of files in the repository",
        example=150,
    )
    scanned_files: int = Field(
        default=0,
        description="Number of files successfully scanned",
        example=145,
    )
    skipped_files: int = Field(
        default=0,
        description="Number of files skipped during scanning",
        example=5,
    )

