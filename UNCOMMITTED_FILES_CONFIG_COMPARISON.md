# Configuration Approach Comparison: Uncommitted Files Handling

## Overview
This document compares two approaches for configuring how the scanner handles files without commit hashes (uncommitted/untracked files).

## Approach 1: Parameters (ScanParams)

### Implementation
Add fields to `ScanParams` model:
```python
strict_uncommitted_files: bool = Field(
    default=False,
    description="If True, fail scan when any files lack commit hashes"
)
warn_on_uncommitted_files: bool = Field(
    default=True,
    description="If True, log warnings for files without commit hashes"
)
```

### Pros
1. **Explicit and Clear**
   - Behavior is visible in API requests/responses
   - Self-documenting in OpenAPI schema
   - Easy to see what's being used in logs/debugging

2. **Per-Scan Control**
   - Different scans can have different policies
   - Easy to override for specific use cases
   - Flexible for CI/CD vs development scenarios

3. **No File Management**
   - No need to create/manage config files
   - No file path resolution issues
   - No config file versioning concerns

4. **API-Friendly**
   - Natural fit for REST API
   - Easy to pass via JSON
   - Works well with CLI arguments

5. **Type Safety**
   - Pydantic validation
   - IDE autocomplete support
   - Compile-time checking

6. **Simple Implementation**
   - Just add fields to existing model
   - No file parsing logic needed
   - No config file discovery/search

### Cons
1. **Verbosity**
   - Must specify in every API call
   - CLI commands get longer
   - More parameters to remember

2. **No Persistent Defaults**
   - Can't set project-wide defaults
   - Must remember to set each time
   - Harder to enforce team policies

3. **Repetition**
   - Same values passed repeatedly
   - Can't set once and forget
   - More error-prone (typos, etc.)

4. **Less Convenient for Teams**
   - Each developer must know/remember settings
   - Can't standardize across team easily
   - Harder to enforce organizational policies

## Approach 2: Config File (e.g., `.gcrs.yaml` or `gcrs.toml`)

### Implementation
Create config file in repo root:
```yaml
# .gcrs.yaml
scan:
  strict_uncommitted_files: false
  warn_on_uncommitted_files: true
  skip_dirs: [".build", "generated"]
  respect_gitignore: true
```

### Pros
1. **Persistent Settings**
   - Set once, applies to all scans
   - Project-wide configuration
   - Version controlled with repo

2. **Team Standardization**
   - Shared configuration across team
   - Enforces organizational policies
   - Consistent behavior for all developers

3. **Less Verbose**
   - Don't need to specify in every call
   - Cleaner API requests
   - Shorter CLI commands

4. **Repository-Specific**
   - Different repos can have different policies
   - Config lives with the code
   - Easy to see project preferences

5. **Centralized Configuration**
   - All scan settings in one place
   - Can include other settings (skip_dirs, etc.)
   - Single source of truth

### Cons
1. **Hidden Behavior**
   - Not obvious from API call what settings apply
   - Must check config file to understand behavior
   - Can be surprising if config file exists

2. **File Management Overhead**
   - Need to create/manage config file
   - File path resolution complexity
   - Config file discovery/search logic

3. **Less Flexible**
   - Harder to override for specific scans
   - Must edit file to change behavior
   - Can't easily have different policies per scan

4. **Complexity**
   - Need config file parser (YAML/TOML)
   - Config file validation
   - Error handling for missing/invalid config

5. **CI/CD Challenges**
   - Config file might not exist in CI
   - Need fallback behavior
   - Harder to test different scenarios

6. **Version Control Issues**
   - Config file might be ignored by .gitignore
   - Team members might have different configs
   - Merge conflicts on config file

7. **Discovery Complexity**
   - Where to look for config file? (repo root? home dir? multiple locations?)
   - Priority/precedence if multiple configs exist
   - Performance impact of file system searches

## Hybrid Approach (Recommended)

### Implementation
- Config file for **defaults** (optional)
- Parameters for **overrides** (always available)
- Precedence: Parameters > Config File > Built-in Defaults

```python
# ScanParams with config file support
class ScanParams(BaseModel):
    # ... existing fields ...
    strict_uncommitted_files: bool | None = Field(
        default=None,  # None = use config file or default
        description="If True, fail scan when any files lack commit hashes"
    )
    warn_on_uncommitted_files: bool | None = Field(
        default=None,  # None = use config file or default
        description="If True, log warnings for files without commit hashes"
    )
```

Config file (`.gcrs.yaml`):
```yaml
scan:
  strict_uncommitted_files: false
  warn_on_uncommitted_files: true
```

### Pros of Hybrid
1. **Best of Both Worlds**
   - Config file for team defaults
   - Parameters for per-scan overrides
   - Flexible and convenient

2. **Sensible Defaults**
   - Config file sets project standards
   - Parameters allow exceptions
   - Built-in defaults as fallback

3. **Backward Compatible**
   - Works without config file
   - Existing code continues to work
   - Gradual adoption possible

4. **Explicit When Needed**
   - Can see overrides in API calls
   - Config file provides context
   - Clear precedence rules

### Cons of Hybrid
1. **More Complex**
   - Need to implement both
   - Config file loading logic
   - Precedence resolution

2. **Potential Confusion**
   - Need to understand precedence
   - Might not know which value applies
   - More documentation needed

## Recommendation

**Start with Parameters-only approach**, then add config file support if needed.

### Rationale:
1. **Simplicity First**: Parameters are simpler to implement and understand
2. **Explicit is Better**: Makes behavior clear in API calls
3. **Easy to Add Later**: Can add config file support without breaking changes
4. **Matches Current Pattern**: Codebase already uses ScanParams for all config
5. **Better for API**: REST APIs typically use parameters, not config files

### When to Add Config File:
- If users frequently request the same settings
- If teams need to standardize policies
- If config file would contain many related settings
- If there's clear demand for persistent defaults

## Implementation Plan

### Phase 1: Parameters (Now)
- Add `strict_uncommitted_files` and `warn_on_uncommitted_files` to `ScanParams`
- Implement logic in `persist_scan_results`
- Update tests
- Document in API schema

### Phase 2: Config File (Future, if needed)
- Add config file discovery (look for `.gcrs.yaml` in repo root)
- Implement YAML parser
- Add precedence logic (params > config > defaults)
- Update documentation

