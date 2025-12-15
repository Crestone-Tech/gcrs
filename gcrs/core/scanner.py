"""Repository scanning and analysis module.

This module provides functionality to scan repositories, detect file types,
languages, technologies, and categories, and generate summaries of repository
contents. It includes utilities for walking repository directories, identifying
file characteristics, and generating structured summaries.
"""
from __future__ import annotations

import json
import os
import subprocess
from collections import Counter
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from pathspec import GitIgnoreSpec
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sarif_pydantic import (
    ArtifactLocation,
    Level,
    Location,
    Message,
    PhysicalLocation,
    Result,
    Run,
    Sarif,
    Tool,
    ToolDriver,
)

from gcrs.constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_MARKDOWN, OUTPUT_FORMAT_SARIF, OUTPUT_FORMAT_CSV, OutputFormat
from gcrs.models import ScanParams
from gcrs.logger import setup_logging
from gcrs.models import FileRecord, RepositorySummary, ScanResponse, SummaryResponse

from gcrs.db import *

logger = setup_logging(log_level="DEBUG")

# Directories to skip during repository scanning
SKIP_DIRS = frozenset({
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    "out",
    "tmp",
    ".pytest_cache",
    ".mypy_cache",
    ".vscode",
    ".DS_Store",
    "output",
})

# Binary file extensions
BINARY_EXTENSIONS = frozenset({
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".ico",
    ".webp",
    ".svg",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".rar",
    ".7z",
    ".pdf",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
    ".mp4",
    ".mov",
    ".avi",
})

# Data file extensions mapped to their types
DATA_TYPES_BY_EXTENSION = {
    ".csv": "csv",
    ".jsonl": "jsonl",
    ".xml": "xml",
    ".tsv": "tsv",
    ".parquet": "parquet",
    ".sqlite": "sqlite",
    ".db": "db",
    ".ndjson": "ndjson",
}

# File extensions mapped to programming languages
LANGUAGE_BY_EXT = {
    ".c": "c",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".css": "css",
    ".go": "go",
    ".h": "c-header",
    ".hpp": "cpp-header",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".jsx": "javascript",
    ".kt": "kotlin",
    ".m": "objective-c",
    ".md": "markdown",
    ".mm": "objective-c++",
    ".php": "php",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".sass": "sass",
    ".scala": "scala",
    ".scss": "scss",
    ".sql": "sql",
    ".swift": "swift",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".vb": "vb",
}

# Dependency files mapped to their kind
DEPENDENCY_KIND_BY_NAME = {
    "requirements.txt": "python-requirements",
    "pyproject.toml": "python-pyproject",
    "Pipfile": "python-pipenv",
    "Pipfile.lock": "python-pipenv-lock",
    "poetry.lock": "python-poetry-lock",
    "package.json": "node-package",
    "package-lock.json": "node-lock",
    "pnpm-lock.yaml": "node-pnpm-lock",
    "yarn.lock": "node-yarn-lock",
    "go.mod": "go-mod",
    "go.sum": "go-sum",
    "pom.xml": "maven-pom",
    "Gemfile": "ruby-gemfile",
    "Gemfile.lock": "ruby-gem-lock",
    "Cargo.toml": "rust-cargo",
    "Cargo.lock": "rust-cargo-lock",
}

# Map dependency kinds to technologies (extract technology from dependency_kind value)
DEPENDENCY_TO_TECHNOLOGY = {
    "python-requirements": "Python",
    "python-pyproject": "Python",
    "python-pipenv": "Python",
    "python-pipenv-lock": "Python",
    "python-poetry-lock": "Python",
    "node-package": "Node.js",
    "node-lock": "Node.js",
    "node-pnpm-lock": "Node.js",
    "node-yarn-lock": "Node.js",
    "go-mod": "Go",
    "go-sum": "Go",
    "maven-pom": "Maven",
    "ruby-gemfile": "Ruby",
    "ruby-gem-lock": "Ruby",
    "rust-cargo": "Rust",
    "rust-cargo-lock": "Rust",
}

# Build technology patterns from dependency files
TECHNOLOGY_FROM_DEPENDENCIES = {
    filename: DEPENDENCY_TO_TECHNOLOGY[kind]
    for filename, kind in DEPENDENCY_KIND_BY_NAME.items()
    if kind in DEPENDENCY_TO_TECHNOLOGY
}

