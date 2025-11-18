from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from app.core.scanner import scan_learning_repo
from app.logger import setup_logging
from app.models import ScanResponse

logger = setup_logging(log_level="DEBUG")
logger.debug("Starting the API")

app = FastAPI(title="Green Cloud Repository Scanner")


@app.get("/")
async def root():
    return {"message": "Green Cloud Repository Scanner"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


class ScanParams(BaseModel):
    repo_root: str


@app.get("/file/slr")
async def scan_learning_repository(repo_root: str = ".") -> ScanResponse:
    logger.debug("method: scan_learning_repository() starting at directory: %s", repo_root)
    repo_root_path = Path(repo_root)
    if not repo_root_path.exists() or not repo_root_path.is_dir():
        logger.error("Directory does not exist: %s", repo_root)
        return ScanResponse(
            status="error",
            records=[],
            repo_root=str(repo_root_path.resolve()),
            scanned_count=97,
            skipped_count=0,
        )
    file_records = scan_learning_repo(repo_root_path)
    logger.debug(
        "method: scan_learning_repository() finished scanning repository, found %d file records",
        len(file_records),
    )
    # create output directory if it doesn't exist
    output_dir = repo_root_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    # save file records to output directory
    
    # create response
    response = ScanResponse(
        status="success",
        repo_root=str(repo_root_path.resolve()),
        scanned_count=len(file_records),
        skipped_count=0,
    )
    return response
