from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, HTTPException, status

from gcrs.api.utils import validate_root_and_output_directory, generate_output_filename
import gcrs.core.scanner as scanner
from gcrs.logger import setup_logging
from gcrs.models import SummaryResponse, ScanParams, ScanResponse

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
async def summarize_repository_contents(params: ScanParams) -> SummaryResponse:
    """Summarize the contents of a repository.
    
    Scans the specified repository directory and generates a detailed summary
    of file types, languages, technologies, and dependencies found.
    
    **Parameters:**
    - `repo_root`: Path to the repository root directory (default: ".")
    - `output_file_format`: Format of the output file, either "json" or "markdown" or "csv". Defaults to "json".
    
    **Returns:**
    - `status`: "success" or "error"
    - `repository_summary`: Summary of the repository contents
    - `error`: Error message if status is "error"
    
    **Example Request:**
    ```json
    {
        "repo_root": ".",
        "output_file_format": "markdown"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "status": "success",
        "error": null,
        "repository_summary": {
            "total_files": 150,
            "scanned_files": 145,
            "skipped_files": 5,
            "files_by_language": {
                "python": 50,
                "javascript": 30,
                "typescript": 20
            },
        }
    }
    ```
    """
    logger.debug("gcrs.api.main:summarize_repository_contents() starting at directory: %s", params.repo_root)

    try:
        # validate the repository root directory before proceeding
        repo_root_path, output_dir_path = validate_root_and_output_directory(params.repo_root)
        output_file_path = output_dir_path / generate_output_filename(repo_root=str(repo_root_path.name), operation="summary", output_file_format=params.output_file_format)

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

    Output is written to ./output in the GCRS project directory. The file name is generated based on the repository name and timestamp.

    Output file formats:

    - json
    - markdown
    - csv

    **Parameters:**
    - `repo_root`: Path to the repository root directory
    - `output_file_format`: Format of the output file, either "json" or "markdown" or "csv". Defaults to "json".

    **Returns:**
    - `status`: "success" or "error"
    - `error`: Error message if status is "error"

    **Example Request:**
    ```json
    {
        "repo_root": ".",
        "output_file_format": "markdown"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "status": "success",
        "error": null,
    }
    ```
"""

    logger.debug("gcrs.api.main:scan_repository() starting at directory: %s", params.repo_root)

    try:
        # validate the repository root directory before proceeding
        repo_root_path, output_dir_path = validate_root_and_output_directory(params.repo_root)

        output_file_path = output_dir_path / generate_output_filename(repo_root=str(repo_root_path.name), operation="scan", output_file_format=params.output_file_format)

        # scan the repository
        scan_response = scanner.scan_repository(
            repo_root_path=repo_root_path,
            output_file_path=output_file_path,
            output_file_format=params.output_file_format,
        )
        logger.debug(
            "method: scan_repository() finished scanning repository, status: %s",
            scan_response.status,
        )
        return scan_response

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.exception("Unexpected error in scan_repository: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "error": f"An unexpected error occurred: {str(e)}",
                "repo_root": params.repo_root,
            },
        )
