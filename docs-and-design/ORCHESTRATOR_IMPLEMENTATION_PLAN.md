# Orchestrator Implementation Plan

## Overview

The Orchestrator is a **separate process** from GCRS that coordinates repository scanning, analyzer invocation, and persistence of results. This document outlines the implementation plan based on the acceptance criteria.

## Project Structure

Since the orchestrator is a separate process, it should live in its own folder:

```
gcrs_project/
├── gcrs/                    # Existing GCRS scanner
│   ├── api/
│   ├── core/
│   └── ...
├── orchestrator/            # NEW: Orchestrator module (separate process)
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── cli.py               # CLI interface
│   ├── orchestrator.py      # Main orchestrator class
│   ├── scheduler.py         # Scan scheduling
│   ├── config.py            # Configuration management
│   ├── models.py            # Data models
│   ├── hooks/               # Git hook management
│   │   ├── __init__.py
│   │   ├── git_hooks.py     # Git hook installation/management
│   │   └── post_commit.py   # Post-commit hook handler
│   ├── runners/             # Runner modules
│   │   ├── __init__.py
│   │   ├── gcrs_runner.py   # GCRS integration
│   │   ├── gcco_runner.py   # GCCO execution (future)
│   │   └── gcgm_runner.py   # GCGM execution (future)
│   ├── db/                  # Database operations
│   │   ├── __init__.py
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── services.py      # Database services
│   │   └── migrations/      # Alembic migrations
│   └── utils/               # Utilities
│       ├── __init__.py
│       ├── logging.py       # Logging setup
│       └── validators.py     # Validation utilities
├── docs-and-design/
└── ...
```

**Alternative Structure (if orchestrator becomes a separate package):**
```
gcrs_project/
├── gcrs/                    # GCRS scanner
├── orchestrator/            # Orchestrator (separate package)
│   ├── orchestrator/
│   │   └── ... (same structure as above)
│   ├── pyproject.toml       # Separate package config
│   └── README.md
└── ...
```

**Recommendation:** Start with the first structure (orchestrator as a module in the same repo), then extract to a separate package later if needed.

---

## Implementation Phases

### Phase 1: Foundation & Core Orchestrator (MVP)

#### 1.1 Project Setup

**Tasks:**
- [ ] Create `orchestrator/` directory structure
- [ ] Set up `__init__.py` files
- [ ] Create `orchestrator/pyproject.toml` or update root `pyproject.toml` with orchestrator entry points
- [ ] Add orchestrator dependencies to `requirements.txt` or `pyproject.toml`
- [ ] Set up logging infrastructure (`orchestrator/utils/logging.py`)
- [ ] Create configuration management (`orchestrator/config.py`)

**Dependencies:**
- `uuid` (standard library) - for RUN_UUID generation
- `datetime` (standard library) - for timestamps
- `httpx` or `requests` - for calling GCRS API
- `click` or `argparse` - for CLI
- `sqlalchemy` - for database (shared with GCRS)
- `psycopg2-binary` - for PostgreSQL (shared with GCRS)
- `pydantic` - for data validation
- `python-dotenv` - for environment variables

#### 1.2 Database Models & Schema

**Tasks:**
- [ ] Create `orchestrator/db/models.py` with SQLAlchemy models:
  - [ ] `Run` model (for `orchestration_run` table)
  - [ ] `ScanSchedule` model (for `scan_schedule` table)
  - [ ] `Rule` model (for `rule` table - Phase 1 MVP)
  - [ ] `Finding` model (for `finding` table - Phase 1 MVP)
- [ ] Create Alembic migration for new tables:
  - [ ] `orchestration_run` table
  - [ ] `scan_schedule` table
  - [ ] `rule` table (Phase 1)
  - [ ] `finding` table (Phase 1)
- [ ] Create `orchestrator/db/services.py` with database service functions
- [ ] Add database initialization function

**Database Tables (from ORCHESTRATOR_DESIGN.md):**
- `orchestration_run` - Tracks orchestration execution runs
- `scan_schedule` - Stores scan scheduling information
- `rule` - Rule metadata for GCCO (Phase 1 MVP)
- `finding` - Code inefficiency findings (Phase 1 MVP)

#### 1.3 Core Models & Types

