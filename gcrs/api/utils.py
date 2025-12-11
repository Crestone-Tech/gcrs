# standard library imports
from pathlib import Path
from datetime import datetime
from fastapi import HTTPException, status
from typing import Literal

# local imports
from gcrs.constants import OUTPUT_FORMAT_JSON, OutputFormat, OUTPUT_FILE_FORMAT_EXTENSIONS
from gcrs.logger import setup_logging

# setup logging
logger = setup_logging(log_level="DEBUG")

def generate_output_filename(repo_name: str, operation: Literal["scan", "summary"] = "scan", output_file_format: OutputFormat = OUTPUT_FORMAT_JSON) -> str:
    """Generate a default output filename with repo name and timestamp.
    
    Args:
        repo_name: Name of the repository.
        operation: Operation type to include in filename. Defaults to "scan".
        output_file_format: Format of the output file. Defaults to json if blank/not provided. Other options are markdown and csv. Markdown and csv output tables.
    
    Returns:
        A filename in the format: {repo_name}_{timestamp}.{operation}{extension}
    """
    repo_name = "".join(c for c in repo_name if c.isalnum() or c in ('-', '_', '.')) or "repo"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    file_extension = OUTPUT_FILE_FORMAT_EXTENSIONS.get(output_file_format) 

    return f"{repo_name}_{timestamp}.{operation}{file_extension}"
