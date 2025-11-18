from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from app.logger import setup_logging
from app.models import FileRecord, RepositorySummary, SummaryResponse

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
DATA_EXTENSIONS = {".csv", ".jsonl", ".xml", ".tsv", ".parquet", ".sqlite", ".db", ".ndjson"}

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
    **dict.fromkeys(DATA_EXTENSIONS, "data"),
    # assets (fallback: binary handled via is_binary_ext)
    ".svg": "asset",
}

# CI/CD filenames (no extension or special names)
CI_FILENAMES = {"Jenkinsfile", ".gitlab-ci.yml", "azure-pipelines.yml"}
CI_DIR_HINTS = {".github/workflows", ".circleci"}

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
    return ext in DATA_EXTENSIONS


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

# ---- write the summary to a file ----
def write_summary_to_file(summary: RepositorySummary, output_file_path: Path):
    """Write the summary to a file.

    Args:
        summary: String summary of the repository contents.
        summary_file_path: Path to the output file.
    """
    logger.debug("write_summary_to_file(): writing summary to file: %s", output_file_path)
    with open(output_file_path, "w", encoding="utf-8") as f:
        # The summary object is a Pydantic model, so you can serialize it to JSON and write it to a file.
        # This uses the Pydantic model's model_dump_json() method to dump as JSON.
        json_str = summary.model_dump_json(indent=2)
        f.write(json_str)
    logger.debug("write_summary_to_file(): finished writing summary to file: %s", output_file_path.name)

# ---- scan the repo and output a summary of the contents ----
def summarize_repo_contents(repo_root_path: Path, output_file_path: Path) -> SummaryResponse:
    """Summarize the contents of the repository.

    Args:
        repo_root_path: Path to the root of the repository.
        output_file_path: Path to the output file.

    Returns:
        A string summarizing the contents of the repository.
    """
    logger.debug("summarize_repo_contents(): start")

    file_records, summary = scan_repo(repo_root_path)
        
    write_summary_to_file(summary=summary, output_file_path=output_file_path)
    return SummaryResponse(
        status="success",
        files_scanned=summary.scanned_files,
        files_skipped=summary.skipped_files,
        repo_root=str(repo_root_path.resolve())
    )
    
# ---- scan repo and return a list of file records and a summary of the repository contents ----
def scan_repo(repo_root_path: Path) -> tuple[list[FileRecord], RepositorySummary]:
    """Scan the repository and return a list of file records and a summary of the repository contents.

    Args:
        repo_root_path: Path to the root of the repository.

    Returns:
        A tuple containing a list of FileRecord objects for all files in the repository and a summary of the repository contents.
    """
    logger.debug("scan_repo(): start")
    file_records: list[FileRecord] = []
    filenames = walk_the_repo(repo_root_path)
    summary = RepositorySummary(
        language_files={},
        category_files={},
        technology_files={},
        dependency_files={},
        file_extensions={},
        total_files=0,
        scanned_files=0,
        skipped_files=0,
        summary="",
    )
    
    for filename in filenames:
        relative_dir = filename.relative_to(repo_root_path).as_posix()
        name = filename.name
        extension = filename.suffix.lower()
        language = LANGUAGE_BY_EXT.get(extension, None)
        category = CATEGORY_BY_EXT.get(extension, None)
        is_binary = is_binary_ext(extension)
        size_bytes = filename.stat().st_size
        new_file_record = FileRecord(
            relative_dir=relative_dir,
            name=name,
            extension=extension,
            category=category,
            language=language,
            is_binary=is_binary,
            size_bytes=size_bytes,
        )
        file_records.append(new_file_record)
        summary.scanned_files += 1
        if language:
         summary.language_files[language] = 1
        if category:
         summary.category_files[category] = 1
        if extension:
         summary.file_extensions[extension] = 1
    logger.debug("scan_repo(): end")
    return file_records, summary

















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


# def scan_repo(repo_root: Path) -> List[FileRecord]:
#     """Scan the repository and return a list of file records.

#     Args:
#         repo_root: Path to the root of the repository.

#     Returns:
#         A list of FileRecord objects for all files in the repository.
#     """

#     records: List[FileRecord] = []
#     for path in walk_files(repo_root):
#         ext = path.suffix.lower()
#         shebang_language = detect_shebang_language(path)
#         language = shebang_language or LANGUAGE_BY_EXT.get(ext, "unknown")

#         category = "placeholder"
#         size_bytes = path.stat().st_size
#         is_binary = is_binary_ext(ext)
#         relative_dir = path.parent.relative_to(repo_root).as_posix() if path.parent != repo_root else "."

#         records.append(FileRecord(
#             relative_dir=relative_dir,
#             name=path.name,
#             extension=ext or "",
#             category=category,
#             language=language,
#             size_bytes=size_bytes,
#             is_binary=is_binary,
#         ))
#         return records
