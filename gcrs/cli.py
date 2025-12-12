"""Command-line interface for the Green Cloud Repository Scanner."""

import argparse
import sys
from pathlib import Path

from gcrs.constants import (
    OUTPUT_FORMAT_CSV,
    OUTPUT_FORMAT_JSON,
    OUTPUT_FORMAT_MARKDOWN,
    OUTPUT_FORMAT_SARIF,
    OutputFormat,
)
from gcrs.core.scanner import scan_repository, summarize_repo_contents


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Green Cloud Repository Scanner - Scan and analyze repository contents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute", required=True)

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan repository and output file records")
    scan_parser.add_argument(
        "repo_root",
        type=str,
        help="Path to the repository root directory to scan",
    )
    scan_parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["json", "markdown", "csv", "sarif"],
        default="json",
        help="Output format (default: json)",
    )
    scan_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file path (default: stdout)",
    )
    scan_parser.add_argument(
        "--skip-dirs",
        type=str,
        nargs="+",
        default=[],
        help="Additional directories to skip during scanning",
    )
    scan_parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Do not respect .gitignore files",
    )

    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Generate repository summary")
    summary_parser.add_argument(
        "repo_root",
        type=str,
        help="Path to the repository root directory to scan",
    )
    summary_parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["json", "markdown", "csv"],
        default="json",
        help="Output format (default: json)",
    )
    summary_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file path (default: stdout)",
    )
    summary_parser.add_argument(
        "--skip-dirs",
        type=str,
        nargs="+",
        default=[],
        help="Additional directories to skip during scanning",
    )
    summary_parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Do not respect .gitignore files",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    args = parse_args()

    # Convert repo_root to Path and validate
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        print(f"Error: Repository root does not exist: {repo_root}", file=sys.stderr)
        return 1
    if not repo_root.is_dir():
        print(f"Error: Repository root is not a directory: {repo_root}", file=sys.stderr)
        return 1

    # Determine output format
    output_format: OutputFormat = args.format  # type: ignore

    # Determine output destination
    output_file = Path(args.output) if args.output else None
    output_stream = sys.stdout if args.output is None else None

    # Parse skip_dirs
    skip_dirs = args.skip_dirs if args.skip_dirs else []

    # Parse respect_gitignore
    respect_gitignore = not args.no_gitignore

    try:
        if args.command == "scan":
            response = scan_repository(
                repo_root=repo_root,
                output_file=output_file,
                output_file_format=output_format,
                skip_dirs=skip_dirs,
                respect_gitignore=respect_gitignore,
                output_stream=output_stream,
            )
            if response.status == "error":
                print(f"Error: {response.error}", file=sys.stderr)
                return 1
            return 0

        elif args.command == "summary":
            response = summarize_repo_contents(
                repo_root=repo_root,
                output_file=output_file,
                output_file_format=output_format,
                skip_dirs=skip_dirs,
                respect_gitignore=respect_gitignore,
                output_stream=output_stream,
            )
            if response.status == "error":
                print(f"Error: {response.error}", file=sys.stderr)
                return 1
            return 0

        else:
            print(f"Error: Unknown command: {args.command}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

