from __future__ import annotations
import os
from pathlib import Path
from typing import Iterable, List, Optional
from app.models import FileRecord

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
    ".mypy_cache"
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
    ".exe",".dll",".so",".dylib",".ttf",".otf",".woff",".woff2",".mp4",".mov",".avi"    
}

DATA_EXTENSIONS = {
    ".csv",
    ".jsonl",
    ".xml",
    ".tsv",
    ".parquet",
    ".sqlite",
    ".db",
    ".ndjson"
}

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
    ".vb": "vb"
}

# Category by extension (baseline)
CATEGORY_BY_EXT = {
    # code
    **{ext:"code" for ext in LANGUAGE_BY_EXT.keys()},
    # config
    ".yml":"config",".yaml":"config",".json":"config",".toml":"config",".ini":"config",".cfg":"config",".conf":"config",
    # docs
    ".md":"documentation",".rst":"documentation",".txt":"documentation",".adoc":"documentation",
    # scripts
    ".sh":"script",".ps1":"script",".bat":"script",".cmd":"script",
    # infrastructure
    ".tf":"infrastructure",".dockerfile":"infrastructure",
    # data
    **{ext:"data" for ext in DATA_EXTENSIONS},
    # assets (fallback: binary handled via is_binary_ext)
    ".svg":"asset",
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
    """ Check if a file extension is in the list of data extensions.

    Args:
        ext: File extension to check.

    Returns:
        True if the extension is in the list of data extensions, False otherwise.
    """
    return ext in DATA_EXTENSIONS

def walk_files(root: Path) -> Iterable[Path]:
    """Walk the repository and yield all files that are not in the skip directories.

    Args:
        root: Path to the root of the repository.

    Returns:
        An iterable of Path objects for all files in the repository.
    """
    for dirpath, subdirnames, filenames in os.walk(root):
        subdirnames[:] = [d for d in subdirnames if d not in SKIP_DIRS]
        for fname in filenames:
            yield Path(dirpath) / fname

# ---- Shebang detection ----
def detect_shebang_language(p: Path) -> Optional[str]:
    """Detect the programming language from a file's shebang line.

    Args:
        p: Path to the file to check.

    Returns:
        The detected language name (e.g., "python", "bash", "javascript") or None.
    """
    try:
        with p.open('r', encoding='utf-8',errors='ignore') as f:
            first_line = f.readline(200).strip().lower()
    except Exception:
        return None
    if not first_line.startswith('#!'):
        return None
    if "python" in first_line: 
        return "python"
    if "bash" in first_line or "sh" in first_line: 
        return "bash"
    if "node" in first_line:
        return "javascript"
    if "ruby" in first_line:
        return "ruby"
    if "perl" in first_line:
        return "perl"
    return None

# ---- Main scan function ----
def scan_repo(root: Path) -> List[FileRecord]:
    """Scan the repository and return a list of file records.

    Args:
        root: Path to the root of the repository.

    Returns:
        A list of FileRecord objects for all files in the repository.
    """
    
    records: List[FileRecord] = []
    for path in walk_files(root):
        ext = path.suffix.lower()
        shebang_language = detect_shebang_language(path)
        language = shebang_language or LANGUAGE_BY_EXT.get(ext, "unknown")

        category = "placeholder"
        size_bytes = path.stat().st_size
        is_binary = is_binary_ext(ext)
        relative_dir = path.parent.relative_to(root).as_posix() if path.parent != root else "."
                
        records.append(FileRecord(
            relative_dir=relative_dir,
            name=path.name,
            extension=ext or "",
            category=category,
            language=language,
            size_bytes=size_bytes,
            is_binary=is_binary,
        ))
        return records
