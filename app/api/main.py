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
    root: str


@app.get("/file/slr")
async def scan_learning_repository(directory: str = ".") -> ScanResponse:
    logger.debug("method: scan_learning_repository() starting at directory: %s", directory)
    file_records = scan_learning_repo(Path(directory))
    logger.debug(
        "method: scan_learning_repository() finished scanning repository, found %d file records",
        len(file_records),
    )
    response = ScanResponse(
        status="success",
        records=file_records,
        root=str(Path(directory).resolve()),
        scanned_count=len(file_records),
        skipped_count=0,
    )
    return response
