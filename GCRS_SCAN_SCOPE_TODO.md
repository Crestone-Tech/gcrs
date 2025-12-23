# GCRS Scan Scope Enhancements - TODO List

This document tracks the implementation of scan scope features for GCRS, as required by the Orchestrator module.

## Overview

GCRS currently supports whole repository scans (baseline). The Orchestrator requires three scan scopes:
1. **Whole Repo (Baseline)** - Already implemented ✅
2. **Incremental (Since Datetime)** - Files modified since a given datetime
3. **Per Commit** - Files changed in a specific commit

## Implementation Tasks

### 1. Incremental Scan (Since Datetime)

#### Models & Types
- [ ] Add `since_datetime: datetime | None` field to `ScanParams` model (`gcrs/models.py`)
- [ ] Add validation for `since_datetime` (must be in the past)
- [ ] Update `ScanOptions` model if needed

#### Core Scanner Logic
- [ ] Add `since_datetime` parameter to `do_the_repo_scan()` function (`gcrs/core/scanner.py`)
- [ ] Add `since_datetime` parameter to `scan_repository()` function
- [ ] Add `since_datetime` parameter to `summarize_repo_contents()` function
- [ ] Implement filtering logic:
  - After getting commit info for files, filter files where `most_recent_commit_date >= since_datetime`
  - Handle files with `None` commit dates (include or exclude based on requirement)
- [ ] Update function docstrings

#### API Integration
- [ ] Update `/scan` API endpoint to accept `since_datetime` parameter (`gcrs/api/main.py`)
- [ ] Update `/scan/summary` API endpoint to accept `since_datetime` parameter
- [ ] Add parameter validation and error handling

#### CLI Integration
- [ ] Add `--since-datetime` or `--since` option to `gcrs scan` command (`gcrs/cli.py`)
- [ ] Add `--since-datetime` or `--since` option to `gcrs summary` command
- [ ] Parse datetime from command line (support ISO 8601 format)
- [ ] Update CLI help text

#### Database Integration
- [ ] Update `persist_scan_results()` to store `since_datetime` in `scan_config` JSONB field
- [ ] Ensure `scan_config` includes scan scope information

#### Testing
- [ ] Unit tests for incremental scan filtering logic
- [ ] Integration tests for incremental scan with various datetime values
- [ ] Test edge cases:
  - `since_datetime` in the future (should error)
  - `since_datetime` before any commits (should include all files)
  - Files with no commit date
- [ ] Test with API endpoints
- [ ] Test with CLI commands

#### Documentation
- [ ] Update README.md with incremental scan usage examples
- [ ] Update API documentation
- [ ] Add examples for incremental scan use cases

---

### 2. Per Commit Scan

#### Models & Types
- [ ] Add `commit_hash: str | None` field to `ScanParams` model (`gcrs/models.py`)
- [ ] Add validation for `commit_hash` (must be valid 40-character SHA-1 hash)
- [ ] Update `ScanOptions` model if needed

#### Core Scanner Logic
- [ ] Add `commit_hash` parameter to `do_the_repo_scan()` function (`gcrs/core/scanner.py`)
- [ ] Add `commit_hash` parameter to `scan_repository()` function
- [ ] Add `commit_hash` parameter to `summarize_repo_contents()` function
- [ ] Implement per-commit scan logic:
  - Use `git diff --name-only <commit_hash>^..<commit_hash>` to get changed files
  - Or use `git show --name-only --pretty=format: <commit_hash>` to get changed files
  - Checkout files at that commit state (or use git show to read file content)
  - Scan only those files
  - Ensure commit exists in repository (validate)
- [ ] Handle edge cases:
  - First commit (no parent)
  - Merge commits (multiple parents)
  - Invalid commit hash
- [ ] Update function docstrings

#### Git Utilities
- [ ] Create helper function `get_files_changed_in_commit(repo_root: Path, commit_hash: str) -> list[Path]`
- [ ] Create helper function `get_file_content_at_commit(repo_root: Path, file_path: Path, commit_hash: str) -> str`
- [ ] Create helper function `validate_commit_hash(repo_root: Path, commit_hash: str) -> bool`
- [ ] Add error handling for git operations

#### API Integration
- [ ] Update `/scan` API endpoint to accept `commit_hash` parameter (`gcrs/api/main.py`)
- [ ] Update `/scan/summary` API endpoint to accept `commit_hash` parameter
- [ ] Add parameter validation and error handling
- [ ] Return appropriate error if commit doesn't exist

#### CLI Integration
- [ ] Add `--commit` or `--commit-hash` option to `gcrs scan` command (`gcrs/cli.py`)
- [ ] Add `--commit` or `--commit-hash` option to `gcrs summary` command
- [ ] Validate commit hash format
- [ ] Update CLI help text

#### Database Integration
- [ ] Update `persist_scan_results()` to store `commit_hash` in `scan_config` JSONB field
- [ ] Link scan to specific commit in `bom_commits` table
- [ ] Ensure proper commit tracking

#### Testing
- [ ] Unit tests for per-commit scan logic
- [ ] Unit tests for git helper functions
- [ ] Integration tests for per-commit scan with various commits
- [ ] Test edge cases:
  - First commit (no parent)
  - Merge commits
  - Invalid commit hash
  - Commit with no file changes
  - Large commits (many files)
- [ ] Test with API endpoints
- [ ] Test with CLI commands

#### Documentation
- [ ] Update README.md with per-commit scan usage examples
- [ ] Update API documentation
- [ ] Add examples for per-commit scan use cases

---

### 3. Scan Scope Validation & Mutual Exclusivity

#### Logic
- [ ] Ensure `since_datetime` and `commit_hash` are mutually exclusive
- [ ] Add validation in `ScanParams` model to enforce mutual exclusivity
- [ ] Default behavior: whole repo scan if neither parameter is provided
- [ ] Update error messages for invalid combinations

#### Testing
- [ ] Test that providing both `since_datetime` and `commit_hash` raises validation error
- [ ] Test that providing neither uses default (whole repo) behavior

---

### 4. Integration with Orchestrator

#### Orchestrator Interface
- [ ] Ensure orchestrator can call GCRS with all three scan scopes
- [ ] Verify scan scope parameters are properly passed through
- [ ] Test orchestrator → GCRS integration

---

## Implementation Notes

### Scan Scope Enum (Optional)

Consider creating a `ScanScope` enum for type safety:

```python
from enum import Enum

class ScanScope(str, Enum):
    WHOLE_REPO = "whole_repo"
    INCREMENTAL = "incremental"
    PER_COMMIT = "per_commit"
```

### Performance Considerations

- **Incremental Scan**: Filtering by commit date should be efficient (already have commit info)
- **Per Commit Scan**: Git operations may be slower; consider caching
- Both scopes should be faster than whole repo scans (fewer files)

### Backward Compatibility

- All new parameters should be optional
- Default behavior (whole repo scan) must remain unchanged
- Existing API calls and CLI commands should continue to work

---

## Priority

1. **High Priority**: Incremental scan (needed for scheduled scans)
2. **High Priority**: Per commit scan (needed for commit-level analysis)
3. **Medium Priority**: Validation and error handling
4. **Low Priority**: Performance optimizations

---

## Related Documentation

- See `ORCHESTRATOR_DESIGN.md` for orchestrator requirements
- See `DATABASE_DESIGN.md` for database schema
- See `README.md` for current GCRS usage

---

**Last Updated:** 2025-01-16  
**Status:** Planning Phase


