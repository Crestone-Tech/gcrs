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
   
   uvicorn gcrs.api.main:app --reload
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
- `GET /healthz` - Health check endpoint
- `POST /scan/summary` - Generate a summary of repository contents
- `POST /scan` - Scan a repository and generate a BOM

## API Documentation: Summary Scans

The `/scan/summary` endpoint scans a repository directory and generates a comprehensive summary of its contents. The summary can be output in JSON or Markdown format.

### Endpoint Details

**URL:** `POST /scan/summary`

**Request Body Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `repo_root` | string | No | `"."` | Path to the repository root directory to scan |
| `output_dir` | string | No | `"output"` | Directory relative to `repo_root` where the output file will be written |
| `output_file` | string | No | Auto-generated | Optional filename for the summary file. If not provided, generates a default name based on repository name and timestamp |
| `output_file_format` | string | No | `"markdown"` | Format of the output file: `"json"` or `"markdown"` |

### Request Examples

#### Using curl

**Basic request with default parameters (scans current directory, outputs markdown):**
```bash
curl -X POST "http://127.0.0.1:8000/scan/summary" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Scan specific repository with JSON output:**
```bash
curl -X POST "http://127.0.0.1:8000/scan/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_root": "/path/to/repository",
    "output_dir": "output",
    "output_file": "summary.json",
    "output_file_format": "json"
  }'
```

**Summarize repository with Markdown output:**
```bash
curl -X POST "http://127.0.0.1:8000/scan/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_root": "/path/to/repository",
    "output_dir": "output",
    "output_file": "summary.md",
    "output_file_format": "markdown"
  }'
```

**Summarize repository with custom output directory:**
```bash
curl -X POST "http://127.0.0.1:8000/scan/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_root": ".",
    "output_dir": "reports",
    "output_file": "repo_summary.md"
  }'
```

#### Using Python requests

```python
import requests

# Basic request with default parameters
response = requests.post(
    "http://127.0.0.1:8000/scan/summary",
    json={}
)

# Request with JSON output format
response = requests.post(
    "http://127.0.0.1:8000/scan/summary",
    json={
        "repo_root": "/path/to/repository",
        "output_dir": "output",
        "output_file": "summary.json",
        "output_file_format": "json"
    }
)

# Request with Markdown output format
response = requests.post(
    "http://127.0.0.1:8000/scan/summary",
    json={
        "repo_root": "/path/to/repository",
        "output_dir": "output",
        "output_file": "summary.md",
        "output_file_format": "markdown"
    }
)

data = response.json()
print(f"Status: {data['status']}")
print(f"Files scanned: {data['files_scanned']}")
```

#### Using JavaScript/Node.js (fetch)

```javascript
// Basic request
const response = await fetch('http://127.0.0.1:8000/scan/summary', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({})
});

// Request with JSON output
const response = await fetch('http://127.0.0.1:8000/scan/summary', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    repo_root: '/path/to/repository',
    output_dir: 'output',
    output_file: 'summary.json',
    output_file_format: 'json'
  })
});

const data = await response.json();
console.log(`Status: ${data.status}`);
console.log(`Files scanned: ${data.files_scanned}`);
```

### Response Format

The endpoint returns a JSON response with the following structure:

```json
{
  "status": "success",
  "summary": null,
  "repository_summary": {
    "files_by_language": {
      "python": 50,
      "javascript": 30,
      "typescript": 20
    },
    "files_by_category": {
      "code": 80,
      "config": 10,
      "documentation": 5,
      "data": 8
    },
    "files_by_technology": {
      "Docker": 3,
      "Kubernetes": 2,
      "Python": 4
    },
    "files_by_dependency": {
      "python-requirements": 1,
      "node-package": 1
    },
    "files_by_extension": {
      ".py": 50,
      ".js": 30,
      ".md": 5
    },
    "binary_files_by_extension": {
      ".png": 10,
      ".jpg": 5
    },
    "files_without_extension": 3,
    "files_with_extension": 147,
    "data_files_by_extension": {
      "csv": 5,
      "jsonl": 2
    },
    "total_files": 150,
    "scanned_files": 145,
    "skipped_files": 5
  },
  "repo_root": "/absolute/path/to/repository",
  "files_scanned": 145,
  "files_skipped": 5,
  "error": null
}
```

### Output Files

The summary is written to a file in the specified `output_dir` directory:

- **JSON format**: Contains the repository summary as structured JSON data
- **Markdown format**: Contains a human-readable markdown table with the same information

The output file location will be: `{repo_root}/{output_dir}/{output_file}`

#### Example: JSON Output File

For the JSON example above, the output file `summary.json` would contain:

```json
{
  "files_by_language": {
    "python": 50,
    "javascript": 30,
    "typescript": 20
  },
  "files_by_category": {
    "code": 80,
    "config": 10,
    "documentation": 5,
    "data": 8
  },
  "files_by_technology": {
    "Docker": 3,
    "Kubernetes": 2,
    "Python": 4
  },
  "files_by_dependency": {
    "python-requirements": 1,
    "node-package": 1
  },
  "files_by_extension": {
    ".py": 50,
    ".js": 30,
    ".md": 5
  },
  "binary_files_by_extension": {
    ".png": 10,
    ".jpg": 5
  },
  "files_without_extension": 3,
  "files_with_extension": 147,
  "data_files_by_extension": {
    "csv": 5,
    "jsonl": 2
  },
  "total_files": 150,
  "scanned_files": 145,
  "skipped_files": 5
}
```

#### Example: Markdown Output File

For the same repository, when using `"output_file_format": "markdown"`, the output file `summary.md` would contain:

```markdown
# Repository Summary
## Total Files: 150
## Scanned Files: 145
## Skipped Files: 5
## Files without Extension: 3
## Files with Extension: 147
## Files by Language:
  - python: 50
  - javascript: 30
  - typescript: 20
## Files by Category:
  - code: 80
  - config: 10
  - documentation: 5
  - data: 8
## Files by Technology:
  - Docker: 3
  - Kubernetes: 2
  - Python: 4
## Files by Dependency:
  - python-requirements: 1
  - node-package: 1
## Files by Extension:
  - .py: 50
  - .js: 30
  - .md: 5
## Binary Files by Extension:
  - .png: 10
  - .jpg: 5
## Data Files by Extension:
  - csv: 5
  - jsonl: 2
```

### Error Responses

If an error occurs, the response will have `status: "error"` and include an `error` field:

```json
{
  "status": "error",
  "error": "The specified repository root directory does not exist or is not a directory",
  "repo_root": "/invalid/path"
}
```

### Using Swagger UI (Interactive Testing)

1. Navigate to http://127.0.0.1:8000/docs
2. Find the `POST /scan/summary` endpoint
3. Click "Try it out"
4. Enter your parameters in the request body JSON editor
5. Click "Execute" to see the response

### Summary Contents

The summary includes:
- Total number of files scanned and skipped
- Number of files by programming language (Python, JavaScript, etc.)
- Number of files by category (code, config, documentation, data, etc.)
- Number of files by technology (Docker, Kubernetes, Terraform, etc.)
- Number of files by dependency management system
- Number of files by file extension
- Number of binary files by extension
- Number of data files by extension
- Counts of files with and without extensions
