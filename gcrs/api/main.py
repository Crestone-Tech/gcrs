from __future__ import annotations
from datetime import datetime
from pathlib import Path
import json
from fastapi import FastAPI, HTTPException, status

import gcrs.core.scanner as scanner
from gcrs.logger import setup_logging
from gcrs.models import SummaryParams, SummaryResponse, ScanParams, ScanResponse

# ---- setup logging ----
logger = setup_logging(log_level="DEBUG")
logger.debug("gcrs.api.main.py:main() starting the API")

# ---- instantiate the FastAPI as the app ----
app = FastAPI(
    title="Green Cloud Repository Scanner",
    description="API for scanning repositories and generating summaries of their contents",
    version="1.0.0",
)

# ---- root endpoint ----
@app.get(
    "/",
    summary="API root",
    description="Returns a message identifying the Green Cloud Repository Scanner API",
    tags=["General"],
)
async def root():
    """API root endpoint.
    
    Returns a simple message identifying the API service.
    
    **Returns:**
    - `message`: Service identification message
    """
    return {"message": "Green Cloud Repository Scanner"}

# ---- health check endpoint ----
@app.get(
    "/healthz",
    summary="Health check endpoint",
    description="Health check endpoint to verify the API service is running",
    tags=["General"],
)
async def health():
    """Health check endpoint.
    
    Used to verify that the API service is running and responsive.
    Useful for monitoring and load balancer health checks.
    
    **Returns:**
    - `status`: "healthy" if the service is operational
    """
    return {"status": "healthy"}

# ---- helper functions ----
def validate_and_resolve_path(path: str, must_exist: bool = False, create_if_missing: bool = False) -> Path | None:
    """Validate and resolve a path, optionally creating it if missing.
    
    Args:
        path: Path to validate.
        must_exist: If True, path must exist or None is returned.
        create_if_missing: If True, create the directory if it doesn't exist.
    
    Returns:
        Resolved Path object if valid, None if invalid.
    """
    try:
        path_obj = Path(path).resolve()
        if not path_obj.exists():
            if must_exist:
                logger.error("The specified path does not exist: %s", path_obj)
                return None
            if create_if_missing:
                logger.info("Creating directory: %s", path_obj)
                path_obj.mkdir(parents=True, exist_ok=True)
        elif not path_obj.is_dir():
            logger.error("The specified path is not a directory: %s", path_obj)
            return None
        return path_obj
    except (OSError, ValueError) as e:
        logger.error("Error validating path %s: %s", path, e)
        return None

def generate_default_output_file(repo_root: str, file_extension: str = "summary.txt") -> str:
    """Generate a default output filename with repo name and timestamp.
    
    Args:
        repo_root: Path to the repository root directory.
        file_extension: File extension (without the dot).
    
    Returns:
        A filename in the format: {repo_name}_{timestamp}.{extension}
    """
    repo_path = Path(repo_root).resolve()
    # Get the directory name, or use "repo" as fallback
    repo_name = repo_path.name if repo_path.name else "repo"
    # Sanitize the repo name (remove invalid filename characters)
    repo_name = "".join(c for c in repo_name if c.isalnum() or c in ('-', '_', '.')) or "repo"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{repo_name}_{timestamp}.{file_extension}"