**Tasks:**
- [ ] Create `orchestrator/models.py` with Pydantic models:
  - [ ] `RunIdentity` - RUN_UUID, timestamps
  - [ ] `ScanScope` - Enum (WHOLE_REPO, INCREMENTAL, PER_COMMIT)
  - [ ] `RunStatus` - Enum (PENDING, IN_PROGRESS, SUCCESS, FAILED, PARTIAL)
  - [ ] `ScanTrigger` - Enum (MANUAL, POST_COMMIT, SCHEDULED)
  - [ ] `ScanParams` - Parameters for scan execution
  - [ ] `RunConfig` - Run configuration
- [ ] Add validation logic for models

#### 1.4 GCRS Integration

**Tasks:**
- [ ] Create `orchestrator/runners/gcrs_runner.py`:
  - [ ] `GCRSRunner` class
  - [ ] `invoke_scan()` method - calls GCRS API or CLI
  - [ ] `invoke_summary()` method - calls GCRS summary API
  - [ ] Support for scan scopes:
    - [ ] Whole repo scan
    - [ ] Incremental scan (since datetime) - requires GCRS enhancement
    - [ ] Per commit scan - requires GCRS enhancement
  - [ ] Error handling and retries
- [ ] Add GCRS API client or subprocess execution
- [ ] Handle GCRS response parsing
- [ ] Link scan results to BOM in database

**Integration Options:**
1. **API-based**: Call GCRS FastAPI endpoints (recommended for production)
2. **CLI-based**: Execute `gcrs` CLI command via subprocess (simpler for MVP)
3. **Library-based**: Import GCRS functions directly (tightest coupling)

**Recommendation:** Start with CLI-based for MVP, migrate to API-based later.

#### 1.5 Core Orchestrator Class

**Tasks:**
- [ ] Create `orchestrator/orchestrator.py`:
  - [ ] `Orchestrator` class
  - [ ] `execute_run()` method - main execution flow
  - [ ] `generate_run_uuid()` method - AC-RUN-001
  - [ ] `capture_timestamps()` method - AC-RUN-002
  - [ ] `execute_scan_workflow()` method - coordinates scan execution
  - [ ] Error handling and status tracking
- [ ] Implement run identity generation (RUN_UUID)
- [ ] Implement timestamp capture (RUN_STARTED_AT, RUN_FINISHED_AT)
- [ ] Implement repeatability logic (AC-RUN-003)

#### 1.6 CLI Interface

**Tasks:**
- [ ] Create `orchestrator/cli.py`:
  - [ ] `scan` command - AC-CLI-001
    - [ ] `--team` (required) - AC-DB-002
    - [ ] `--repo` - repository path or identifier
    - [ ] `--branch` - AC-TARGET-002
    - [ ] `--commit` - AC-TARGET-003
    - [ ] `--full` - AC-SCOPE-002 (default: DELTA - AC-SCOPE-001)
    - [ ] `--output-file` - SARIF output file path
    - [ ] `--db` - enable database persistence
    - [ ] `--log-file` - log file path
  - [ ] `install-hook` command - AC-CLI-002
  - [ ] `uninstall-hook` command - AC-CLI-002
  - [ ] Exit codes - AC-CLI-003
- [ ] Add CLI help text and documentation
- [ ] Implement argument validation

#### 1.7 Git Hook Management

**Tasks:**
- [ ] Create `orchestrator/hooks/git_hooks.py`:
  - [ ] `install_hook()` function - installs post-commit hook
  - [ ] `uninstall_hook()` function - removes hook
  - [ ] `validate_hook()` function - validates hook installation
- [ ] Create `orchestrator/hooks/post_commit.py`:
  - [ ] Post-commit hook script/template
  - [ ] Hook execution logic
  - [ ] Default DELTA scan behavior - AC-TRIG-001
- [ ] Support per-repository hook installation - AC-CLI-002

#### 1.8 Target Selection

**Tasks:**
- [ ] Implement target selection logic in `orchestrator/orchestrator.py`:
  - [ ] `resolve_target()` method:
    - [ ] Latest default - AC-TARGET-001 (current branch, latest commit)
    - [ ] Branch selection - AC-TARGET-002
    - [ ] Commit UUID - AC-TARGET-003
  - [ ] Git operations for commit/branch resolution
  - [ ] Error handling for invalid branches/commits

