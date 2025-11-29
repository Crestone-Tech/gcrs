# standard library imports
from pathlib import Path
from datetime import datetime
from typing import Literal
from fastapi import HTTPException, status

# local imports
from gcrs.logger import setup_logging

# setup logging
logger = setup_logging(log_level="DEBUG")

# dictionary that maps output file formats to their corresponding file extensions
OUTPUT_FILE_FORMAT_EXTENSIONS = {
    "json": ".json",
    "markdown": ".md",
    "csv": ".csv",
}

def validate_directory_path(path: str) -> Path | None:
    """Validate a directory path.
    
    Args:
        path: Directory path to validate.
    
    Returns:
        Resolved Path object if the directory exists and is a directory
        None if the directory does not exist or is not a directory.
    """
    try:
        path_obj = Path(path).resolve()
        if not path_obj.exists():
            logger.error("The specified path does not exist: %s", path_obj)
            return None
        if not path_obj.is_dir():
            logger.error("The specified path is not a directory: %s", path_obj)
            return None
        return path_obj
    except (OSError, ValueError) as e:
        logger.error("Error validating path %s: %s", path, e)
        return None

def validate_root_and_output_directory(repo_root: str) -> tuple[Path, Path]:
    """Validate the repository root directory and create the output directory if it doesn't exist.

    Args:
        repo_root: Path to the repository root directory.
    Raises:
        HTTPException: If the repository root directory does not exist or is not a directory.
    Returns:
        A tuple containing the repository root directory and the output directory.
        None if the repository root directory does not exist or is not a directory.
    """
    repo_root_path = validate_directory_path(repo_root)
    if repo_root_path is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "error": f"The specified repository root directory [{repo_root}] does not exist or is not a directory",
            },
        )

    output_dir_path = repo_root_path / './output'
    output_dir_path.mkdir(parents=True, exist_ok=True)

    return (repo_root_path, output_dir_path)

def generate_output_filename(repo_root: str, operation: Literal["scan", "summary"] = "scan", output_file_format: Literal["json", "markdown", "csv"] = "json") -> str:
    """Generate a default output filename with repo name and timestamp.
    
    Args:
        repo_root: Path to the repository root directory.
        operation: Operation type to include in filename. Defaults to "scan".
        output_file_format: Format of the output file. Defaults to json if blank/not provided. Other options are markdown and csv. Markdown and csv output tables.
    
    Returns:
        A filename in the format: {repo_name}_{timestamp}.{operation}{extension}
    """
    repo_root_path = Path(repo_root)
    repo_name = repo_root_path.name if repo_root_path.name else "repo"
    repo_name = "".join(c for c in repo_name if c.isalnum() or c in ('-', '_', '.')) or "repo"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    file_extension = OUTPUT_FILE_FORMAT_EXTENSIONS.get(output_file_format) 

    return f"{repo_name}_{timestamp}.{operation}{file_extension}"
