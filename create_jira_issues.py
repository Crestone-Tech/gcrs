#!/usr/bin/env python3
"""Script to create Jira issues via the Jira REST API.

Usage:
    python create_jira_issues.py --url https://your-domain.atlassian.net --project PROJECT_KEY --email your@email.com --token YOUR_API_TOKEN
    
Or set environment variables:
    export JIRA_URL=https://your-domain.atlassian.net
    export JIRA_PROJECT=PROJECT_KEY
    export JIRA_EMAIL=your@email.com
    export JIRA_API_TOKEN=YOUR_API_TOKEN
    python create_jira_issues.py
"""

import os
import sys
import argparse
import json

try:
    import requests
except ImportError:
    print("Error: requests library not installed. Install with: pip install requests")
    sys.exit(1)


def create_jira_issue(
    jira_url: str,
    project_key: str,
    email: str,
    api_token: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
    priority: str | None = None,
    labels: list[str] | None = None,
) -> dict:
    """Create a Jira issue.
    
    Args:
        jira_url: Jira instance URL (e.g., https://your-domain.atlassian.net)
        project_key: Jira project key (e.g., "PROJ")
        email: Jira account email
        api_token: Jira API token
        summary: Issue summary/title
        description: Issue description
        issue_type: Issue type (default: "Task")
        priority: Priority level (optional)
        labels: List of labels (optional)
    
    Returns:
        Created issue data
    """
    url = f"{jira_url}/rest/api/2/issue"
    
    auth = (email, api_token)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
        }
    }
    
    if priority:
        payload["fields"]["priority"] = {"name": priority}
    
    if labels:
        payload["fields"]["labels"] = labels
    
    response = requests.post(url, json=payload, headers=headers, auth=auth)
    
    if response.status_code == 201:
        issue_data = response.json()
        print(f"✅ Issue created successfully!")
        print(f"   Key: {issue_data['key']}")
        print(f"   URL: {jira_url}/browse/{issue_data['key']}")
        return issue_data
    else:
        print(f"❌ Error creating issue: {response.status_code}")
        print(f"   Response: {response.text}")
        try:
            error_data = response.json()
            if "errorMessages" in error_data:
                for msg in error_data["errorMessages"]:
                    print(f"   Error: {msg}")
            if "errors" in error_data:
                for field, msg in error_data["errors"].items():
                    print(f"   {field}: {msg}")
        except:
            pass
        sys.exit(1)


