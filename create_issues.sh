#!/bin/bash
# Script to create GitHub issues for GCRS work items
# Run: gh auth login first, then: bash create_issues.sh

GH_CMD="C:/Program Files/GitHub CLI/gh.exe"

# Check authentication
$GH_CMD auth status || {
    echo "Please authenticate first: $GH_CMD auth login"
    exit 1
}

# Issue 1: Incremental Scan (Since Datetime)
$GH_CMD issue create \
  --title "Implement Incremental Scan (Since Datetime)" \
  --body "## Overview
Implement incremental scan functionality that scans only files modified since a given datetime. This is required for the Orchestrator module to support scheduled scans.

## Requirements
- Add \`since_datetime\` parameter to ScanParams model
- Filter files where \`most_recent_commit_date >= since_datetime\`
- Support via API endpoints (\`/scan\` and \`/scan/summary\`)
- Support via CLI commands (\`gcrs scan\` and \`gcrs summary\`)
- Store scan scope in database \`scan_config\` JSONB field
- Comprehensive testing including edge cases

## Priority
High - Needed for scheduled scans

## Related
- See \`GCRS_SCAN_SCOPE_TODO.md\` section 1 for detailed task breakdown
- See \`ORCHESTRATOR_DESIGN.md\` for orchestrator requirements" \
  --label "enhancement,high-priority,scan-scope"

# Issue 2: Per Commit Scan
$GH_CMD issue create \
  --title "Implement Per Commit Scan" \
  --body "## Overview
Implement per-commit scan functionality that scans only files changed in a specific commit. This enables commit-level analysis for the Orchestrator.

## Requirements
- Add \`commit_hash\` parameter to ScanParams model
- Implement git utilities to get files changed in a commit
- Support via API endpoints (\`/scan\` and \`/scan/summary\`)
- Support via CLI commands (\`gcrs scan\` and \`gcrs summary\`)
- Handle edge cases: first commit, merge commits, invalid hashes
- Link scan to specific commit in database
- Comprehensive testing

## Priority
High - Needed for commit-level analysis

## Related
- See \`GCRS_SCAN_SCOPE_TODO.md\` section 2 for detailed task breakdown
- See \`ORCHESTRATOR_DESIGN.md\` for orchestrator requirements" \
  --label "enhancement,high-priority,scan-scope"

# Issue 3: Scan Scope Validation
$GH_CMD issue create \
  --title "Implement Scan Scope Validation and Mutual Exclusivity" \
  --body "## Overview
Ensure scan scope parameters (\`since_datetime\` and \`commit_hash\`) are mutually exclusive and properly validated.

## Requirements
- Add validation in ScanParams model to enforce mutual exclusivity
- Default behavior: whole repo scan if neither parameter is provided
- Clear error messages for invalid combinations
- Comprehensive testing

## Priority
Medium - Supporting feature for scan scopes

## Related
- See \`GCRS_SCAN_SCOPE_TODO.md\` section 3" \
  --label "enhancement,medium-priority,validation"

# Issue 4: Uncommitted Files Configuration
$GH_CMD issue create \
  --title "Implement Configurable Uncommitted Files Handling" \
  --body "## Overview
Make the handling of files without commit hashes configurable. Currently files are skipped with warnings, but we need options for strict mode (fail) and silent mode.

## Requirements
- Add \`strict_uncommitted_files\` parameter to ScanParams (default: False)
- Add \`warn_on_uncommitted_files\` parameter to ScanParams (default: True)
- Implement strict mode: fail immediately if any files lack commit hashes
- Implement silent mode: skip files without warnings
- Update \`persist_scan_results()\` to respect these settings
- Comprehensive testing

## Status
Partially implemented - needs testing and documentation

## Related
- See \`UNCOMMITTED_FILES_CONFIG_COMPARISON.md\` for design discussion" \
  --label "enhancement,medium-priority,configuration"

# Issue 5: Orchestrator Integration Testing
$GH_CMD issue create \
  --title "Orchestrator Integration Testing" \
  --body "## Overview
Ensure GCRS can be called by the Orchestrator with all three scan scopes (whole repo, incremental, per commit).

## Requirements
- Verify orchestrator can call GCRS with all scan scopes
- Test parameter passing through orchestrator → GCRS
- Integration tests for orchestrator → GCRS workflow
- Document orchestrator integration patterns

## Priority
Medium - Required for orchestrator module

## Related
- See \`GCRS_SCAN_SCOPE_TODO.md\` section 4
- See \`ORCHESTRATOR_DESIGN.md\`" \
  --label "enhancement,medium-priority,integration,orchestrator"

echo "All issues created successfully!"


