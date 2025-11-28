"""Repository scanning and analysis module.

This module provides functionality to scan repositories, detect file types,
languages, technologies, and categories, and generate summaries of repository
contents. It includes utilities for walking repository directories, identifying
file characteristics, and generating structured summaries.
"""
from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from typing import Literal
import json
from gcrs.logger import setup_logging
from gcrs.models import FileRecord, RepositorySummary, SummaryResponse, ScanResponse

logger = setup_logging(log_level="DEBUG")

# ---- list of directories to skip ----
SKIP_DIRS = {
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
}

# ---- list of binary file extensions ----
BINARY_EXTENSIONS = {
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
}

# ---- list of data file extensions ----
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

# ---- map file extensions to their language ----
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

# ---- map dependency files to their kind ----
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

# ---- map file extensions to their category ----
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

# ---- check if a file extension is in the list of binary extensions ----
def is_binary_ext(ext: str) -> bool:
    """Check if a file extension is in the list of binary extensions.

    Args:
        ext: File extension to check.

    Returns:
        True if the extension is in the list of binary extensions, False otherwise.
    """
    return ext in BINARY_EXTENSIONS


# ---- check if a file extension is in the list of data extensions ----
def is_data_ext(ext: str) -> bool:
    """Check if a file extension is in the list of data extensions.

    Args:
        ext: File extension to check.

    Returns:
        True if the extension is in the list of data extensions, False otherwise.
    """
    return ext in DATA_TYPES_BY_EXTENSION


# ---- walk the repository and yield all files that are not in the skip directories ----
def walk_the_repo(repo_root: Path) -> Iterable[str]:
    """Walk the repository and yield all files that are not in the skip directories.

    Args:
        repo_root: Path to the root of the repository.

    Returns:
        An iterable of Path objects for all files in the repository.
    """
    logger.debug("walk_the_repo() is walking the repository starting at repo_root: %s", repo_root)
    for dirpath, subdirectories, filenames in os.walk(repo_root):
        subdirectories[:] = [
            d for d in subdirectories if d not in SKIP_DIRS
        ]  # TODO: skip what's in .gitignore
        for fname in filenames:
            yield Path(dirpath) / fname

    logger.debug("walk_the_repo() is finished walking the repository")

# ---- parse the file records and output a summary of the contents ----
# def parse_summary(file_records: list[FileRecord]) -> str:
#     """Parse the summary of the repository contents.

#     Args:
#         file_records: List of FileRecord objects.

#     Returns:
#         A string summarizing the contents of the repository.
#     """
#     summary_lines = [f"{file_record.relative_dir}/{file_record.name}" for file_record in file_records]
#     return "\n".join(summary_lines)

# ---- format the summary as markdown ----
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
# ---- write the summary to a file ----
def write_summary_to_file(summary: RepositorySummary, output_file_path: Path,
    output_file_format: Literal["json", "markdown"] = "markdown"):
    """Write the summary to a file.

    Args:
        summary: RepositorySummary object containing repository statistics.
        output_file_path: Path to the output file where the summary will be written.
        output_file_format: Format of the output file, either "json" or "markdown".
            Defaults to "markdown".

    Raises:
        ValueError: If output_file_format is not "json" or "markdown".
    """
    logger.debug("write_summary_to_file(): writing summary to file: %s", output_file_path)
    with open(output_file_path, "w", encoding="utf-8") as f:
        # The summary object is a Pydantic model, so you can serialize it to JSON and write it to a file.
        # This uses the Pydantic model's model_dump_json() method to dump as JSON.
        json_str = summary.model_dump_json(indent=2)
        if output_file_format == "json":
            f.write(json_str)
        elif output_file_format == "markdown":
            f.write(format_summary_as_markdown(summary))
        else:
            raise ValueError(f"Invalid output file format: {output_file_format}")
    logger.debug("write_summary_to_file(): finished writing summary to file: %s", output_file_path.name)

# escape markdown table cells
def escape_markdown_table_cells(cell: str) -> str:
    """Escape markdown table cells.

    Args:
        cell: Cell to escape.

    Returns:
        An escaped markdown table cell.
    """
    cell = cell.replace("|", "\\|")
    cell = cell.replace("*", "\\*")
    cell = cell.replace("_", "\\_")
    cell = cell.replace("~", "\\~")
    cell = cell.replace("`", "\\`")
    cell = cell.replace("^", "\\^")
    cell = cell.replace("$", "\\$")
    cell = cell.replace("#", "\\#")
    cell = cell.replace("&", "\\&")
    return cell

# ---- format the file records as markdown ----
def format_file_records_as_markdown(file_records: list[FileRecord]) -> str:
    """Format the file records as markdown.

    Args:
        file_records: List of FileRecord objects to format.

    Returns:
        A markdown-formatted string representation of the file records.
    """
    markdown_lines = []
    markdown_lines.append(f"# File Records")
    markdown_lines.append(f"## Total Files: {len(file_records)}")
    markdown_lines.append(f"## Files:")
    # Write a table header for the file records
    markdown_lines.append("")
    markdown_lines.append("| Name | Extension | Relative Dir | Language | Category | Data Type | Dependency Kind | Size (bytes) | Binary |")
    markdown_lines.append("|------|-----------|--------------|----------|----------|--------------|-----------------|--------------|--------|")
    # Write each file record as a row in the markdown table
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