def create_gcrs_issues(jira_url: str, project_key: str, email: str, api_token: str):
    """Create all GCRS issues in Jira."""
    
    issues = [
        {
            "summary": "Implement Incremental Scan (Since Datetime)",
            "description": """h2. Overview
Implement incremental scan functionality that scans only files modified since a given datetime. This is required for the Orchestrator module to support scheduled scans.

h2. Requirements
* Add {{since_datetime}} parameter to ScanParams model
* Filter files where {{most_recent_commit_date >= since_datetime}}
* Support via API endpoints ({{/scan}} and {{/scan/summary}})
* Support via CLI commands ({{gcrs scan}} and {{gcrs summary}})
* Store scan scope in database {{scan_config}} JSONB field
* Comprehensive testing including edge cases

h2. Priority
High - Needed for scheduled scans

h2. Related
* See {{GCRS_SCAN_SCOPE_TODO.md}} section 1 for detailed task breakdown
* See {{ORCHESTRATOR_DESIGN.md}} for orchestrator requirements""",
            "issue_type": "Story",
            "priority": "High",
            "labels": ["enhancement", "scan-scope"],
        },
        {
            "summary": "Implement Per Commit Scan",
            "description": """h2. Overview
Implement per-commit scan functionality that scans only files changed in a specific commit. This enables commit-level analysis for the Orchestrator.

h2. Requirements
* Add {{commit_hash}} parameter to ScanParams model
* Implement git utilities to get files changed in a commit
* Support via API endpoints ({{/scan}} and {{/scan/summary}})
* Support via CLI commands ({{gcrs scan}} and {{gcrs summary}})
* Handle edge cases: first commit, merge commits, invalid hashes
* Link scan to specific commit in database
* Comprehensive testing

h2. Priority
High - Needed for commit-level analysis

h2. Related
* See {{GCRS_SCAN_SCOPE_TODO.md}} section 2 for detailed task breakdown
* See {{ORCHESTRATOR_DESIGN.md}} for orchestrator requirements""",
            "issue_type": "Story",
            "priority": "High",
            "labels": ["enhancement", "scan-scope"],
        },
        {
            "summary": "Implement Scan Scope Validation and Mutual Exclusivity",
            "description": """h2. Overview
Ensure scan scope parameters ({{since_datetime}} and {{commit_hash}}) are mutually exclusive and properly validated.

h2. Requirements
* Add validation in ScanParams model to enforce mutual exclusivity
* Default behavior: whole repo scan if neither parameter is provided
* Clear error messages for invalid combinations
* Comprehensive testing

h2. Priority
Medium - Supporting feature for scan scopes

h2. Related
* See {{GCRS_SCAN_SCOPE_TODO.md}} section 3""",
            "issue_type": "Task",
            "priority": "Medium",
            "labels": ["enhancement", "validation"],
        },
        {
            "summary": "Complete Uncommitted Files Configuration Implementation",
            "description": """h2. Overview
Complete the implementation of configurable uncommitted files handling. The basic implementation is done, but needs testing and documentation.

h2. Requirements
* Add comprehensive tests for strict mode and silent mode
* Update API documentation with new parameters
* Update README.md with usage examples
* Add CLI help text for new options
* Document behavior modes (strict, warn, silent)

h2. Status
Partially implemented - core logic done, needs testing and docs

h2. Related
* See {{UNCOMMITTED_FILES_CONFIG_COMPARISON.md}} for design discussion
* Implementation in {{gcrs/models.py}} and {{gcrs/db/services.py}}""",
            "issue_type": "Task",
            "priority": "Medium",
            "labels": ["enhancement", "configuration"],
        },
        {
            "summary": "Orchestrator Integration Testing",
            "description": """h2. Overview
Ensure GCRS can be called by the Orchestrator with all three scan scopes (whole repo, incremental, per commit).

h2. Requirements
* Verify orchestrator can call GCRS with all scan scopes
* Test parameter passing through orchestrator → GCRS
* Integration tests for orchestrator → GCRS workflow
* Document orchestrator integration patterns

h2. Priority
Medium - Required for orchestrator module

h2. Related
* See {{GCRS_SCAN_SCOPE_TODO.md}} section 4
* See {{ORCHESTRATOR_DESIGN.md}}""",
            "issue_type": "Task",
            "priority": "Medium",
            "labels": ["enhancement", "integration", "orchestrator"],
        },
    ]
    
    created_issues = []
    for issue_data in issues:
        print(f"\nCreating issue: {issue_data['summary']}")
        issue = create_jira_issue(
            jira_url=jira_url,
            project_key=project_key,
            email=email,
            api_token=api_token,
            summary=issue_data["summary"],
            description=issue_data["description"],
            issue_type=issue_data["issue_type"],
            priority=issue_data["priority"],
            labels=issue_data.get("labels"),
        )
        created_issues.append(issue)
    
    print(f"\n✅ Successfully created {len(created_issues)} issues!")
    return created_issues


def main():
    parser = argparse.ArgumentParser(description="Create Jira issues for GCRS")
    parser.add_argument("--url", help="Jira instance URL (e.g., https://your-domain.atlassian.net)")
    parser.add_argument("--project", help="Jira project key (e.g., PROJ)")
    parser.add_argument("--email", help="Jira account email")
    parser.add_argument("--token", help="Jira API token")
    
    args = parser.parse_args()
    
    # Get values from args or environment variables
    jira_url = args.url or os.getenv("JIRA_URL")
    project_key = args.project or os.getenv("JIRA_PROJECT")
    email = args.email or os.getenv("JIRA_EMAIL")
    api_token = args.token or os.getenv("JIRA_API_TOKEN")
    
    if not all([jira_url, project_key, email, api_token]):
        print("Error: Missing required parameters")
        print("\nRequired parameters:")
        print("  --url       Jira instance URL (or JIRA_URL env var)")
        print("  --project   Jira project key (or JIRA_PROJECT env var)")
        print("  --email     Jira account email (or JIRA_EMAIL env var)")
        print("  --token     Jira API token (or JIRA_API_TOKEN env var)")
        print("\nTo create a Jira API token:")
        print("1. Go to https://id.atlassian.com/manage-profile/security/api-tokens")
        print("2. Click 'Create API token'")
        print("3. Copy the token and use it with --token or JIRA_API_TOKEN env var")
        sys.exit(1)
    
    # Ensure URL doesn't have trailing slash
    jira_url = jira_url.rstrip("/")
    
    print(f"Creating issues in project: {project_key}")
    print(f"Jira URL: {jira_url}\n")
    
    create_gcrs_issues(jira_url, project_key, email, api_token)


if __name__ == "__main__":
    main()


