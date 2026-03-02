"""Command-line interface orchestration for Sentinel."""

import argparse
import sys
from pathlib import Path


def build_argument_parser() -> argparse.ArgumentParser:
    """Construct and return the Sentinel CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="sentinel",
        description="Sentinel: a production-grade static analysis CLI tool.",
    )
    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Run static analysis on the specified path.",
    )
    analyze_parser.add_argument(
        "path",
        type=str,
        help="File or directory path to analyze.",
    )

    return parser


def execute(args: argparse.Namespace) -> int:
    """Dispatch CLI commands and return an exit code.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Integer exit code. 0 for success, 1 for failure.
    """
    if args.command is None:
        build_argument_parser().print_help()
        return 1

    if args.command == "analyze":
        target = Path(args.path)
        if not target.exists():
            print(f"sentinel: error: path does not exist: {args.path}", file=sys.stderr)
            return 1
        print("Analysis engine not yet implemented.")
        return 0

    return 1


def main() -> None:
    """Entry point for the Sentinel CLI."""
    parser = build_argument_parser()
    args = parser.parse_args()
    raise SystemExit(execute(args))