# ---- write the file records to a file ----
def write_file_records_to_file(file_records: list[FileRecord], output_file_path: Path,
    output_file_format: Literal["json", "markdown"] = "markdown") -> None:
    """Write the file records to a file.

    Args:
        file_records: List of FileRecord objects to write.
        output_file_path: Path to the output file where the file records will be written.
        output_file_format: Format of the output file, either "json" or "markdown".


        Raises:
        ValueError: If output_file_format is not "json" or "markdown".
    """
    logger.debug("write_file_records_to_file(): writing file records to file: %s", output_file_path)
    with open(output_file_path, "w", encoding="utf-8") as f:
        if output_file_format == "json":
            # Use Pydantic's model_dump() to convert models to dicts, then serialize to JSON
            # This is the recommended pattern for serializing lists of Pydantic models
            file_records_dict = [record.model_dump() for record in file_records]
            json.dump(file_records_dict, f, indent=2)
        elif output_file_format == "markdown":
            f.write(format_file_records_as_markdown(file_records))
        else:
            raise ValueError(f"Invalid output file format: {output_file_format}")
    logger.debug("write_file_records_to_file(): finished writing file records to file: %s", output_file_path.name)

# ---- scan the repo and output a summary of the contents ----
def summarize_repo_contents(repo_root_path: Path, output_file_path: Path,
    output_file_format: Literal["json", "markdown"] = "markdown") -> SummaryResponse:
    """Summarize the contents of the repository.

    Scans the repository, generates a summary of its contents, and writes the
    summary to the specified output file.

    Args:
        repo_root_path: Path to the root of the repository to scan.
        output_file_path: Path to the output file where the summary will be written.
        output_file_format: Format of the output file, either "json" or "markdown".
            Defaults to "markdown".

    Returns:
        A SummaryResponse object containing the repository summary, scan status,
        file counts, and repository root path.
    """
    logger.debug("summarize_repo_contents(): start")

    _, summary = do_the_repo_scan(repo_root_path)
    write_summary_to_file(summary=summary, output_file_path=output_file_path, output_file_format=output_file_format)
    return SummaryResponse(
        repository_summary=summary,
        status="success",
        files_scanned=summary.scanned_files,
        files_skipped=summary.skipped_files,
        repo_root=str(repo_root_path.resolve())
    )

# ---- scan repo and return a list of file records and a summary of the repository contents ----
def do_the_repo_scan(repo_root_path: Path) -> tuple[list[FileRecord], RepositorySummary]:
    """Scan the repository and return a list of file records and a summary of the repository contents.

    Args:
        repo_root_path: Path to the root of the repository.

    Returns:
        A tuple containing a list of FileRecord objects for all files in the repository and a summary of the repository contents.
    """
    logger.debug("do_the_repo_scan(): start")
    file_records: list[FileRecord] = []
    filenames = walk_the_repo(repo_root_path)
    total_files = 0
    files_without_extension = 0
    files_with_extension = 0
    summary = RepositorySummary(
        files_by_language={},
        files_by_category={},
        data_files_by_extension={},
        files_by_technology={},
        files_by_dependency={},
        files_by_extension={}
    )
    for filename in filenames:
        total_files += 1
        relative_dir = filename.relative_to(repo_root_path).as_posix()
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
            technology=technology,
            dependency_kind=dependency_kind,
            size_bytes=size_bytes,
            is_binary=is_binary
        )
        file_records.append(new_file_record)
        
        if language:
            summary.files_by_language[language] = summary.files_by_language.get(language, 0) + 1
        if category:
            summary.files_by_category[category] = summary.files_by_category.get(category, 0) + 1
        if not extension:
            files_without_extension += 1
        else:
            files_with_extension += 1
            summary.files_by_extension[extension] = summary.files_by_extension.get(extension, 0) + 1
        if extension and is_binary:
            summary.binary_files_by_extension[extension] = summary.binary_files_by_extension.get(extension, 0) + 1
        if dependency_kind:
            summary.files_by_dependency[dependency_kind] = summary.files_by_dependency.get(dependency_kind, 0) + 1
        if data_type:
            summary.data_files_by_extension[data_type] = summary.data_files_by_extension.get(data_type, 0) + 1
        if technology:
            summary.files_by_technology[technology] = summary.files_by_technology.get(technology, 0) + 1
    summary.total_files = total_files
    summary.files_without_extension = files_without_extension
    summary.files_with_extension = files_with_extension
    summary.scanned_files = len(file_records)
    summary.skipped_files = total_files - len(file_records)
    logger.debug("do_the_repo_scan(): end")
    return file_records, summary

def scan_repository(repo_root_path: Path, output_file_path: Path,
    output_file_format: Literal["json", "markdown"] = "markdown") -> ScanResponse:
    """Scan the repo, write file information to the output file.

    Scans the repository, writes file information to the output file.
    """
    logger.debug("scan_repository(): start")

    file_records, summary = do_the_repo_scan(repo_root_path)
    write_file_records_to_file(file_records=file_records, output_file_path=output_file_path, output_file_format=output_file_format)
    return ScanResponse(
        status="success",
        repo_root=str(repo_root_path.resolve()),
        files_scanned=len(file_records),
        files_skipped=summary.skipped_files,
        error=None,
        output_file=str(output_file_path.resolve())
    )








# ---- Shebang detection ----
# def detect_shebang_language(p: Path) -> Optional[str]:
#     """Detect the programming language from a file's shebang line.

#     Args:
#         p: Path to the file to check.

#     Returns:
#         The detected language name (e.g., "python", "bash", "javascript") or None.
#     """
#     try:
#         with p.open('r', encoding='utf-8',errors='ignore') as f:
#             first_line = f.readline(200).strip().lower()
#     except Exception:
#         return None
#     if not first_line.startswith('#!'):
#         return None
#     if "python" in first_line:
#         return "python"
#     if "bash" in first_line or "sh" in first_line:
#         return "bash"
#     if "node" in first_line:
#         return "javascript"
#     if "ruby" in first_line:
#         return "ruby"
#     if "perl" in first_line:
#         return "perl"
#     return None