# ---- scan the repository and output a summary of the contents ----
@app.post(
    "/scan/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan repository and generate summary",
    description="""
    Scans a repository directory and generates a comprehensive summary of its contents.
    
    The summary includes:
    - Total number of files scanned and skipped
    - # of files by language (Python, JavaScript, etc.)
    - # of files by type (code, config, documentation, etc.)
    - # of files by technology (Docker, Kubernetes, etc.)
    - # of files by dependency management system
    - # of files by file extension
    - # of data files by extension
    
    The summary is written to a JSON file in the specified output directory.
    """,
    response_description="Summary response containing repository statistics",
    tags=["Scanning"],
)
async def summarize_repository_contents(params: SummaryParams) -> SummaryResponse:
    """Summarize the contents of a repository.
    
    Scans the specified repository directory and generates a detailed summary
    of file types, languages, technologies, and dependencies found.
    
    **Parameters:**
    - `repo_root`: Path to the repository root directory (default: ".")
    - `output_dir`: Directory relative to repo_root where output file will be written (default: "output")
    - `output_file`: Optional filename for the summary JSON file. If not provided, generates a default name.
    
    **Returns:**
    - `status`: "success" or "error"
    - `files_scanned`: Number of files successfully scanned
    - `files_skipped`: Number of files skipped during scanning
    - `repo_root`: Absolute path to the scanned repository
    - `error`: Error message if status is "error"
    
    **Example Request:**
    ```json
    {
        "repo_root": ".",
        "output_dir": "output",
        "output_file": null
    }
    ```
    
    **Example Response:**
    ```json
    {
        "status": "success",
        "files_scanned": 150,
        "files_skipped": 5,
        "repo_root": "/path/to/repository"
    }
    ```
    """
    logger.debug("gcrs.api.main:summarize_repository_contents() starting at directory: %s", params.repo_root)

    try:
        # validate the repository root directory before proceeding
        repo_root_path = validate_and_resolve_path(params.repo_root, must_exist=True)
        if repo_root_path is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "error": "The specified repository root directory does not exist or is not a directory",
                    "repo_root": params.repo_root,
                },
            )

        # create output directory if it doesn't exist (output_dir is relative to repo_root)
        output_dir_path = validate_and_resolve_path(
            str(repo_root_path / params.output_dir),
            create_if_missing=True,
        )
        if output_dir_path is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "error": f"The specified output directory path [{params.output_dir}] is invalid or could not be created",
                    "repo_root": str(repo_root_path),
                },
            )

        # generate default output filename if not provided
        output_file = params.output_file or generate_default_output_file(str(repo_root_path))
        # Ensure output_file is not empty
        if not output_file or not output_file.strip():
            output_file = generate_default_output_file(str(repo_root_path))
        
        output_file_path = output_dir_path / output_file
        # Ensure parent directory exists
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        # Create the file if it doesn't exist
        if not output_file_path.exists():
            output_file_path.touch()
        
        # summarize the repository content
        summary_response = scanner.summarize_repo_contents(
            repo_root_path=repo_root_path,
            output_file_path=output_file_path,
            output_file_format=params.output_file_format,
        )
        logger.debug(
            "method: summarize_repo_contents() finished summarizing repository content, status: %s",
            summary_response.status,
        )
        return summary_response

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.exception("Unexpected error in summarize_repository_contents: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "error": f"An unexpected error occurred: {str(e)}",
                "repo_root": params.repo_root,
            },
        )

# ---- scan the repository and output full info about the files in the repository ----
@app.post("/scan")
async def scan_repository(params: ScanParams) -> ScanResponse:
    """Scan the repository and output full info about the files in the repository.

    The output includes:
    - Total number of files scanned and skipped
    - for each file:
        - relative path
        - name
        - extension
        - category
        - language
        - technology
        - dependency management system
        - size in bytes
        - is binary
        - is data file
        - is code file
        - is config file
        - is documentation file
        - is test file
        - is example file
        - is sample file

    The output is written to a file in the specified output directory.

    Output file formats:

    - json
    - markdown
    - csv

    **Parameters:**
    - `repo_root`: Path to the repository root directory
    - `output_dir`: Directory relative to repo_root where output file will be written
    - `output_file`: Optional filename for the output file. If not provided, generates a default name.
    - `output_file_format`: Format of the output file, either "json" or "markdown" or "csv". Defaults to "json".

    **Returns:**
    - `status`: "success" or "error"
    - `repo_root`: Absolute path to the scanned repository
    - `scanned_count`: Number of files successfully scanned
    - `skipped_count`: Number of files skipped during scanning
    - `error`: Error message if status is "error"

    **Example Request:**
    ```json
    {
        "repo_root": ".",
        "output_dir": "output",
        "output_file": null,
        "output_file_format": "json"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "status": "success",
        "repo_root": "/path/to/repository",
        "scanned_count": 150,

    }
    ```
"""

    logger.debug("gcrs.api.main:scan_repository() starting at directory: %s", params.repo_root)
    repo_root_path = Path(params.repo_root)
    # check if repo root directory exists
    if not repo_root_path.exists() or not repo_root_path.is_dir():
        logger.error("Directory does not exist: %s", params.repo_root)
        return ScanResponse(
            status="error",
            repo_root=params.repo_root,
            scanned_count=0,
            skipped_count=0,
            error="Directory does not exist",
        )
    output_file_path = Path(params.output_dir) / params.output_file
    # scan the repository
    scan_response = scanner.scan_repository(repo_root_path=repo_root_path, output_file_path=output_file_path, output_file_format=params.output_file_format)
    
    # create response
    response = ScanResponse(
        status="success",
        repo_root=str(repo_root_path.resolve()),
        files_scanned=scan_response.files_scanned,
        files_skipped=scan_response.files_skipped,
        error=None,
        output_file=str(output_file_path.resolve().as_posix()),
    )
    return response

