"""Repository scanning and analysis module.

This module provides functionality to scan repositories, detect file types,
languages, technologies, and categories, and generate summaries of repository
contents. It includes utilities for walking repository directories, identifying
file characteristics, and generating structured summaries.
"""
from __future__ import annotations

import json
import os
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from pydantic import ValidationError

from gcrs.constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_MARKDOWN, OutputFormat
from gcrs.logger import setup_logging
from gcrs.models import FileRecord, RepositorySummary, ScanResponse, SummaryResponse

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


def walk_the_repo(repo_root: Path) -> Iterable[Path]:
    """Walk the repository and yield all files that are not in the skip directories.

    Args:
        repo_root: Path to the root of the repository.

    Yields:
        Path objects for all files in the repository.
    """
    logger.debug("walk_the_repo() is walking the repository starting at repo_root: %s", repo_root)
    try:
        for dirpath, subdirectories, filenames in os.walk(repo_root):
            subdirectories[:] = [
                d for d in subdirectories if d not in SKIP_DIRS
            ]  # TODO: skip what's in .gitignore
            for fname in filenames:
                yield Path(dirpath) / fname
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

def write_summary_to_file(
    summary: RepositorySummary,
    output_file: Path,
    output_file_format: OutputFormat = OUTPUT_FORMAT_MARKDOWN,
) -> None:
    """Write the summary to a file.

    Args:
        summary: RepositorySummary object containing repository statistics.
        output_file: Path to the output file where the summary will be written.
        output_file_format: Format of the output file, either "json", "markdown", or "csv".
            Defaults to "markdown".

    Raises:
        ValueError: If output_file_format is not "json", "markdown", or "csv".
    """
    logger.debug("write_summary_to_file(): writing summary to file: %s", output_file)
    with open(output_file, "w", encoding="utf-8") as f:
        json_data = summary.model_dump_json(indent=2)
        if output_file_format == OUTPUT_FORMAT_JSON:
            f.write(json_data)
        elif output_file_format == OUTPUT_FORMAT_MARKDOWN:
            f.write(format_summary_as_markdown(summary))
        else:
            raise ValueError(f"Invalid output file format: {output_file_format}")
    logger.debug("write_summary_to_file(): finished writing summary to file: %s", output_file.name)


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


def write_file_records_to_file(
    file_records: list[FileRecord],
    output_file: Path,
    output_file_format: OutputFormat = OUTPUT_FORMAT_MARKDOWN,
) -> None:
    """Write the file records to a file.

    Args:
        file_records: List of FileRecord objects to write.
        output_file: Path to the output file where the file records will be written.
        output_file_format: Format of the output file, either "json", "markdown", or "csv".

    Raises:
        ValueError: If output_file_format is not "json", "markdown", or "csv".
    """
    logger.debug("write_file_records_to_file(): writing file records to file: %s", output_file)
    with open(output_file, "w", encoding="utf-8") as f:
        if output_file_format == OUTPUT_FORMAT_JSON:
            file_records = [record.model_dump() for record in file_records]
            json_data = json.dumps(file_records, indent=2)
            f.write(json_data)
        elif output_file_format == OUTPUT_FORMAT_MARKDOWN:
            f.write(format_file_records_as_markdown(file_records))
        else:
            raise ValueError(f"Invalid output file format: {output_file_format}")
    logger.debug("write_file_records_to_file(): finished writing file records to file: %s", output_file.name)


######## HELPER METHODS ########

def do_the_repo_scan(repo_root: Path) -> tuple[list[FileRecord], RepositorySummary]:
    """Scan the repository and return a list of file records and a summary of the repository contents.

    Args:
        repo_root: Path to the root of the repository.

    Returns:
        A tuple containing a list of FileRecord objects for all files in the repository and a summary of the repository contents.
    """
    logger.debug("do_the_repo_scan(): start")
    file_records: list[FileRecord] = []
    filenames = walk_the_repo(repo_root)
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
            is_binary=is_binary
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
    output_file: Path,
    output_file_format: OutputFormat = OUTPUT_FORMAT_MARKDOWN,
) -> ScanResponse:
    """Scan the repo, write file information to the output file.

    Scans the repository, writes file information to the output file.
    """
    logger.debug("scan_repository(): start")
    try:
        file_records, summary = do_the_repo_scan(repo_root)
        write_file_records_to_file(file_records=file_records, output_file=output_file, output_file_format=output_file_format)
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
    output_file: Path,
    output_file_format: OutputFormat = OUTPUT_FORMAT_MARKDOWN,
) -> SummaryResponse:
    """Summarize the contents of the repository.

    Scans the repository, generates a summary of its contents, and writes the
    summary to the specified output file.

    Args:
        repo_root: Path to the root of the repository to scan.
        output_file: Path to the output file where the summary will be written.
        output_file_format: Format of the output file, either "json", "markdown", or "csv".
            Defaults to "markdown".

    Returns:
        A SummaryResponse object containing the repository summary and scan status.
    """
    logger.debug("summarize_repo_contents(): start")

    try:
        _, summary = do_the_repo_scan(repo_root)
        write_summary_to_file(summary=summary, output_file=output_file, output_file_format=output_file_format)
    except (OSError, ValueError, ValidationError) as e:
        logger.error("summarize_repo_contents(): error summarizing repository or writing file: %s", e)
        return SummaryResponse(
            status="error",
            error=str(e),
            repository_summary=None,
        )
    return SummaryResponse(
        status="success",
        repository_summary=summary,
    )
