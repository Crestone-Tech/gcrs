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
- `POST /scan/summary` - Generate a summary of repository contents
- `POST /scan` - Scan a repository and generate a BOM

## Testing

### Testing `/scan/summary` Endpoint

The `/scan/summary` endpoint returns a JSON summary of the repository contents, including counts by category, language, and extension.

#### Using curl

**Test with default parameters (scans current directory):**
```bash
curl -X POST "http://127.0.0.1:8000/scan/summary"
```

**Test with custom repository root:**
```bash
curl -X POST "http://127.0.0.1:8000/scan/summary?repo_root=/path/to/repository"
```

**Test with custom repository root and output directory:**
```bash
curl -X POST "http://127.0.0.1:8000/scan/summary?repo_root=/path/to/repository&output_dir=output"
```

#### Using Swagger UI (Interactive Testing)

1. Navigate to http://127.0.0.1:8000/docs
2. Find the `POST /scan/summary` endpoint
3. Click "Try it out"
4. Enter your parameters:
   - `repo_root`: Path to the repository (default: ".")
   - `output_dir`: Output directory (default: "output")
5. Click "Execute" to see the response

#### Expected Response

The endpoint returns a JSON object containing:
- Repository summary statistics
- Counts by category, language, and file extension
- Total file counts and sizes
