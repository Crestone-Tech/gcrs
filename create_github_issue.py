#!/usr/bin/env python3
"""Script to create GitHub issues via the GitHub API.

Usage:
    python create_github_issue.py --title "Issue Title" --body "Issue description"
    
Requires:
    - GITHUB_TOKEN environment variable set
    - Or pass --token option
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library not installed. Install with: pip install requests")
    sys.exit(1)


def get_repo_info():
    """Get repository owner and name from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        remote_url = result.stdout.strip()
        
        # Handle both SSH and HTTPS URLs
        if remote_url.startswith("git@"):
            # SSH format: git@github.com:owner/repo.git
            parts = remote_url.replace("git@github.com:", "").replace(".git", "").split("/")
        elif "github.com" in remote_url:
            # HTTPS format: https://github.com/owner/repo.git
            parts = remote_url.split("github.com/")[1].replace(".git", "").split("/")
        else:
            raise ValueError(f"Unknown remote URL format: {remote_url}")
        
        if len(parts) >= 2:
            return parts[0], parts[1]
        else:
            raise ValueError(f"Could not parse repository from URL: {remote_url}")
    except Exception as e:
        print(f"Error getting repo info: {e}")
        sys.exit(1)


def create_issue(owner: str, repo: str, title: str, body: str, token: str, labels: list[str] | None = None):
    """Create a GitHub issue."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    data = {
        "title": title,
        "body": body,
    }
    
    if labels:
        data["labels"] = labels
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 201:
        issue_data = response.json()
        print(f"✅ Issue created successfully!")
        print(f"   Title: {issue_data['title']}")
        print(f"   URL: {issue_data['html_url']}")
        print(f"   Number: #{issue_data['number']}")
        return issue_data
    else:
        print(f"❌ Error creating issue: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Create a GitHub issue")
    parser.add_argument("--title", required=True, help="Issue title")
    parser.add_argument("--body", required=True, help="Issue body/description")
    parser.add_argument("--token", help="GitHub personal access token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--labels", nargs="+", help="Labels to add to the issue")
    parser.add_argument("--owner", help="Repository owner (auto-detected from git remote if not provided)")
    parser.add_argument("--repo", help="Repository name (auto-detected from git remote if not provided)")
    
    args = parser.parse_args()
    
    # Get token
    token = args.token or os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GitHub token required. Set GITHUB_TOKEN environment variable or use --token")
        print("\nTo create a token:")
        print("1. Go to https://github.com/settings/tokens")
        print("2. Click 'Generate new token (classic)'")
        print("3. Select 'repo' scope")
        print("4. Copy the token and set it: export GITHUB_TOKEN=your_token")
        sys.exit(1)
    
    # Get repo info
    if args.owner and args.repo:
        owner, repo = args.owner, args.repo
    else:
        owner, repo = get_repo_info()
        print(f"Detected repository: {owner}/{repo}")
    
    # Create issue
    create_issue(owner, repo, args.title, args.body, token, args.labels)


if __name__ == "__main__":
    main()


