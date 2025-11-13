from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path

from app.models import ScanResponse
from app.core.scanner import scan_repo

app = FastAPI(title="Green Cloud Repository Scanner")

@app.get("/")
async def root():
    return {"message": "Green Cloud Repository Scanner"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

class ScanParams(BaseModel):
    root: str

@app.post("/scan", response_model=ScanResponse)
def scan(params: ScanParams):
    root = Path(params.root).resolve()
    records = scan_repo(root)
    return ScanResponse(
        records=records,
        root=str(root),
        scanned_count=len(records),
        skipped_count=0
    )