TECHNOLOGY_PATTERNS = {
    # Infrastructure and tools
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker",
    "docker-compose.yaml": "Docker",
    "docker-compose.override.yml": "Docker",
    "docker-compose.override.yaml": "Docker",
    "k8s": "Kubernetes",
    ".tf": "Terraform",
    "ansible": "Ansible",
    "ansible.cfg": "Ansible",
    "build.gradle": "Gradle",
    "setup.cfg": "Python",
    "tox.ini": "Python",
    "pytest.ini": "Python",
    # Include technology mappings from dependency files
    **TECHNOLOGY_FROM_DEPENDENCIES,
}

# File extensions mapped to their category
CATEGORY_BY_EXT = {
    # code
    **dict.fromkeys(LANGUAGE_BY_EXT, "code"),
    # config
    ".yml": "config",
    ".yaml": "config",
    ".json": "config",
    ".toml": "config",
    ".ini": "config",
    ".cfg": "config",
    ".conf": "config",
    # docs
    ".md": "documentation",
    ".rst": "documentation",
    ".txt": "documentation",
    ".adoc": "documentation",
    # scripts
    ".sh": "script",
    ".ps1": "script",
    ".bat": "script",
    ".cmd": "script",
    # infrastructure
    ".tf": "infrastructure",
    ".dockerfile": "infrastructure",
    # data
    **dict.fromkeys(DATA_TYPES_BY_EXTENSION, "data"),
    # assets (fallback: binary handled via is_binary_ext)
    ".svg": "asset",
}

# CI/CD filenames (no extension or special names)
CI_FILENAMES = {"Jenkinsfile", ".gitlab-ci.yml", "azure-pipelines.yml"}
CI_DIR_HINTS = {".github/workflows", ".circleci"}

def is_binary_ext(ext: str) -> bool:
    """Check if a file extension is in the list of binary extensions.

    Args:
        ext: File extension to check.

    Returns:
        True if the extension is in the list of binary extensions, False otherwise.
    """
    return ext in BINARY_EXTENSIONS


def is_data_ext(ext: str) -> bool:
    """Check if a file extension is in the list of data extensions.

    Args:
        ext: File extension to check.

    Returns:
        True if the extension is in the list of data extensions, False otherwise.
    """
    return ext in DATA_TYPES_BY_EXTENSION


def walk_the_repo(repo_root: Path, skip_dirs: list[str] = [], respect_gitignore: bool = True) -> Iterable[Path]:
    """Walk the repository and yield all files that are not in the skip directories.

    Args:
        repo_root: Path to the root of the repository.
        skip_dirs: List of directories to skip.
        respect_gitignore: Whether to respect .gitignore files.
    Yields:
        Path objects for all files in the repository.
    """
    logger.debug("walk_the_repo() is walking the repository starting at repo_root: %s", repo_root)
    try:
        merged_skip_dirs = SKIP_DIRS.union(frozenset(skip_dirs))   # convert the list to a set and merge it with the default skip directories
        logger.debug("walk_the_repo() merged_skip_dirs: %s", merged_skip_dirs)
        
        # Build gitignore spec if needed
        gitignore_spec = None
        if respect_gitignore:
            gitignore_path = repo_root / ".gitignore"
            if gitignore_path.exists() and gitignore_path.is_file():
                try:
                    with open(gitignore_path, "r", encoding="utf-8") as f:
                        gitignore_lines = f.readlines()
                    gitignore_spec = GitIgnoreSpec.from_lines(gitignore_lines)
                    logger.debug("walk_the_repo() loaded .gitignore from: %s", gitignore_path)
                except (OSError, IOError) as e:
                    logger.warning("walk_the_repo() failed to read .gitignore file: %s", e)
            else:
                logger.debug("walk_the_repo() no .gitignore file found at: %s", gitignore_path)
        
        for dirpath, subdirectories, filenames in os.walk(repo_root):
            dirpath_path = Path(dirpath)
            
            # Filter subdirectories by skip_dirs and gitignore
            filtered_subdirs = []
            for d in subdirectories:
                # Skip if in skip_dirs
                if d in merged_skip_dirs:
                    continue
                
                # Skip if matches gitignore pattern
                if gitignore_spec:
                    # Check if directory matches gitignore (relative to repo_root)
                    rel_dir_path = (dirpath_path / d).relative_to(repo_root)
                    if gitignore_spec.match_file(str(rel_dir_path)):
                        continue
                
                filtered_subdirs.append(d)
            
            subdirectories[:] = filtered_subdirs
            
            # Yield files that are not skipped
            for fname in filenames:
                file_path = dirpath_path / fname
                
                # Skip if matches gitignore pattern
                if gitignore_spec:
                    rel_file_path = file_path.relative_to(repo_root)
                    if gitignore_spec.match_file(str(rel_file_path)):
                        continue
                
                yield file_path
        
    except OSError as e:
        logger.error("walk_the_repo() error walking the repository: %s", e)
        raise # re-raise the exception to be handled by the caller
    logger.debug("walk_the_repo() is finished walking the repository")