#### 1.9 Scope Selection (Delta vs Full)

**Tasks:**
- [ ] Implement scope selection in `orchestrator/orchestrator.py`:
  - [ ] `resolve_scan_scope()` method:
    - [ ] DELTA default - AC-SCOPE-001
    - [ ] FULL scan option - AC-SCOPE-002
  - [ ] Delta file resolution - AC-SCOPE-003:
    - [ ] Include added and modified files
    - [ ] Exclude deleted files
    - [ ] Handle renames (treat as new path)
  - [ ] Git diff operations for delta resolution
  - [ ] Reproducible delta file set

#### 1.10 Run Execution Flow

**Tasks:**
- [ ] Implement complete run execution in `orchestrator/orchestrator.py`:
  - [ ] `execute_run()` workflow:
    1. Generate RUN_UUID
    2. Capture RUN_STARTED_AT
    3. Validate TEAM (required) - AC-DB-002
    4. Resolve target (branch/commit)
    5. Resolve scan scope (DELTA/FULL)
    6. Invoke GCRS scanner - AC-RS-001, AC-RS-002
    7. Handle scanner failures - AC-RS-003
    8. Capture RUN_FINISHED_AT
    9. Update run status
  - [ ] Error handling and status updates
  - [ ] Logging with RUN_UUID correlation

#### 1.11 Results Persistence

**Tasks:**
- [ ] Implement results persistence in `orchestrator/db/services.py`:
  - [ ] `create_run()` - create orchestration_run record
  - [ ] `update_run_status()` - update run status
  - [ ] `persist_run_config()` - store run configuration
  - [ ] Link to BOM from GCRS scan
- [ ] Ensure all issues are stored (no deduplication) - AC-RES-001
- [ ] Handle zero-issue runs - AC-RES-003

#### 1.12 SARIF Output Generation

**Tasks:**
- [ ] Create `orchestrator/output/sarif_generator.py`:
  - [ ] `generate_sarif()` function - AC-OUT-001
  - [ ] Include RUN_UUID, commit, branch metadata - AC-OUT-001
  - [ ] SARIF spec compliance - AC-OUT-002
  - [ ] Tool identification - AC-OUT-002
- [ ] Support file output - AC-OUT-003
- [ ] Support database storage (optional) - AC-OUT-003

#### 1.13 Configuration Management

**Tasks:**
- [ ] Create `orchestrator/config.py`:
  - [ ] `OrchestratorConfig` class
  - [ ] Per-repo configuration support - AC-TRIG-003
  - [ ] Configuration hash calculation
  - [ ] Configuration validation
- [ ] Support configuration files (YAML/JSON)
- [ ] Environment variable support

#### 1.14 Testing

**Tasks:**
- [ ] Create `tests/orchestrator/` directory
- [ ] Unit tests:
  - [ ] Run UUID generation
  - [ ] Timestamp capture
  - [ ] Target resolution
  - [ ] Scope resolution
  - [ ] Configuration management
- [ ] Integration tests:
  - [ ] End-to-end run execution
  - [ ] GCRS integration
  - [ ] Database persistence
  - [ ] Git hook installation
- [ ] Test fixtures and mocks

---

### Phase 2: Analyzer Integration (GCCO - MVP)

#### 2.1 GCCO Foundation

**Tasks:**
- [ ] Create `orchestrator/runners/gcco_runner.py`:
  - [ ] `GCCORunner` class
  - [ ] Rule loading from configuration
  - [ ] Pattern module execution
  - [ ] Findings generation
- [ ] Create rule configuration system
- [ ] Implement pattern module interface
- [ ] Add AST parsing support

#### 2.2 Technology-Based Analyzer Selection

**Tasks:**
- [ ] Implement analyzer selection logic - AC-AN-001:
  - [ ] Map technologies from GCRS scan to analyzers
  - [ ] Support config mapping - AC-AN-002
  - [ ] Support container naming - AC-AN-002
