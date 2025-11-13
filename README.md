# gcrs
Green Cloud Repository Scanner - scans a repository and generates a bill of materials (BOM)

## Setup

### Prerequisites
- Python 3.11 or higher
- pip

### Installation

1. Create a virtual environment:
   
   python -m venv .venv
   
2. Activate the virtual environment:
   
   **On Windows (Git Bash):**
   source .venv/Scripts/activate
      
   **On Windows (CMD):**
   
   .venv\Scripts\activate.bat
      **On Linux/Mac:**h
   source .venv/bin/activate
   3. Install dependencies:
  
   pip install -e .
      This will install FastAPI, uvicorn, pydantic, and other required packages.

## Starting the API

1. Ensure your virtual environment is activated (you should see `(.venv)` in your prompt).

2. Start the API server:
   
   uvicorn app.api.main:app --reload
      The `--reload` flag enables auto-reload during development.

3. The API will be available at:
   - **API Root:** http://127.0.0.1:8000/
   - **Health Check:** http://127.0.0.1:8000/health
   - **API Documentation:** http://127.0.0.1:8000/docs (Swagger UI)
   - **Alternative Docs:** http://127.0.0.1:8000/redoc (ReDoc)

### Verifying the Virtual Environment

To confirm you're using the virtual environment, check:
which uvicornThis should show a path containing `.venv` or `venv` (e.g., `/path/to/gcrs/.venv/Scripts/uvicorn`).

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check endpoint
- `POST /scan` - Scan a repository and generate a BOM
