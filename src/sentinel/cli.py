"""Command-line interface orchestration for Sentinel."""

import argparse
import sys
from pathlib import Path
from typing import Any, cast

from sentinel.analysis.engine import analyze_file
from sentinel.parser.ast_extractor import SentinelSyntaxError


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


def _print_summary(report: dict[str, Any]) -> None:
    """Print a structured human-readable summary of an analysis report.

    Args:
        report: The dictionary returned by ``analyze_file``.
    """
    print(f"File      : {report['file']}")
    print(f"Score     : {report['score']}")
    print(f"Risk      : {report['risk']}")
    print()

    functions = report["functions"]
    print(f"Functions : {len(functions)}")
    for func in functions:
        name = func["name"]
        complexity = report["complexity"].get(name, 1)
        nesting = report["nesting"].get(name, 0)
        recursive = report["recursion"].get(name, False)
        print(
            f"  {name}"
            f"  [complexity={complexity}"
            f"  nesting={nesting}"
            f"  recursive={recursive}]"
        )

    print()
    print(f"Classes   : {len(report['classes'])}")
    for cls in report["classes"]:
        print(f"  {cls['name']}  (line {cls['lineno']})")

    print()
    print(f"Imports   : {len(report['imports'])}")
    for module in report["imports"]:
        print(f"  {module}")

    print()
    print(f"Globals   : {len(report['globals'])}")
    for name in report["globals"]:
        print(f"  {name}")


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
        try:
            report: dict[str, Any] = cast(dict[str, Any], analyze_file(target))
        except ValueError as exc:
            print(f"sentinel: error: {exc}", file=sys.stderr)
            return 1
        except SentinelSyntaxError as exc:
            print(f"sentinel: error: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"sentinel: error: {exc}", file=sys.stderr)
            return 1
        _print_summary(report)
        return 0

    return 1


def main() -> None:
    """Entry point for the Sentinel CLI."""
    parser = build_argument_parser()
    args = parser.parse_args()
    raise SystemExit(execute(args))