def format_summary_as_markdown(summary: RepositorySummary) -> str:
    """Format the summary as markdown.

    Args:
        summary: RepositorySummary object containing repository statistics.

    Returns:
        A markdown-formatted string representation of the repository summary.
    """
    markdown_lines = []
    markdown_lines.append(f"# Repository Summary")
    markdown_lines.append(f"## Total Files: {summary.total_files}")
    markdown_lines.append(f"## Scanned Files: {summary.scanned_files}")
    markdown_lines.append(f"## Skipped Files: {summary.skipped_files}")
    markdown_lines.append(f"## Files without Extension: {summary.files_without_extension}")
    markdown_lines.append(f"## Files with Extension: {summary.files_with_extension}")
    markdown_lines.append(f"## Files by Language:")
    for language, count in summary.files_by_language.items():
        markdown_lines.append(f"  - {language}: {count}")
    markdown_lines.append(f"## Files by Category:")
    for category, count in summary.files_by_category.items():
        markdown_lines.append(f"  - {category}: {count}")
    markdown_lines.append(f"## Files by Technology:")
    for technology, count in summary.files_by_technology.items():
        markdown_lines.append(f"  - {technology}: {count}")
    markdown_lines.append(f"## Files by Dependency:")
    for dependency, count in summary.files_by_dependency.items():
        markdown_lines.append(f"  - {dependency}: {count}")
    markdown_lines.append(f"## Files by Extension:")
    for extension, count in summary.files_by_extension.items():
        markdown_lines.append(f"  - {extension}: {count}")
    markdown_lines.append(f"## Binary Files by Extension:")
    for extension, count in summary.binary_files_by_extension.items():
        markdown_lines.append(f"  - {extension}: {count}")

    return "\n".join(markdown_lines)


def format_summary_as_json(summary: RepositorySummary) -> str:
    """Format the summary as JSON.

    Args:
        summary: RepositorySummary object containing repository statistics.

    Returns:
        A JSON-formatted string representation of the repository summary.
    """
    return summary.model_dump_json(indent=2)


def format_summary_as_csv(summary: RepositorySummary) -> str:
    """Format the summary as CSV.

    Args:
        summary: RepositorySummary object containing repository statistics.

    Returns:
        A CSV-formatted string representation of the repository summary.
    """
    csv_lines = []
    csv_lines.append("Metric,Value")
    csv_lines.append(f"Total Files,{summary.total_files}")
    csv_lines.append(f"Scanned Files,{summary.scanned_files}")
    csv_lines.append(f"Skipped Files,{summary.skipped_files}")
    csv_lines.append(f"Files without Extension,{summary.files_without_extension}")
    csv_lines.append(f"Files with Extension,{summary.files_with_extension}")
    
    csv_lines.append("")
    csv_lines.append("Language,Count")
    for language, count in summary.files_by_language.items():
        csv_lines.append(f"{language},{count}")
    
    csv_lines.append("")
    csv_lines.append("Category,Count")
    for category, count in summary.files_by_category.items():
        csv_lines.append(f"{category},{count}")
    
    csv_lines.append("")
    csv_lines.append("Technology,Count")
    for technology, count in summary.files_by_technology.items():
        csv_lines.append(f"{technology},{count}")
    
    csv_lines.append("")
    csv_lines.append("Dependency,Count")
    for dependency, count in summary.files_by_dependency.items():
        csv_lines.append(f"{dependency},{count}")
    
    csv_lines.append("")
    csv_lines.append("Extension,Count")
    for extension, count in summary.files_by_extension.items():
        csv_lines.append(f"{extension},{count}")
    
    csv_lines.append("")
    csv_lines.append("Binary Extension,Count")
    for extension, count in summary.binary_files_by_extension.items():
        csv_lines.append(f"{extension},{count}")
    
    return "\n".join(csv_lines)


