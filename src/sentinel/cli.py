"""Command-line interface orchestration for Sentinel."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from sentinel.ai.reviewer import generate_review
from sentinel.analysis.engine import analyze_file
from sentinel.parser.ast_extractor import SentinelSyntaxError
from sentinel.reporting.markdown import generate_markdown_report

logger = logging.getLogger(__name__)

ANALYZE_EXCEPTIONS: tuple[type[Exception], ...] = (
    ValueError,
    SentinelSyntaxError,
    OSError,
)

REVIEW_EXCEPTIONS: tuple[type[Exception], ...] = (
    TypeError,
    ValueError,
)


def _handle_cli_error(event: str, path: Path, message: str, exc: Exception) -> int:
    """Log and print a structured CLI error.

    Args:
        event: Event name used in structured logging.
        path: Target path associated with the error.
        message: Human-readable log message.
        exc: Captured exception.

    Returns:
        Process exit code ``1``.
    """
    logger.exception(message, extra={"event": event, "path": str(path)})
    print(f"sentinel: error: {exc}", file=sys.stderr)
    return 1


def build_argument_parser() -> argparse.ArgumentParser:
    """Construct and return the Sentinel CLI argument parser."""
    logger.debug("Building CLI argument parser", extra={"event": "cli.parser.build"})
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
    analyze_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full analysis report as JSON.",
    )
    analyze_parser.add_argument(
        "--report",
        type=str,
        help="Write the full analysis report to a Markdown file.",
    )
    analyze_parser.add_argument(
        "--ai",
        action="store_true",
        help="Generate an AI-assisted review.",
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
    logger.debug(
        "Executing CLI command",
        extra={"event": "cli.execute", "command": getattr(args, "command", None)},
    )
    if args.command is None:
        build_argument_parser().print_help()
        return 1

    if args.command == "analyze":
        target = Path(args.path)
        logger.info("Starting analysis command", extra={"event": "cli.analyze.start", "path": str(target)})
        if not target.exists():
            logger.error("Analysis target does not exist", extra={"event": "cli.analyze.invalid_path", "path": str(target)})
            print(f"sentinel: error: path does not exist: {args.path}", file=sys.stderr)
            return 1
        try:
            report = analyze_file(target)
        except ANALYZE_EXCEPTIONS as exc:
            return _handle_cli_error(
                event="cli.analyze.error",
                path=target,
                message="Analysis command failed",
                exc=exc,
            )

        if args.report:
            report_path = Path(args.report)
            try:
                markdown_output = generate_markdown_report(report)
                report_path.write_text(markdown_output, encoding="utf-8")
                logger.info(
                    "Markdown report written",
                    extra={"event": "cli.report.written", "path": str(report_path)},
                )
            except OSError as exc:
                return _handle_cli_error(
                    event="cli.report.write_error",
                    path=report_path,
                    message="Failed to write markdown report",
                    exc=exc,
                )

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            _print_summary(report)

        if args.ai:
            try:
                review = generate_review(report, use_ai=True)
            except REVIEW_EXCEPTIONS as exc:
                return _handle_cli_error(
                    event="cli.review.error",
                    path=target,
                    message="Review generation failed",
                    exc=exc,
                )
            print()
            print("Review")
            print("------")
            print(review)
            logger.info("Review generated", extra={"event": "cli.review.generated", "path": str(target)})
        logger.info("Analysis command completed", extra={"event": "cli.analyze.completed", "path": str(target)})
        return 0

    return 1


def main() -> None:
    """Entry point for the Sentinel CLI."""
    logger.debug("CLI entrypoint invoked", extra={"event": "cli.main"})
    parser = build_argument_parser()
    args = parser.parse_args()
    raise SystemExit(execute(args))
