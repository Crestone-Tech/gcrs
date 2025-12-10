from __future__ import annotations
from fastapi import FastAPI, HTTPException, status

from gcrs.api.utils import generate_output_filename
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
    contact={
        "name": "Crestone Technology",
        "url": "https://crestone.tech",
        "email": "info@crestone.tech",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
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

# ---- scan the repository and output details about each file in the repository ----
@app.post("/scan")
async def scan_repository(params: ScanParams) -> ScanResponse:
    """Scans the repository and outputs details about each file in the repository.

    **Returns:**
    - `status`: "success" or "error"
    - `error`: Error message if status is "error"
"""

    logger.debug("gcrs.api.main:scan_repository() starting at directory: %s", params.repo_root)

    try:
        output_dir = params.repo_root / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / generate_output_filename(repo_root=str(params.repo_root.name), operation="scan", output_file_format=params.output_file_format)

        # scan the repository
        scan_response = scanner.scan_repository(
            repo_root=params.repo_root,
            output_file=output_file,
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

# ---- scan the repository and output a summary of the contents ----
@app.post(
    "/scan/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan repository and output summary of contents",
    description="""Scans a repository directory and generates a comprehensive summary of its contents.""",
    response_description="Summary response containing repository statistics",
    tags=["Scanning"],
)
async def summarize_repository_contents(params: ScanParams) -> SummaryResponse:
    """Scans the specified repository directory and generates a summary
    of file types, languages, technologies, and dependencies found.
    
    **Parameters:**
    - `repo_root`: Path to the repository root directory (default: ".")
    - `output_file_format`: Format of the output file, either "json", "markdown", or "csv". Defaults to "json".
    
    **Returns:**
    - `status`: "success" or "error"
    - `repository_summary`: Summary of the repository contents
    - `error`: Error message if status is "error"
    
    """
    logger.debug("gcrs.api.main:summarize_repository_contents() starting at directory: %s", params.repo_root)

    try:
        # validate the repository root directory before proceeding
        output_dir = params.repo_root / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / generate_output_filename(repo_root=str(params.repo_root.name), operation="summary", output_file_format=params.output_file_format)

        # summarize the repository content
        summary_response = scanner.summarize_repo_contents(
            repo_root=params.repo_root,
            output_file=output_file,
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