def format_summary(summary: RepositorySummary, output_format: OutputFormat) -> str:
    """Format the summary in the specified format.

    Args:
        summary: RepositorySummary object containing repository statistics.
        output_format: Format to use ("json", "markdown", or "csv").

    Returns:
        A formatted string representation of the repository summary.

    Raises:
        ValueError: If output_format is not supported.
    """
    if output_format == OUTPUT_FORMAT_JSON:
        return format_summary_as_json(summary)
    elif output_format == OUTPUT_FORMAT_MARKDOWN:
        return format_summary_as_markdown(summary)
    elif output_format == OUTPUT_FORMAT_CSV:
        return format_summary_as_csv(summary)
    else:
        raise ValueError(f"Invalid output format: {output_format}")


def format_file_records(file_records: list[FileRecord], output_format: OutputFormat) -> str:
    """Format the file records in the specified format.

    Args:
        file_records: List of FileRecord objects to format.
        output_format: Format to use ("json", "markdown", "csv", or "sarif").

    Returns:
        A formatted string representation of the file records.

    Raises:
        ValueError: If output_format is not supported.
    """
    if output_format == OUTPUT_FORMAT_JSON:
        file_records_dict = [record.model_dump(mode='json') for record in file_records]
        return json.dumps(file_records_dict, indent=2)
    elif output_format == OUTPUT_FORMAT_MARKDOWN:
        return format_file_records_as_markdown(file_records)
    elif output_format == OUTPUT_FORMAT_SARIF:
        return format_file_records_as_sarif(file_records)
    elif output_format == OUTPUT_FORMAT_CSV:
        return format_file_records_as_csv(file_records)
    else:
        raise ValueError(f"Invalid output format: {output_format}")

def write_summary_to_file(
    summary: RepositorySummary,
    output_file: Path | None = None,
    output_file_format: OutputFormat = OUTPUT_FORMAT_MARKDOWN,
    output_stream: object | None = None,
) -> None:
    """Write the summary to a file or stream.

    Args:
        summary: RepositorySummary object containing repository statistics.
        output_file: Path to the output file where the summary will be written.
            If None and output_stream is provided, writes to the stream instead.
        output_file_format: Format of the output file, either "json", "markdown", or "csv".
            Defaults to "markdown".
        output_stream: Optional file-like object to write to (e.g., sys.stdout).
            If provided, output_file is ignored.

    Raises:
        ValueError: If output_file_format is not "json", "markdown", or "csv", or if
            neither output_file nor output_stream is provided.
    """
    formatted_output = format_summary(summary, output_file_format)
    
    if output_stream is not None:
        logger.debug("write_summary_to_file(): writing summary to stream")
        output_stream.write(formatted_output)
        if hasattr(output_stream, 'flush'):
            output_stream.flush()
    elif output_file is not None:
        logger.debug("write_summary_to_file(): writing summary to file: %s", output_file)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(formatted_output)
        logger.debug("write_summary_to_file(): finished writing summary to file: %s", output_file.name)
    else:
        raise ValueError("Either output_file or output_stream must be provided")


def escape_markdown_table_cells(cell: str) -> str:
    """Escape markdown table cells.

    Args:
        cell: Cell to escape.

    Returns:
        An escaped markdown table cell.
    """
    translation_table = str.maketrans({
        "|": "\\|",
        "*": "\\*",
        "_": "\\_",
        "~": "\\~",
        "`": "\\`",
        "^": "\\^",
        "$": "\\$",
        "#": "\\#",
        "&": "\\&",
    })
    return cell.translate(translation_table)


