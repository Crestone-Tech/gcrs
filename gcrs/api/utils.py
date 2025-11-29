# standard library imports
from pathlib import Path
from datetime import datetime
from typing import Literal

# local imports
from gcrs.logger import setup_logging

# setup logging
logger = setup_logging(log_level="DEBUG")

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

def generate_output_filename(repo_root: str, operation: Literal["scan", "summary"] = "scan", output_file_format: Literal["json", "markdown", "csv"] = "json") -> str:
    """Generate a default output filename with repo name and timestamp.
    
    Args:
        repo_root: Path to the repository root directory.
        output_file_format: Format of the output file. Defaults to json if blank/not provided. Other options are markdown and csv. Markdown and csv output tables.
    
    Returns:
        A filename in the format: {repo_name}_{timestamp}.{operation}.{extension}
    """
    repo_name = "".join(c for c in repo_root if c.isalnum() or c in ('-', '_', '.')) or "repo"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    file_extension = "json" if output_file_format == "json" else "md" if output_file_format == "markdown" else "csv"

    return f"{repo_name}_{timestamp}.{operation}.{file_extension}"
