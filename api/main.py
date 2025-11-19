from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

import gcrs.core.scanner as scanner
from gcrs.logger import setup_logging
from gcrs.models import ScanResponse, SummaryResponse

# ---- setup logging ----
logger = setup_logging(log_level="DEBUG")
logger.debug("gcrs.api.main.py:main() starting the API")

# ---- instantiate the FastAPI as the app ----
app = FastAPI(title="Green Cloud Repository Scanner")

# ---- root endpoint ----
@app.get("/")
async def root():
    return {"message": "Green Cloud Repository Scanner"}

# ---- health check endpoint ----
@app.get("/health")
async def health():
    return {"status": "healthy"}

# ---- helper functions ----
def validate_path(path: str) -> Path | None:
    """Validate that the path exists and is a directory.
    
    Args:
        path: Path to the directory.
    
    Returns:
        Path object if valid, None if invalid.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        logger.error("The specified path does not exist and will be created: %s", path_obj)
        path_obj.mkdir(parents=True, exist_ok=True)
    elif not path_obj.is_dir():
        logger.error("The specified path is not a directory: %s", path_obj)
        return None
        
    return path_obj

def generate_default_output_file(repo_root: str, file_extension: str = "sarif") -> str:
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

# ---- scan parameters ----
# ScanParams is a Pydantic model to define and validate the parameters for a scan request (for example, when accepting POST/JSON body parameters about which repo directory to scan).
class ScanParams(BaseModel):
    repo_root: str = "."
    output_dir: str = "output"
    output_format: str = "SARIF"
    output_file: str | None = None

class SummaryParams(BaseModel):
    repo_root: str = "."
    output_dir: str = "output"
    output_file: str | None = None

# ---- scan the repository and output a summary of the contents ----
@app.post("/scan/summary")
async def summarize_repository_contents(params: SummaryParams) -> SummaryResponse:
    """Summarize the contents of the repository:

    - # of files scanned
    - # of files skipped
    - # of files per category (code, config, docs, etc.)
    - # of files per language (python, javascript, etc.)
    
    Args:
        params: SummaryParams containing the repository root directory and output directory.
    
    Returns:
        A SummaryResponse containing the summary of the repository contents. 
        On Error: If the repository root directory does not exist, sets the status to "error" and returns an error response.
    """
    logger.debug("gcrs.api.main:summarize_repository_contents() starting at directory: %s", params.repo_root)

    # validate the repository root directory before proceeding
    repo_root_path = validate_path(params.repo_root)
    if repo_root_path is None:
        return SummaryResponse(
            status="error",
            error="The specified repository root directory does not exist or is not a directory",
            repo_root=params.repo_root,
            summary=None,
            files_scanned=None,
            files_skipped=None,
        )

    # create output directory if it doesn't exist (output_dir is relative to repo_root)
    output_dir_path = validate_path(str(repo_root_path / params.output_dir))
    if output_dir_path is None:
        return SummaryResponse(
            status="error",
            error="The specified output directory is not a directory",
            repo_root=params.repo_root,
            summary=None,
            files_scanned=None,
            files_skipped=None,
        )
    # generate default output filename if not provided
    output_file = params.output_file or generate_default_output_file(params.repo_root, "summary.txt")
    output_file_path = output_dir_path / output_file
    if not output_file_path.exists():
        output_file_path.touch()
    
    # summarize the repository content
    summary_response = scanner.summarize_repo_contents(repo_root_path=repo_root_path, output_file_path=output_file_path)
    logger.debug("method: generate_repo_summary() finished summarizing repository content, status: %s", summary_response.status)
    return summary_response


# ---- scan the repository and output full info about the files in the repository ----
# @app.get("/scan")
# async def scan_repository(ScanParams: ScanParams) -> ScanResponse:
#     logger.debug("gcrs.api.main:scan_repository() starting at directory: %s", ScanParams.repo_root)
#     repo_root_path = Path(ScanParams.repo_root)
#     # check if repo root directory exists
#     if not repo_root_path.exists() or not repo_root_path.is_dir():
#         logger.error("Directory does not exist: %s", ScanParams.repo_root)
#         return ScanResponse(
#             status="error",
#             repo_root=ScanParams.repo_root,
#             scanned_count=0,
#             skipped_count=0,
#             error="Directory does not exist",
#         )
#     # scan the repository
#     file_records = scan_repo(repo_root_path)
#     logger.debug(
#         "method: scan_learning_repository() finished scanning repository, found %d file records",
#         len(file_records),
#     )
#     # create output directory if it doesn't exist
#     output_dir_path = repo_root_path / output_dir
#     output_dir_path.mkdir(parents=True, exist_ok=True)
#     # save file records to output directory
    
#     # create response
#     response = ScanResponse(
#         status="success",
#         repo_root=str(repo_root_path.resolve()),
#         scanned_count=len(file_records),
#         skipped_count=0,
#     )
#     return response

