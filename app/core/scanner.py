from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from app.logger import setup_logging
from app.models import FileRecord, SummaryResponse

logger = setup_logging(log_level="DEBUG")

# ---- Configuration ----
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

# Simple lists for quick binary/data detection
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

DATA_EXTENSIONS = {".csv", ".jsonl", ".xml", ".tsv", ".parquet", ".sqlite", ".db", ".ndjson"}

# Language map (for "code" category)
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

# Category by extension (baseline)
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

# Dependency files
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
    return ext in DATA_EXTENSIONS


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

# ---- the Summary function ----
def parse_summary(file_records: list[FileRecord]) -> str:
    """Parse the summary of the repository contents.

    Args:
        file_records: List of FileRecord objects.

    Returns:
        A string summarizing the contents of the repository.
    """
    logger.debug("parse_summary(): start")
    logger.debug("parse_summary(): parsing summary of %d file records", len(file_records))
    summary = "Repository contents summarized"
    summary_lines = ["foo", "bar", "baz"]
    #for file_record in file_records:
     #   summary_lines.append(f"{file_record.relative_dir}/{file_record.name}")
    summary = "\n".join(summary_lines)
    logger.debug("parse_summary(): finished parsing summary of %d file records", len(file_records))
    return summary

def write_summary_to_file(summary: str, output_dir_path: Path):
    """Write the summary to a file.

    Args:
        summary: String summary of the repository contents.
        output_dir_path: Path to the output directory.
    """
    summary_file_path = output_dir_path / "summary.txt"
    logger.debug("write_summary_to_file(): writing summary to file: %s", summary_file_path)
    with open(summary_file_path, "w", encoding="utf-8") as f:
        f.write(summary)
    logger.debug("write_summary_to_file(): finished writing summary to file: %s", summary_file_path)

def summarize_repo_contents(repo_root_path: Path, output_dir_path: Path) -> SummaryResponse:
    """Summarize the contents of the repository.

    Args:
        repo_root_path: Path to the root of the repository.
        output_dir_path: Path to the output directory.

    Returns:
        A string summarizing the contents of the repository.
    """
    logger.debug("summarize_repo_contents(): start")

    file_records = scan_repo(repo_root_path)
    logger.debug("summarize_repo_contents(): finished scanning repository, found %d file records", len(file_records))
    summary = parse_summary(file_records)
    logger.debug("summarize_repo_contents(): finished parsing summary, summary: %s", summary)
    write_summary_to_file(summary, output_dir_path)
    return SummaryResponse(
        status="success",
        summary=summary,
        repo_root=str(repo_root_path.resolve()),
        files_scanned=len(file_records),
        files_skipped=0,
    )
    
# ---- the Main scan function ----
def scan_repo(repo_root_path: Path) -> list[FileRecord]:
    """Scan the learning repository and return a list of file records.

    Args:
        repo_root_path: Path to the root of the repository.

    Returns:
        A list of FileRecord objects for all files in the repository.
    """

    logger.debug("scan_repo(): start")
    logger.debug("scan_repo(): calling walk_the_repo")

    file_records: list[FileRecord] = []
    filenames = walk_the_repo(repo_root_path)
    for filename in filenames:
        logger.debug(
            "\tscan_repo(): received yield from walk_the_repo(): filename: %s", filename
        )
        relative_dir = filename.relative_to(repo_root_path).as_posix()
        name = filename.name
        extension = filename.suffix.lower()
        language = LANGUAGE_BY_EXT.get(extension, "unknown")
        category = CATEGORY_BY_EXT.get(extension, "unknown")
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

    logger.debug("scan_repo(): end")
    return file_records