def format_file_records_as_markdown(file_records: list[FileRecord]) -> str:
    """Format the file records as markdown.

    Args:
        file_records: List of FileRecord objects to format.

    Returns:
        A markdown-formatted string representation of the file records.
    """
    markdown_lines = []
    markdown_lines.append("# File Records")
    markdown_lines.append(f"## Total Files: {len(file_records)}")
    markdown_lines.append("## Files:")
    markdown_lines.append("")
    markdown_lines.append(
        "| Name | Extension | Relative Dir | Language | Category | Data Type | "
        "Dependency Kind | Size (bytes) | Binary |"
    )
    markdown_lines.append(
        "|------|-----------|--------------|----------|----------|--------------|"
        "-----------------|--------------|--------|"
    )
    for file_record in file_records:
        markdown_lines.append(
            f"| {escape_markdown_table_cells(file_record.name)} "
            f"| {file_record.extension or ''} "
            f"| {escape_markdown_table_cells(file_record.relative_dir)} "
            f"| {file_record.language or ''} "
            f"| {file_record.category or ''} "
            f"| {file_record.data_type or ''} "
            f"| {file_record.dependency_kind or ''} "
            f"| {file_record.size_bytes} "
            f"| {file_record.is_binary} |"
        )
    return "\n".join(markdown_lines)

def format_file_records_as_sarif(file_records: list[FileRecord]) -> str:
    """Format the file records as SARIF 2.1.0 format using sarif-pydantic.

    Args:
        file_records: List of FileRecord objects to format.

    Returns:
        A SARIF-formatted JSON string representation of the file records.
    """
    # Create tool driver
    tool_driver = ToolDriver(
        name="GCRS",
    )
    
    # Create tool with the driver
    tool = Tool(driver=tool_driver)
    
    # Convert each FileRecord to a SARIF result
    results = []
    for record in file_records:
        # Determine ruleId (use category, fallback to "file")
        rule_id = record.category if record.category else "file"
        
        # Build message text with key metadata
        message_parts = [f"File: {record.name}"]
        if record.language:
            message_parts.append(f"Language: {record.language}")
        if record.category:
            message_parts.append(f"Category: {record.category}")
        if record.size_bytes:
            message_parts.append(f"Size: {record.size_bytes} bytes")
        message_text = " | ".join(message_parts)
        
        # Convert absolute filename to URI format (forward slashes)
        file_uri = record.absolute_filename.replace("\\", "/")
        
        # Build properties with all metadata
        properties = {}
        if record.most_recent_commit_hash:
            properties["gitCommit"] = record.most_recent_commit_hash
        if record.most_recent_commit_date:
            # Format datetime as ISO 8601 string
            properties["gitDate"] = record.most_recent_commit_date.isoformat()
        if record.language:
            properties["language"] = record.language
        if record.category:
            properties["category"] = record.category
        if record.extension:
            properties["extension"] = record.extension
        properties["sizeBytes"] = record.size_bytes
        properties["isBinary"] = record.is_binary
        if record.technologies:
            properties["technologies"] = record.technologies
        if record.dependency_kind:
            properties["dependencyKind"] = record.dependency_kind
        if record.data_type:
            properties["dataType"] = record.data_type
        
        # Create physical location
        physical_location = PhysicalLocation(
            artifact_location=ArtifactLocation(
                uri=file_uri,
            ),
        )
        
        # Create location
        location = Location(
            physical_location=physical_location,
        )
        
        # Create SARIF result
        # Build result data with properties if available
        # Use model_validate to allow properties field
        result_dict = {
            "ruleId": rule_id,
            "level": Level.NOTE,
            "message": {"text": message_text},
            "locations": [location.model_dump()],
        }
        if properties:
            result_dict["properties"] = properties
        
        result = Result.model_validate(result_dict)
        
        results.append(result)
    
    # Create SARIF log
    sarif_log = Sarif(
        version="2.1.0",
        runs=[Run(
            tool=tool,
            results=results,
        )],
    )
    
    # Export to JSON string with indentation
    return sarif_log.model_dump_json(indent=2, exclude_none=True)

def format_file_records_as_csv(file_records: list[FileRecord]) -> str:
    """Format the file records as CSV.

    Args:
        file_records: List of FileRecord objects to format.

    Returns:
        A CSV-formatted string representation of the file records.
    """
    csv_lines = []
    csv_lines.append("Name,Extension,Relative Dir,Language,Category,Data Type,Dependency Kind,Size (bytes),Binary")
    for file_record in file_records:
        csv_lines.append(f"{file_record.name},{file_record.extension or ''},{file_record.relative_dir or ''},{file_record.language or ''},{file_record.category or ''},{file_record.data_type or ''},{file_record.dependency_kind or ''},{file_record.size_bytes},{file_record.is_binary}")
    return "\n".join(csv_lines)

