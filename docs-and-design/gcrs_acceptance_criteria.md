# Repo Scanner — Acceptance Criteria (v1)

## 0. Purpose & Scope

**Repo Scanner** is a CLI tool that scans Git repositories to identify **technologies on a file-by-file basis**.

It produces:
- a stream of per-file technology detections (default),
- optional aggregate views (summary, BOM),
- SARIF output,
- persisted results in PostgreSQL for multi-team, multi-repo reporting.

The tool is offered by **SITM** and must be auditable, deterministic, and automation-friendly.

---

## 1. Tool Identity

### AC-1.1 Name
- The tool is named **Repo Scanner**.
- The CLI binary name is consistent (e.g., `repo-scanner`).
- Tool name and version are included in:
  - scan metadata,
  - SARIF output,
  - logs.

---

## 2. Repository Input & Scan Targeting

### AC-2.1 Repository sources
Repo Scanner supports:
- local Git repositories (filesystem path),
- remote Git repositories (HTTPS or SSH).

### AC-2.2 Authentication
- Remote access uses standard Git mechanisms:
  - SSH agent,
  - HTTPS tokens via environment variables,
  - Git credential helpers.
- Credentials must never be logged or written to output.

### AC-2.3 Branch specification
Users may explicitly specify a branch:

    --branch <branch-name>

### AC-2.4 Default branch behavior
- If `--branch` is not specified:
  - local repos: current checked-out branch,
  - remote repos: repository default branch.
- The resolved branch name is always recorded in scan metadata.

### AC-2.5 Revision resolution
- Every scan resolves to a specific commit SHA.
- Both values are recorded:
  - branch (human-facing intent),
  - revision (immutable commit SHA).

### AC-2.6 Precedence
- If both `--revision` (or `--ref`) and `--branch` are provided:
  - revision takes precedence,
  - branch is recorded if determinable,
  - behavior is logged.

---

## 3. Scan Metadata (First-Class, Separate Object)

### AC-3.1 Metadata emission
- Scan metadata is emitted as a **single standalone JSON object**.
- In streaming modes (e.g., JSONL), metadata **must be the first record**.

### AC-3.2 Required metadata fields
Scan metadata includes at minimum:
- type = "scan_metadata"
- scan_id
- tool_name = "Repo Scanner"
- tool_version
- timestamp (UTC, ISO-8601)
- team_id
- repo_id
- repo_display_name
- repo_description (nullable)
- repo_url (if available)
- branch
- revision (commit SHA)
- scan_config_hash

### AC-3.3 Propagation
Scan metadata is:
- persisted to the database,
- embedded in BOM exports,
- embedded in SARIF at the run level only,
- **not duplicated** on each file record.
---

## 4. Repository Identity

### AC-4.1 Repository identifiers
Each repository has:
- **repo_id** — system-generated, immutable
- **repo_display_name** — human-readable, unique per team
- **repo_description** — optional short free text

### AC-4.2 First-run definition
- repo_display_name and repo_description are defined on the **first scan only**.
- They are immutable for v1.
- Subsequent attempts to redefine them:
  - are ignored,
  - are logged as informational.

### AC-4.3 CLI flags
    --repo-name "Customer Billing Service"
    --repo-description "Handles invoicing and payments"

---

## 5. Default Output Behavior (File-by-File)

### AC-5.1 Default mode
    repo-scanner scan <repo>

Produces **file-by-file technology identification**.

### AC-5.2 Output formats
- text (default)
- jsonl (streaming)
- json (non-streaming)

### AC-5.3 Streaming guarantees
- stdout contains only JSON objects in jsonl mode
- logs never appear on stdout

---

## 6. File-by-File Detection Model

### AC-6.1 File record schema
Each file detection record includes:
- type = "file_detection"
- scan_id
- repo_id
- path
- file_kind (text | binary | unknown)
- extension
- language (nullable)
- technologies[]

### AC-6.2 Technology record
Each technology entry includes:
- tech_id (ALL CAPS)
- tech_name
- category (ALL CAPS)
- confidence (HIGH | MEDIUM | LOW)
- evidence[]

### AC-6.3 Evidence
Evidence entries include:
- type (FILENAME | CONTENT | STRUCTURE | DEPENDENCY | HEURISTIC)
- detail
- optional line/column info

### AC-6.4 Categories
Minimum categories:
- LANGUAGE
- FRAMEWORK
- BUILD
- DEPENDENCY_MANIFEST
- IAC
- CONTAINER
- CI_CD
- RUNTIME_PLATFORM

---

## 7. Technology & Rule Identification

### AC-7.1 Rule IDs
- Stable
- ALL CAPS
- Used across file output, DB, SARIF, and reports

Examples:
- TECH_IAC_TERRAFORM
- TECH_LANG_PYTHON
- TECH_CI_GITHUB_ACTIONS

### AC-7.2 Determinism
Same repo + revision + config yields identical results.

---

## 8. Logging

### AC-8.1 Log output
    --log-file <path>

### AC-8.2 Defaults
- logs → stderr
- scan output → stdout

### AC-8.3 Log content
Includes:
- timestamp
- log level
- scan_id
- repo_display_name
- repo_id

### AC-8.4 Persistence
- logs are file-only
- logs are not stored in DB
---

## 9. Database (PostgreSQL Only)

### AC-9.1 Supported DB
- PostgreSQL only

### AC-9.2 Container support
Documentation includes:
- docker run example
- docker-compose example

### AC-9.3 Connection handling
- configured via CLI or env vars
- validated at startup

---

## 10. Multi-Team & Multi-Repo Support

### AC-10.1 Teams
- multiple teams supported
- RBAC out of scope

### AC-10.2 Team requirement
- --team is required when writing to DB

---

## 11. SARIF Output

### AC-11.1 Generation
    --sarif-out <path>

### AC-11.2 Standard
- SARIF 2.1.0

### AC-11.3 Mapping
- one result per (file, technology)
- ruleId = tech_id

### AC-11.4 Metadata
- run-level only

---

## 12. BOM & Reporting

### AC-12.1 BOM
- derived
- optional
- not default

### AC-12.2 Reporting
- from DB or saved scans
- text, JSON, Markdown

---

## 13. Documentation

### AC-13.1 Quickstart
    repo-scanner scan .
    repo-scanner scan . --branch main
    repo-scanner scan . --format jsonl > scan.jsonl
    repo-scanner scan . --log-file scan.log
    repo-scanner scan . --write-db --team ACME --db postgres://...
    repo-scanner scan . --sarif-out results.sarif

---

## 14. Exit Codes

### AC-14.1 Success
- exit code 0

### AC-14.2 Failure
- invalid args
- repo access failure
- DB failure
- output write failure

---

## 15. v1 Guarantees

- File-by-file default
- Separate metadata object
- Branch + revision recorded
- PostgreSQL only
- Multi-team support
- Human repo name & description
- SARIF run-level metadata only
- ALL CAPS tech IDs
- File-based logging
- BOM is derived
