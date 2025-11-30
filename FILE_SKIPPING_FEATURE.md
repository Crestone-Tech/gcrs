# File Skipping Feature

## Overview

The Green Cloud Repository Scanner includes configurable file and directory skipping functionality that allows users to control which files and directories are scanned during repository analysis. Skipped directories are not traversed, improving scan performance and allowing users to exclude irrelevant or large directories from analysis.

## How Skipping Works

When a directory or file is skipped:
- The item is not yielded by the repository walker
- The item is not processed or included in scan results
- For skipped directories, the scanner does not descend into subdirectories, preventing traversal of entire directory trees

## Configuration Parameters

### `skip_dirs` Parameter

The `skip_dirs` parameter allows users to specify a list of directory names that should be skipped during scanning.

- **Type:** `list[str]`
- **Default:** A sensible default list of common directories (see Default Skip Directories below)
- **Behavior:** Directory name matching is case-insensitive by default
- **Location:** Available in both `ScanParams` and `SummaryParams`

**Example API Request:**
```json
{
  "repo_root": ".",
  "output_dir": "output",
  "skip_dirs": [".git", "node_modules", "venv", "__pycache__"]
}
```

**CURL Example:**
```bash
curl -X POST "http://localhost:8000/scan/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_root": ".",
    "output_dir": "output",
    "skip_dirs": [".git", "node_modules", "venv", "__pycache__"]
  }'
```

### `.gitignore` Support

The scanner can automatically respect `.gitignore` files when scanning repositories.

- **Parameter:** `respect_gitignore` (in `ScanParams` and `SummaryParams`)
- **Type:** `bool`
- **Default:** `true`
- **Behavior:** 
  - When `true` and a `.gitignore` file is present, files and directories specified in `.gitignore` are skipped
  - Supports nested `.gitignore` files (e.g., `.gitignore` in root and `src/.gitignore`)
  - Uses the `pathspec` library for proper `.gitignore` pattern parsing

**Example API Request:**
```json
{
  "repo_root": ".",
  "output_dir": "output",
  "respect_gitignore": true
}
```

## Always-Skipped Directories

For safety and performance, certain directories are always skipped, regardless of user configuration. If a user's `skip_dirs` list omits any of these directories, they will be automatically added with a warning.

**Always-skipped directories:**
- `node_modules` - Node.js dependencies (can be extremely large)
- `.git` - Git repository metadata
- `venv`, `.venv` - Python virtual environments
- `.pytest_cache` - Pytest test cache
- `__pycache__` - Python bytecode cache
- `.mypy_cache` - MyPy type checking cache

**Rationale:** These directories are:
1. Frequently very large (costly to scan)
2. Generated or derived content (not source code)
3. Common across many project types
4. Rarely useful to include in repository scans

If a user attempts to scan these directories by omitting them from `skip_dirs`, the system will:
- Log a warning message
- Automatically add the missing always-skipped directories
- Include a note in the API response indicating that directories were added

## Implementation Details

### Performance Optimization

The `skip_dirs` list is internally converted to a set for O(1) lookup performance during directory traversal, ensuring efficient skipping even with large skip lists.

### Case Sensitivity

Directory name matching is case-insensitive by default. For example, `node_modules`, `Node_Modules`, and `NODE_MODULES` will all be matched and skipped.

## Future Enhancements

The following enhancements are planned for future releases:

1. **Pattern Matching Support**
   - Support for glob patterns in `skip_dirs` (e.g., `*_cache`, `test_*`)
   - More flexible matching beyond exact directory names

2. **Case-Sensitive Matching Option**
   - Add a `case_sensitive` parameter (defaults to `false`)
   - Allow users to enable case-sensitive directory name matching when needed
   - Priority: Low

3. **Path-Based Skipping**
   - Support for skipping specific paths (e.g., `src/temp`) in addition to directory names
   - Support for glob patterns in paths (e.g., `**/test_data`)
   - More granular control over what gets skipped

4. **Include Directories Override**
   - Add an `include_directories` parameter that allows users to override the default `skip_dirs`
   - Enables scanning of directories that would normally be skipped by default
   - Useful for edge cases where users need to scan typically-skipped directories

## Usage Examples

### Basic Usage with Defaults
```json
{
  "repo_root": ".",
  "output_dir": "output"
}
```
Uses default `skip_dirs` and respects `.gitignore` files.

### Custom Skip Directories
```json
{
  "repo_root": ".",
  "output_dir": "output",
  "skip_dirs": [".git", "node_modules", "dist", "build", "coverage"]
}
```

### Disable .gitignore Support
```json
{
  "repo_root": ".",
  "output_dir": "output",
  "respect_gitignore": false
}
```

### Combined Configuration
```json
{
  "repo_root": ".",
  "output_dir": "output",
  "skip_dirs": ["custom_dir", "another_dir"],
  "respect_gitignore": true
}
```