def write_file_records_to_file(
    file_records: list[FileRecord],
    output_file: Path | None = None,
    output_file_format: OutputFormat = OUTPUT_FORMAT_MARKDOWN,
    output_stream: object | None = None,
) -> None:
    """Write the file records to a file or stream.

    Args:
        file_records: List of FileRecord objects to write.
        output_file: Path to the output file where the file records will be written.
            If None and output_stream is provided, writes to the stream instead.
        output_file_format: Format of the output file, either "json", "markdown", "csv", or "sarif".
        output_stream: Optional file-like object to write to (e.g., sys.stdout).
            If provided, output_file is ignored.

    Raises:
        ValueError: If output_file_format is anything other than "json", "markdown", "csv", or "sarif", or if
            neither output_file nor output_stream is provided.
    """
    formatted_output = format_file_records(file_records, output_file_format)
    
    if output_stream is not None:
        logger.debug("write_file_records_to_file(): writing file records to stream")
        output_stream.write(formatted_output)
        if hasattr(output_stream, 'flush'):
            output_stream.flush()
    elif output_file is not None:
        logger.debug("write_file_records_to_file(): writing file records to file: %s", output_file)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(formatted_output)
        logger.debug("write_file_records_to_file(): finished writing file records to file: %s", output_file.name)
    else:
        raise ValueError("Either output_file or output_stream must be provided")


######## HELPER METHODS ########

def get_git_commit_info(file_path: Path, repo_root: Path) -> tuple[datetime | None, str | None]:
    """Get the most recent commit date and hash for a file from Git.
    
    Args:
        file_path: Absolute path to the file.
        repo_root: Root of the Git repository.
        
    Returns:
        A tuple of (commit_date, commit_hash). Both are None if Git is not available,
        the file is not tracked, or an error occurs.
    """
    try:
        # Get relative path from repo root
        try:
            rel_path = file_path.relative_to(repo_root)
        except ValueError:
            # File is not under repo_root
            return None, None
        
        # Check if we're in a Git repository
        git_dir = repo_root / ".git"
        if not git_dir.exists():
            return None, None
        
        # Run git log to get the most recent commit
        # Format: %H (full hash) %ai (author date, ISO 8601-like format)
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H %ai", "--", str(rel_path)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=1,  # Timeout after 1 second (should complete in milliseconds)
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            # File is not tracked in Git or has no commits
            return None, None
        
        # Parse output: "hash YYYY-MM-DD HH:MM:SS +TZ"
        parts = result.stdout.strip().split(" ", 2)
        if len(parts) < 2:
            return None, None
        
        commit_hash = parts[0]
        # Parse datetime (format: "2025-01-01 12:00:00 +0000")
        try:
            # Remove timezone info for parsing (we'll keep it as naive datetime)
            date_str = " ".join(parts[1:])
            # Remove timezone offset if present
            if "+" in date_str or date_str.count("-") > 2:
                date_str = date_str.rsplit(" ", 1)[0]
            commit_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.warning("get_git_commit_info() failed to parse date: %s", date_str)
            return None, None
        
        return commit_date, commit_hash
        
    except subprocess.TimeoutExpired:
        logger.warning("get_git_commit_info() timeout getting commit info for: %s", file_path)
        return None, None
    except FileNotFoundError:
        # Git is not installed
        logger.debug("get_git_commit_info() Git not found")
        return None, None
    except Exception as e:
        logger.warning("get_git_commit_info() error getting commit info for %s: %s", file_path, e)
        return None, None

# def get_or_create_repo_in_db(session: Session, repo_root: Path) -> Repo:
#     """Get or create a repository record.
    
#     Args:
#         session: Session object
#         repo_root: Path to the root of the repository.
    
#     Returns:
#         A Repo object.
#     """
#     uri = str(repo_root.resolve())
#     git_owner_account = "unknown"
#     repo = get_or_create_repo(session,uri=uri, git_owner_account=git_owner_account)
#     return repo

# def get_or_create_file_in_db(session: Session, repo_id: int, file_path: str) -> File:
#     """Get or create a file record.
    
