"""AST extraction utilities for parsing Python source files."""

import ast
from pathlib import Path


class SentinelSyntaxError(Exception):
    """Raised when a Python source file contains invalid syntax.

    Attributes:
        file_path: The path to the file that failed to parse.
        line_number: The line number where the syntax error occurred, if available.
        detail: The underlying syntax error message.
    """

    def __init__(self, file_path: Path, line_number: int | None, detail: str) -> None:
        self.file_path: Path = file_path
        self.line_number: int | None = line_number
        self.detail: str = detail
        super().__init__(
            f"Syntax error in {file_path}"
            f"{f' at line {line_number}' if line_number is not None else ''}"
            f": {detail}"
        )


def parse_python_file(path: Path) -> ast.AST:
    """Parse a Python source file and return its AST.

    Args:
        path: Path to a Python source file.

    Returns:
        The parsed abstract syntax tree.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file does not have a .py extension.
        SentinelSyntaxError: If the file contains invalid Python syntax.
        OSError: If the file cannot be read.
    """
    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")

    if path.suffix != ".py":
        raise ValueError(f"Expected a .py file, got: {path.suffix!r} ({path})")

    source: str = path.read_text(encoding="utf-8")

    try:
        return ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise SentinelSyntaxError(
            file_path=path,
            line_number=exc.lineno,
            detail=exc.msg,
        ) from exc
