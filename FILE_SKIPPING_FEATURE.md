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

The `skip_dirs` parameter allows users to specify additional directory names that should be skipped during scanning, in addition to directories that are always skipped (see Always-Skipped Directories below).

**Purpose:** This parameter enables users to add custom directories to skip that are specific to their project or technology stack. The always-skipped directories are automatically skipped and cannot be overridden. Duplication by including an always-skipped directory in the user-supplied `skip_dirs` parameter is harmless.

- **Type:** `list[str]`
- **Default:** `[]` (empty list)
- **Behavior:** 
  - User-provided directories are merged with the always-skipped directories
  - Directory name matching is case-insensitive by default
  - The always-skipped directories are always included, regardless of what the user specifies
- **Location:** Available in `ScanParams`

**Example API Request:**
```json
{
  "repo_root": ".",
  "skip_dirs": ["dist", "build", "coverage", "custom_build_dir"]
}
```

**CURL Example:**
```bash
curl -X POST "http://localhost:8000/scan/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_root": ".",
    "skip_dirs": [".git", "node_modules", "venv", "__pycache__"]
  }'
```

### `.gitignore` Support

The scanner can automatically respect `.gitignore` files when scanning repositories.

- **Parameter:** `respect_gitignore` (in `ScanParams`)
- **Type:** `bool`
- **Default:** `true`
- **Behavior:** 
  - When `true` and a `.gitignore` file is present in the repository root, files and directories specified in `.gitignore` are skipped
  - Currently supports root-level `.gitignore` files only
  - Uses the `pathspec` library for proper `.gitignore` pattern parsing
  - `.gitignore` patterns are combined with `skip_dirs` and always-skipped directories (if any pattern matches, the item is skipped)

**Example API Request:**
```json
{
  "repo_root": ".",
  "respect_gitignore": true
}
```

## Always-Skipped Directories

For safety and performance, certain directories are **always skipped**. This **cannot be overridden or configured** by user configuration. Duplication by including an always-skipped directory in the user-supplied `skip_dirs` parameter is harmless.

**Always-skipped directories:**
- `.git` - Git repository metadata
- `node_modules` - Node.js dependencies (can be extremely large)
- `.venv`, `venv` - Python virtual environments
- `__pycache__` - Python bytecode cache
- `dist` - Distribution/build output
- `build` - Build artifacts
- `out` - Output directories
- `tmp` - Temporary files
- `.pytest_cache` - Pytest test cache
- `.mypy_cache` - MyPy type checking cache
- `.vscode` - Visual Studio Code settings
- `.DS_Store` - macOS directory metadata

**Rationale:** These directories are:
1. Frequently very large (costly to scan)
2. Generated or derived content (not source code)
3. Common across many project types
4. Rarely useful to include in repository scans

**Important:** These directories are **not optional** and **cannot be disabled**. The `skip_dirs` parameter is for adding additional directories to skip, not for configuring the always-skipped directories. The system automatically merges user-provided `skip_dirs` with the always-skipped directories.

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

4. **Nested .gitignore Support**
   - Support for nested `.gitignore` files (e.g., `.gitignore` in root and `src/.gitignore`)
   - More comprehensive `.gitignore` pattern matching

## Usage Examples

### Basic Usage with Defaults
```json
{
  "repo_root": "."
}
```
Uses default `skip_dirs` and respects `.gitignore` files. Output files are automatically generated in `{repo_root}/output/`.

### Custom Skip Directories
```json
{
  "repo_root": ".",
  "skip_dirs": ["coverage", "test_results", "temp", "custom_build_dir"]
}
```
Note: The always-skipped directories (`.git`, `node_modules`, `dist`, `build`, etc.) are automatically included and do not need to be specified in `skip_dirs`.

### Disable .gitignore Support
```json
{
  "repo_root": ".",
  "respect_gitignore": false
}
```

### Combined Configuration
```json
{
  "repo_root": ".",
  "skip_dirs": ["custom_dir", "another_dir", "project_specific_build"],
  "respect_gitignore": true
}
```
This configuration will skip:
- All always-skipped directories (automatically included)
- User-specified directories: `custom_dir`, `another_dir`, `project_specific_build`
- Any files/directories matching patterns in `.gitignore` (if present)