#     Args:
#         session: Session object
#         repo_id: Repository ID
#         file_path: Path to the file relative to the repository root.
    
#     Returns:
#         A File object.
#     """

#     file = get_or_create_file(session,repo_id=repo_id, file_path=file_path)
#     return file

def do_the_repo_scan(repo_root: Path, skip_dirs: list[str] = [], persist_to_db: bool = True, respect_gitignore: bool = True) -> tuple[list[FileRecord], RepositorySummary]:
    """Scan the repository and return a list of file records and a summary of the repository contents.

    Args:
        repo_root: Path to the root of the repository (must be a git repository).

    Returns:
        A tuple containing a list of FileRecord objects for all files in the repository and a summary of the repository contents.
    
    Raises:
        ValueError: If the directory is not a git repository.
    """
    logger.debug("do_the_repo_scan(): start")
    logger.debug("do_the_repo_scan() respect_gitignore param: %s", respect_gitignore)
    
    # Validate that this is a git repository
    git_dir = repo_root / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        raise ValueError(
            f"Directory is not a git repository: {repo_root}. "
            "Only git repositories are supported."
        )

    file_records: list[FileRecord] = []
    filenames = walk_the_repo(repo_root, skip_dirs, respect_gitignore)
    
    
    total_files = 0
    files_without_extension = 0
    files_with_extension = 0

    # Use Counter objects for efficient counting during accumulation
    files_by_language_counter = Counter()
    files_by_category_counter = Counter()
    files_by_extension_counter = Counter()
    binary_files_by_extension_counter = Counter()
    files_by_dependency_counter = Counter()
    data_files_by_extension_counter = Counter()
    files_by_technology_counter = Counter()

    # Scan files and collect file records (no database access needed here)
    for filename in filenames:
        total_files += 1
        relative_dir = filename.relative_to(repo_root).as_posix()
        absolute_filename = str(filename.absolute())
        name = filename.name
        extension = filename.suffix.lower()
        language = LANGUAGE_BY_EXT.get(extension, None)
        category = CATEGORY_BY_EXT.get(extension, None)
        data_type = DATA_TYPES_BY_EXTENSION.get(extension, None)
        technology = TECHNOLOGY_PATTERNS.get(name.lower(), None)
        dependency_kind = DEPENDENCY_KIND_BY_NAME.get(name, None)
        size_bytes = filename.stat().st_size
        is_binary = is_binary_ext(extension)
    
        # Get Git commit information
        commit_date, commit_hash = get_git_commit_info(filename, repo_root)
        
        new_file_record = FileRecord(
            relative_dir=relative_dir,
            absolute_filename=absolute_filename,
            name=name,
            extension=extension,
            category=category,
            language=language,
            data_type=data_type,
            # technologies=technology,  # TODO: add technologies to the file record
            dependency_kind=dependency_kind,
            size_bytes=size_bytes,
            is_binary=is_binary,
            most_recent_commit_date=commit_date,
            most_recent_commit_hash=commit_hash,
        )
        file_records.append(new_file_record)

        # Use Counter's efficient += operator (handles missing keys automatically)
        if language:
            files_by_language_counter[language] += 1
        if category:
            files_by_category_counter[category] += 1
        if not extension:
            files_without_extension += 1
        else:
            files_with_extension += 1
            files_by_extension_counter[extension] += 1
        if extension and is_binary:
            binary_files_by_extension_counter[extension] += 1
        if dependency_kind:
            files_by_dependency_counter[dependency_kind] += 1
        if data_type:
            data_files_by_extension_counter[data_type] += 1
        if technology:
            files_by_technology_counter[technology] += 1

    if persist_to_db:
        # Persist scan results to database using a single session
        with get_db_session() as session:
            scan_params = ScanParams(
                repo_root=str(repo_root.resolve()),
                output_file_format=OUTPUT_FORMAT_MARKDOWN,
                skip_dirs=skip_dirs,
                respect_gitignore=respect_gitignore,
            )
            persist_scan_results(
                session=session,
                repo_root=repo_root,
                file_records=file_records,
                scan_params=scan_params,
                repo_uri=str(repo_root.resolve()),
                git_owner_account="unknown",
            )
            
    # Convert Counter objects to dicts for Pydantic model (which expects dict[str, int])
    summary = RepositorySummary(
        files_by_language=dict(files_by_language_counter),
        files_by_category=dict(files_by_category_counter),
        data_files_by_extension=dict(data_files_by_extension_counter),
        files_by_technology=dict(files_by_technology_counter),
        files_by_dependency=dict(files_by_dependency_counter),
        files_by_extension=dict(files_by_extension_counter),
        binary_files_by_extension=dict(binary_files_by_extension_counter),
        total_files=total_files,
        files_without_extension=files_without_extension,
        files_with_extension=files_with_extension,
        scanned_files=len(file_records),
        skipped_files=total_files - len(file_records)
    )
    logger.debug("do_the_repo_scan(): end")
    return file_records, summary

