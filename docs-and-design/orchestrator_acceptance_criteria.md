# MSG Orchestrator Acceptance Criteria (v1)

## Purpose

The MSG Orchestrator coordinates repository scanning, analyzer invocation, and persistence of results for a single execution ("run").

## A) Run Identity and Timing

### AC-RUN-001 | Run UUID

- Each execution MUST generate a unique RUN_UUID.
- RUN_UUID MUST be included in:
  - logs
  - persisted records
  - output artifacts (including SARIF).

### AC-RUN-002 | Run Timestamps

- RUN_STARTED_AT MUST be captured at execution start.
- RUN_FINISHED_AT MUST be captured at execution end (success, partial success, or failure).

### AC-RUN-003 | Repeatability

- Given identical repo state, commit, config, and tool versions:
- Results MUST be equivalent except for: RUN_UUID, RUN_STARTED_AT, RUN_FINISHED_AT.

## B) Triggers and Entrypoints

### AC-TRIG-001 | Git Post-Commit Trigger

- Orchestrator MUST support a post-commit git hook.
- Default behavior is DELTA scan (commit-only).

### AC-TRIG-002 | Manual Scan

- Orchestrator MUST provide a manual CLI scan command.
- Manual scans MUST behave identically to hook-triggered scans.

### AC-TRIG-003 | Per-Repo Configuration

- Configuration MUST be supported per repository.
- Effective configuration (or config hash) MUST be recorded per run.

## C) Target Selection

### AC-TARGET-001 | Latest Default

- If no branch or commit is specified, scan latest commit on current branch.

### AC-TARGET-002 | Branch Selection

- If branch is specified, scan latest commit on that branch.
- Fail if branch cannot be resolved.

### AC-TARGET-003 | Commit UUID

- If commit UUID is specified, scan that exact commit.
- Fail if commit cannot be resolved.

## D) Scope Selection (Delta vs Full)

### AC-SCOPE-001 | Delta Default

- Default scan scope MUST be DELTA.
- DELTA means files changed by the specified commit only.

### AC-SCOPE-002 | Full Repo Scan

- When FULL is specified, the entire repository at the target commit MUST be scanned.

### AC-SCOPE-003 | Delta File Resolution

- In DELTA mode:
  - include added and modified files
  - exclude deleted files
  - treat renames as the new path
- The resolved delta file set MUST be reproducible.

## E) Repo Scanner Invocation (SITM)

### AC-RS-001 | Execution Order

- The SITM Repo Scanner MUST run before any analyzer is invoked.

### AC-RS-002 | Context Passed to Repo Scanner

- Repo identifier and name
- Branch
- Commit UUID
- Scan scope (DELTA or FULL)
- RUN_UUID (or correlation ID)

### AC-RS-003 | Scanner Failure Handling

- If Repo Scanner fails or output is invalid:
  - the run MUST be marked FAILED
  - diagnostics MUST be recorded
  - analyzers MUST NOT be invoked.

## F) Analyzer Selection and Execution

### AC-AN-001 | Technology-Based Selection

- Analyzers MUST be selected based on technology names returned by the Repo Scanner.

### AC-AN-002 | Analyzer Mapping Strategies

- Support either or both:
  1. config mapping: tech → executable
  2. container naming: tech → container name

### AC-AN-003 | Multi-Technology Handling

- Appropriate analyzers MUST be invoked for each applicable technology.

### AC-AN-004 | Analyzer Isolation

- Failure of one analyzer MUST NOT prevent execution of others.
- Per-analyzer status MUST be recorded.

### AC-AN-005 | Timeouts

- Each analyzer MUST support a configurable timeout.
- Timeouts MUST be recorded as failures.

### AC-AN-006 | Analyzer Metadata

- Record analyzer name (technology key).
- Record version or container image digest.
- Record analyzer start and stop timestamps.

## G) Results Normalization and Storage

### AC-RES-001 | No Deduplication Across Runs

- All issues found in every run MUST be stored.
- Issues MUST NOT be deduplicated across runs.

### AC-RES-002 | Required Issue Fields

Each issue MUST include at minimum:

- TEAM
- REPO ID and human-readable name
- RUN_UUID
- RUN_STARTED_AT and RUN_FINISHED_AT
- BRANCH
- COMMIT UUID
- FILE PATH
- RULE / Inefficiency ID (e.g., ECO-PY-001)
- LINE NUMBER
- SEVERITY
- CONFIDENCE
- MESSAGE
- REMEDIATION guidance
- Optional: column, category, snippet, analyzer source

### AC-RES-003 | Zero-Issue Runs

- Runs with zero findings MUST still:
  - create a run record
  - produce a valid merged SARIF with no results.

## H) Output Formats (SARIF)

### AC-OUT-001 | Merged SARIF Per Run

- The orchestrator MUST produce a single merged SARIF per run.
- SARIF MUST include RUN_UUID, commit, and branch metadata.

### AC-OUT-002 | SARIF Validity

- SARIF output MUST conform to the selected SARIF spec version.
- SARIF MUST identify each analyzer as a contributing tool.

### AC-OUT-003 | Output Destinations

- Results MUST be writable to:
  - file output
  - Postgres database
- Behavior when both are enabled MUST be documented.

## I) Persistence Requirements

### AC-DB-001 | Postgres Backend

- Postgres MUST be supported as the database backend.

### AC-DB-002 | Team Required

- TEAM is mandatory for all runs.
- Validation MUST fail before scanning if TEAM is missing.

### AC-DB-003 | Core Data Model

- A RUN record MUST be stored for each execution.
- ISSUE records MUST be linked to the RUN record.

### AC-DB-004 | Persistence Failure Behavior

- Persistence failures MUST mark the run as FAILED or PARTIAL.
- Errors MUST be logged and recorded with the run.

## J) CLI Requirements

### AC-CLI-001 | Scan Command

The CLI MUST provide a scan command supporting:

- `--team` (required)
- `--repo`
- `--branch`
- `--commit`
- `--full`
- `--output-file`
- `--db`
- `--log-file`

### AC-CLI-002 | Hook Management

- The CLI MUST support:
  - install-hook
  - uninstall-hook
- Hooks MUST be installed per repository by default.

### AC-CLI-003 | Exit Codes

- Exit codes MUST be deterministic and documented.
