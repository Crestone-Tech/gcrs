# gcrs
Green Cloud Repository Scanner - scans a repository and generates a bill of materials (BOM)

## Setup

### Prerequisites
- Python 3.11 or higher
- pip
- Git (optional, but recommended for commit information in scan results)

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
3. Install the package and dependencies:
  
   ```bash
   pip install -e .
   ```
   
   This command installs the GCRS package in **editable mode** (also called "development mode"). Here's what it does:
   
   - **`-e`** (or `--editable`) - Installs the package in editable/development mode. This means:
     - Changes to the source code are immediately available without reinstalling
     - The package is linked to the source directory rather than copied
     - Perfect for development and testing
   
   - **`.`** - Refers to the current directory (the project root where `pyproject.toml` is located)
   
   - **What gets installed:**
     - The `gcrs` package itself (making the CLI `gcrs` command available)
     - All dependencies listed in `pyproject.toml` (FastAPI, uvicorn, pydantic, pathspec, etc.)
     - Console script entry points (the `gcrs` CLI command)
   
   After running this command, you can use:
   - The CLI: `gcrs scan .` or `gcrs summary .`
   - The API: `uvicorn gcrs.api.main:app --reload`
   - Python imports: `from gcrs.core.scanner import scan_repository`

## Command-Line Interface (CLI)

The GCRS CLI provides a convenient way to scan repositories and generate summaries directly from the command line, with support for piping output to other programs.

### Installation

After installing the package with `pip install -e .`, the CLI is available as the `gcrs` command. You can also run it directly as `python -m gcrs.cli`.

### Basic Usage

The CLI provides two main commands:

1. **`scan`** - Scans a repository and outputs detailed file records
2. **`summary`** - Generates a summary of repository contents

#### Scan Command

Scans a repository and outputs detailed information about each file.

```bash
# Basic usage - output to stdout (JSON format)
gcrs scan /path/to/repository

# Output to a file
gcrs scan /path/to/repository --output scan_results.json

# Use different output formats
gcrs scan /path/to/repository --format markdown
gcrs scan /path/to/repository --format csv
gcrs scan /path/to/repository --format sarif

# Short form options
gcrs scan . -f json -o results.json
```

#### Summary Command

Generates a high-level summary of repository contents.

```bash
# Basic usage - output to stdout (JSON format)
gcrs summary /path/to/repository

# Output to a file
gcrs summary /path/to/repository --output summary.md

# Use different output formats
gcrs summary /path/to/repository --format markdown
gcrs summary /path/to/repository --format csv

# Short form options
gcrs summary . -f markdown -o summary.md
```

### Command Options

Both commands support the following options:

| Option | Short Form | Description | Default |
|--------|------------|-------------|---------|
| `--format` | `-f` | Output format (see formats below) | `json` |
| `--output` | `-o` | Output file path (omit for stdout) | stdout |
| `--skip-dirs` | - | Additional directories to skip | `[]` |
| `--no-gitignore` | - | Disable .gitignore file respect | `false` |

### Output Formats

#### Scan Command Formats

- **`json`** - JSON array of file records (default)
- **`markdown`** - Markdown table format
- **`csv`** - Comma-separated values
- **`sarif`** - SARIF 2.1.0 format for static analysis tools

#### Summary Command Formats

- **`json`** - JSON object with repository statistics (default)
- **`markdown`** - Human-readable markdown format
- **`csv`** - CSV format with metrics and counts

### Examples

#### Basic Examples

```bash
# Generate summary of current directory
gcrs summary .

# Scan repository and save to file
gcrs scan /path/to/repo --output scan.json

# Generate markdown summary
gcrs summary . --format markdown --output README_SUMMARY.md
```

#### Piping and Redirection

The CLI is designed to work seamlessly with Unix pipes and redirection:

```bash
# Pipe JSON output to jq for filtering
gcrs summary . --format json | jq '.files_by_language'

# Pipe to another program
gcrs scan . --format csv | grep "python"

# Redirect to file
gcrs summary . > summary.json

# Suppress debug logs (redirect stderr)
gcrs summary . --format json 2>/dev/null | jq .

# Chain multiple commands
gcrs scan . --format json | jq '.[] | select(.language == "python")' | wc -l
```

#### Advanced Examples

```bash
# Skip additional directories
gcrs scan . --skip-dirs custom_dir build artifacts

# Disable .gitignore respect
gcrs scan . --no-gitignore

# Generate SARIF output for static analysis tools
gcrs scan . --format sarif --output results.sarif.json

# Combine options
gcrs summary /path/to/repo --format csv --skip-dirs node_modules dist --output summary.csv
```