######## ENDPOINT METHODS. That's why they are at the bottom of the file. ########
def scan_repository(
    repo_root: Path,
    output_file: Path | None = None,
    output_file_format: OutputFormat = OUTPUT_FORMAT_MARKDOWN,
    persist_to_db: bool = True,
    skip_dirs: list[str] = [],
    respect_gitignore: bool = True,
    output_stream: object | None = None,
) -> ScanResponse:
    """Scan the repo, write file information to the output file or stream.

    Scans the repository, writes file information to the output file or stream.
    Either output_file or output_stream must be provided.

    Args:
        repo_root: Path to the root of the repository.
        output_file: Path to the output file where the scan results will be written.
            If None and output_stream is provided, writes to the stream instead.
        output_file_format: Format of the output file, either "json", "markdown", "csv", or "sarif".
            Defaults to "markdown".
        skip_dirs: List of directories to skip.
        respect_gitignore: Whether to respect .gitignore files.
        output_stream: Optional file-like object to write to (e.g., sys.stdout).
            If provided, output_file is ignored.
    """
    logger.debug("scan_repository(): start")

    try:
        file_records, summary = do_the_repo_scan(repo_root, skip_dirs, persist_to_db, respect_gitignore)
        write_file_records_to_file(
            file_records=file_records,
            output_file=output_file,
            output_file_format=output_file_format,
            output_stream=output_stream,
        )
    except (OSError, ValueError, ValidationError) as e:
        logger.error("scan_repository(): error scanning repository or writing file: %s", e)
        return ScanResponse(
            status="error",
            error=str(e),
        )
    return ScanResponse(
        status="success",
        error=None,
    )


def summarize_repo_contents(
    repo_root: Path,
    output_file: Path | None = None,
    output_file_format: OutputFormat = OUTPUT_FORMAT_MARKDOWN,
    skip_dirs: list[str] = [],
    respect_gitignore: bool = True,
    persist_to_db: bool = True,
    output_stream: object | None = None,
) -> SummaryResponse:
    """Summarize the contents of the repository.

    Scans the repository, generates a summary of its contents, and writes the
    summary to the specified output file or stream. Either output_file or output_stream must be provided.

    Args:
        repo_root: Path to the root of the repository to scan.
        output_file: Path to the output file where the summary will be written.
            If None and output_stream is provided, writes to the stream instead.
        output_file_format: Format of the output file, either "json", "markdown", or "csv".
            Defaults to "markdown".
        skip_dirs: List of directories to skip.
        respect_gitignore: Whether to respect .gitignore files.
        output_stream: Optional file-like object to write to (e.g., sys.stdout).
            If provided, output_file is ignored.
    Returns:
        A SummaryResponse object containing the repository summary and scan status.
    """
    logger.debug("summarize_repo_contents(): start")

    try:
        _, summary = do_the_repo_scan(repo_root, skip_dirs, persist_to_db, respect_gitignore)
        write_summary_to_file(
            summary=summary,
            output_file=output_file,
            output_file_format=output_file_format,
            output_stream=output_stream,
        )
    except (OSError) as e:
        logger.error("summarize_repo_contents(): error writing summary to file: %s", e)
        return SummaryResponse(
            status="error",
            error=str(e),
            repository_summary=None,
        )
    except (ValueError, ValidationError) as e:
        logger.error("summarize_repo_contents(): error generating summary: %s", e)
        return SummaryResponse(
            status="error",
            error=str(e),
            repository_summary=None,
        )
    return SummaryResponse(
        status="success",
        repository_summary=summary,
    )