- [ ] Multi-technology handling - AC-AN-003
- [ ] Analyzer isolation - AC-AN-004 (failures don't block others)

#### 2.3 Analyzer Execution

**Tasks:**
- [ ] Implement analyzer execution:
  - [ ] Per-analyzer status tracking - AC-AN-004
  - [ ] Timeout support - AC-AN-005
  - [ ] Analyzer metadata recording - AC-AN-006
- [ ] Error handling and logging

---

### Phase 3: Advanced Features

#### 3.1 Scan Scheduling

**Tasks:**
- [ ] Create `orchestrator/scheduler.py`:
  - [ ] Cron-like scheduling
  - [ ] Event-driven scheduling
  - [ ] Schedule management
- [ ] Background task execution
- [ ] Schedule persistence

#### 3.2 Retry Logic

**Tasks:**
- [ ] Implement retry mechanism:
  - [ ] Configurable max retries
  - [ ] Exponential backoff
  - [ ] Retry queue management

#### 3.3 Per-Repo Configuration

**Tasks:**
- [ ] Enhanced configuration system:
  - [ ] Per-repo config files
  - [ ] Config versioning
  - [ ] Config hash tracking - AC-TRIG-003

---

### Phase 4: GCGM Integration (Future)

#### 4.1 GCGM Foundation

**Tasks:**
- [ ] Create `orchestrator/runners/gcgm_runner.py`
- [ ] Cost estimation logic
- [ ] Jira integration
- [ ] Performance testing

---

## Acceptance Criteria Mapping

### A) Run Identity and Timing

- **AC-RUN-001 | Run UUID**: ✅ Phase 1.5
- **AC-RUN-002 | Run Timestamps**: ✅ Phase 1.5
- **AC-RUN-003 | Repeatability**: ✅ Phase 1.5

### B) Triggers and Entrypoints

- **AC-TRIG-001 | Git Post-Commit Trigger**: ✅ Phase 1.7
- **AC-TRIG-002 | Manual Scan**: ✅ Phase 1.6
- **AC-TRIG-003 | Per-Repo Configuration**: ✅ Phase 1.13, Phase 3.3

### C) Target Selection

- **AC-TARGET-001 | Latest Default**: ✅ Phase 1.8
- **AC-TARGET-002 | Branch Selection**: ✅ Phase 1.8
- **AC-TARGET-003 | Commit UUID**: ✅ Phase 1.8

### D) Scope Selection

- **AC-SCOPE-001 | Delta Default**: ✅ Phase 1.9
- **AC-SCOPE-002 | Full Repo Scan**: ✅ Phase 1.9
- **AC-SCOPE-003 | Delta File Resolution**: ✅ Phase 1.9

### E) Repo Scanner Invocation

- **AC-RS-001 | Execution Order**: ✅ Phase 1.10
- **AC-RS-002 | Context Passed**: ✅ Phase 1.4
- **AC-RS-003 | Scanner Failure Handling**: ✅ Phase 1.10

### F) Analyzer Selection and Execution

- **AC-AN-001 | Technology-Based Selection**: ✅ Phase 2.2
- **AC-AN-002 | Analyzer Mapping**: ✅ Phase 2.2
- **AC-AN-003 | Multi-Technology**: ✅ Phase 2.2
- **AC-AN-004 | Analyzer Isolation**: ✅ Phase 2.3
- **AC-AN-005 | Timeouts**: ✅ Phase 2.3
- **AC-AN-006 | Analyzer Metadata**: ✅ Phase 2.3

### G) Results Normalization and Storage

- **AC-RES-001 | No Deduplication**: ✅ Phase 1.11
- **AC-RES-002 | Required Issue Fields**: ✅ Phase 2.1 (GCCO findings)
- **AC-RES-003 | Zero-Issue Runs**: ✅ Phase 1.11

### H) Output Formats (SARIF)

- **AC-OUT-001 | Merged SARIF**: ✅ Phase 1.12
- **AC-OUT-002 | SARIF Validity**: ✅ Phase 1.12
- **AC-OUT-003 | Output Destinations**: ✅ Phase 1.12

### I) Persistence Requirements

- **AC-DB-001 | Postgres Backend**: ✅ Phase 1.2 (shared with GCRS)
- **AC-DB-002 | Team Required**: ✅ Phase 1.10
- **AC-DB-003 | Core Data Model**: ✅ Phase 1.2
- **AC-DB-004 | Persistence Failure**: ✅ Phase 1.11

### J) CLI Requirements

- **AC-CLI-001 | Scan Command**: ✅ Phase 1.6
- **AC-CLI-002 | Hook Management**: ✅ Phase 1.7
- **AC-CLI-003 | Exit Codes**: ✅ Phase 1.6

---

## Dependencies on GCRS

The orchestrator depends on GCRS enhancements:

1. **Scan Scope Support** (from `GCRS_SCAN_SCOPE_TODO.md`):
   - Incremental scan (since datetime) - Required for Phase 1.4
   - Per-commit scan - Required for Phase 1.4
   - These are tracked separately in `GCRS_SCAN_SCOPE_TODO.md`

2. **API/CLI Interface**:
   - GCRS API endpoints for scan execution
   - Or GCRS CLI for subprocess execution

3. **Database Schema**:
   - Shared database with GCRS
   - Orchestrator adds new tables but uses existing GCRS tables (repo, bom, etc.)

---

## Configuration Files

### orchestrator/config.yaml (example)

```yaml
orchestrator:
  database:
    url: ${DATABASE_URL}
  
  gcrs:
    api_url: "http://localhost:8000"  # If using API
    cli_path: "gcrs"  # If using CLI
    timeout_seconds: 300
  
  logging:
    level: "INFO"
    file: "orchestrator.log"
    format: "json"
  
  runs:
    default_team: null  # Must be provided per run
    default_scope: "delta"
    max_retries: 3
  
  hooks:
    enabled: true
    install_path: ".git/hooks"
  
  output:
    sarif_version: "2.1.0"
    default_output_dir: "./output"
```

### Per-Repo Configuration (orchestrator/.orchestrator.yaml)

```yaml
team: "engineering"
repo_id: 123
scan_schedule:
  type: "cron"
  expression: "0 0 * * *"  # Daily at midnight
analyzer_config:
  enabled_analyzers: ["python", "javascript"]
  timeout_seconds: 600
```

---

## Entry Points

### CLI Entry Point

```bash
# Install orchestrator
pip install -e .

# Run scan
orchestrator scan --team engineering --repo /path/to/repo

# Install git hook
orchestrator install-hook --repo /path/to/repo

# Uninstall git hook
orchestrator uninstall-hook --repo /path/to/repo
```

### Python API Entry Point

```python
from orchestrator import Orchestrator

orchestrator = Orchestrator(config_path="config.yaml")
run_id = orchestrator.execute_scan_workflow(
    repo_path="/path/to/repo",
    team="engineering",
    scope="delta",
    commit_hash="abc123"
)
```

---

## Testing Strategy

### Unit Tests
- Run UUID generation
- Timestamp capture
- Target resolution
- Scope resolution
- Configuration parsing
- Model validation

### Integration Tests
- End-to-end run execution
- GCRS integration (mock or real)
- Database persistence
- Git hook installation
- SARIF generation

### End-to-End Tests
- Complete workflow: trigger → scan → analyze → persist → output
- Multiple scan scopes
- Error scenarios
- Zero-issue runs

---

## Migration Path

### From GCRS to Orchestrator

1. **Phase 1**: Orchestrator calls GCRS as external service (CLI or API)
2. **Phase 2**: Tighten integration, shared database
3. **Phase 3**: Optional: Extract to separate package/repo

---

## Open Questions

1. **Orchestrator Package Structure**: Should orchestrator be a separate Python package or a module in the same repo?
   - **Recommendation**: Start as module, extract later if needed

2. **GCRS Integration Method**: API, CLI, or library import?
   - **Recommendation**: Start with CLI for MVP, migrate to API for production

3. **Database Sharing**: Same database instance or separate?
   - **Recommendation**: Same database, separate schemas or shared tables

4. **Configuration Management**: Centralized config or per-repo?
   - **Recommendation**: Both - centralized defaults, per-repo overrides

5. **Error Handling Strategy**: Fail fast or continue on errors?
   - **Recommendation**: Configurable - default to continue with logging

---

## Next Steps

1. **Review and approve this implementation plan**
2. **Set up orchestrator directory structure**
3. **Begin Phase 1.1: Project Setup**
4. **Coordinate with GCRS scan scope enhancements** (incremental, per-commit)

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-16  
**Status:** Planning Phase