#### Integration Examples

```bash
# Count Python files
gcrs scan . --format json 2>/dev/null | jq '[.[] | select(.language == "python")] | length'

# Find largest files
gcrs scan . --format json 2>/dev/null | jq 'sort_by(.size_bytes) | reverse | .[0:10]'

# Generate summary and extract specific metrics
gcrs summary . --format json 2>/dev/null | jq '{total: .total_files, languages: .files_by_language}'

# Export to CSV for spreadsheet analysis
gcrs scan . --format csv --output files.csv

# Generate SARIF for GitHub Code Scanning
gcrs scan . --format sarif --output code-scan-results.sarif.json
```

### Output to stdout vs Files

By default, the CLI outputs to **stdout**, making it easy to pipe to other programs:

```bash
# Output to stdout (can be piped)
gcrs summary . --format json

# Output to file
gcrs summary . --format json --output summary.json
```

**Note:** Debug logs are written to **stderr**, so they won't interfere with piping stdout to other programs. To suppress debug logs when piping, redirect stderr:

```bash
gcrs summary . --format json 2>/dev/null | jq .
```

### Error Handling

The CLI returns appropriate exit codes:

- **0** - Success
- **1** - Error (invalid path, scan failure, etc.)

Errors are printed to stderr, so they don't interfere with stdout output:

```bash
# Check exit code
gcrs summary /invalid/path
echo $?  # Prints 1

# Errors go to stderr, stdout remains clean for piping
gcrs summary /invalid/path 2>error.log | jq .  # stdout is empty, error in error.log
```

### Help

Get help for any command:

```bash
# General help
gcrs --help

# Command-specific help
gcrs scan --help
gcrs summary --help
```

### Comparison: CLI vs API

| Feature | CLI | API |
|---------|-----|-----|
| **Output Location** | stdout or file | File only |
| **Piping Support** | ✅ Yes | ❌ No |
| **Format Options** | All formats | All formats |
| **Integration** | Shell scripts, pipelines | HTTP clients, web apps |
| **Use Case** | Automation, CI/CD, local analysis | Web services, remote scanning |

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
| `output_file_format` | string | No | `"json"` | Format of the output file: `"json"` or `"markdown"` |

### Request Examples

#### Using curl

**Basic request with default parameters (scans current directory, outputs JSON):**
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
    "output_file_format": "json"
  }'
```

**Summarize repository with Markdown output:**
```bash
curl -X POST "http://127.0.0.1:8000/scan/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_root": "/path/to/repository",
    "output_file_format": "markdown"
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
        "output_file_format": "json"
    }
)

# Request with Markdown output format
response = requests.post(
    "http://127.0.0.1:8000/scan/summary",
    json={
        "repo_root": "/path/to/repository",
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

The summary is automatically written to a file in the `output` directory relative to the repository root:

- **JSON format**: Contains the repository summary as structured JSON data
- **Markdown format**: Contains a human-readable markdown table with the same information

The output file location will be: `{repo_root}/output/{repo_name}_{timestamp}.summary.{extension}`

The filename is automatically generated based on:
- Repository name (from `repo_root` path)
- Timestamp (YYYYMMDD_HHMMSS format)
- Operation type (`summary` or `scan`)
- File extension (based on `output_file_format`)

#### Example: JSON Output File

For a JSON output, the generated file (e.g., `sample_repo_20241210_143022.summary.json`) would contain:

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

For a Markdown output, the generated file (e.g., `sample_repo_20241210_143022.summary.md`) would contain:

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

## API Documentation: Repository Scans

The `/scan` endpoint scans a repository directory and generates detailed file records (Bill of Materials) for each file. The scan can be output in JSON, Markdown, CSV, or SARIF format.

### Endpoint Details

**URL:** `POST /scan`

**Request Body Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `repo_root` | string | No | `"."` | Path to the repository root directory to scan |
| `output_file_format` | string | No | `"json"` | Format of the output file: `"json"`, `"markdown"`, `"csv"`, or `"sarif"` |
| `skip_dirs` | array | No | `[]` | List of directories to skip during scanning |
| `respect_gitignore` | boolean | No | `true` | Whether to respect .gitignore files during scanning |

### FileRecord Structure

Each file in the scan output is represented as a `FileRecord` object with the following fields:

#### Required Identity Fields
- `name` (string): Filename (e.g., 'scanner.py')
- `relative_dir` (string): Directory path relative to repository root (e.g., 'src/utils')
- `absolute_filename` (string): Absolute filename path

#### Required Metadata Fields
- `most_recent_commit_date` (datetime | null): Date and time of the most recent Git commit that changed the file. ISO 8601 format when serialized to JSON (e.g., "2025-01-15T14:30:00"). `null` if the file is not tracked in Git or Git is unavailable.
- `most_recent_commit_hash` (string | null): SHA-1 hash of the most recent Git commit that changed the file (e.g., "a1b2c3d4e5f6789012345678901234567890abcd"). `null` if the file is not tracked in Git or Git is unavailable.
- `size_bytes` (integer): File size in bytes
- `is_binary` (boolean): `true` if the file is binary, `false` otherwise

#### Optional Classification Fields
- `extension` (string | null): File extension in lowercase (e.g., '.py', '.js')
- `category` (string | null): File category (e.g., 'code', 'config', 'documentation', 'data')
- `language` (string | null): Programming language detected (e.g., 'python', 'javascript')
- `data_type` (string | null): Data file type (e.g., 'csv', 'jsonl', 'xml', 'tsv', 'parquet', 'sqlite')
- `dependency_kind` (string | null): Dependency management system type (e.g., 'python-requirements', 'node-package')
- `technologies` (array): List of technologies detected (e.g., ['docker', 'kubernetes'])

### Git Commit Information

The scanner automatically retrieves Git commit information for files when:
- The repository is a Git repository (contains a `.git` directory)
- Git is installed and available in the system PATH
- The file is tracked in Git

**Note:** If Git is not available, the file is not tracked, or the repository is not a Git repository, both `most_recent_commit_date` and `most_recent_commit_hash` will be `null`. The scanner gracefully handles these cases without errors.

### Request Examples

#### Using curl

**Basic scan with JSON output:**
```bash
curl -X POST "http://127.0.0.1:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_root": "/path/to/repository",
    "output_file_format": "json"
  }'
```

**Scan with CSV output:**
```bash
curl -X POST "http://127.0.0.1:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_root": "/path/to/repository",
    "output_file_format": "csv"
  }'
```

### Response Format

The endpoint returns a JSON response with the following structure:

```json
{
  "status": "success",
  "error": null
}
```

The actual file records are written to an output file (see Output Files section below).

### Output Files

The file records are automatically written to a file in the `output` directory relative to the repository root:

- **JSON format**: Contains an array of FileRecord objects as structured JSON data
- **Markdown format**: Contains a human-readable markdown table
- **CSV format**: Contains comma-separated values
- **SARIF format**: Contains SARIF-formatted JSON for static analysis tools

The output file location will be: `{repo_root}/output/{repo_name}_{timestamp}.scan.{extension}`

#### Example: JSON Output File

For a JSON output, the generated file (e.g., `sample_repo_20241210_143022.scan.json`) would contain:

```json
[
  {
    "name": "scanner.py",
    "relative_dir": "gcrs/core",
    "absolute_filename": "/path/to/repository/gcrs/core/scanner.py",
    "most_recent_commit_date": "2025-01-15T14:30:00",
    "most_recent_commit_hash": "a1b2c3d4e5f6789012345678901234567890abcd",
    "size_bytes": 2048,
    "is_binary": false,
    "extension": ".py",
    "category": "code",
    "language": "python",
    "data_type": null,
    "dependency_kind": null,
    "technologies": []
  },
  {
    "name": "requirements.txt",
    "relative_dir": ".",
    "absolute_filename": "/path/to/repository/requirements.txt",
    "most_recent_commit_date": "2025-01-10T09:15:00",
    "most_recent_commit_hash": "b2c3d4e5f6789012345678901234567890abcdef",
    "size_bytes": 512,
    "is_binary": false,
    "extension": ".txt",
    "category": "config",
    "language": null,
    "data_type": null,
    "dependency_kind": "python-requirements",
    "technologies": []
  }
]
```

**Note:** Files that are not tracked in Git or when Git is unavailable will have `most_recent_commit_date` and `most_recent_commit_hash` set to `null`:

```json
{
  "name": "untracked_file.py",
  "relative_dir": ".",
  "absolute_filename": "/path/to/repository/untracked_file.py",
  "most_recent_commit_date": null,
  "most_recent_commit_hash": null,
  "size_bytes": 1024,
  "is_binary": false,
  "extension": ".py",
  "category": "code",
  "language": "python",
  "data_type": null,
  "dependency_kind": null,
  "technologies": []
}
```
