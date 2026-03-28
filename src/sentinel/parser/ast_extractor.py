"""AST extraction utilities for parsing Python source files."""

import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


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
    logger.debug("Parsing Python file", extra={"event": "parser.parse.start", "path": str(path)})
    if not path.exists():
        logger.error("File does not exist", extra={"event": "parser.parse.file_missing", "path": str(path)})
        raise FileNotFoundError(f"File does not exist: {path}")

    if path.suffix != ".py":
        logger.error(
            "Invalid file extension",
            extra={"event": "parser.parse.invalid_extension", "path": str(path), "suffix": path.suffix},
        )
        raise ValueError(f"Expected a .py file, got: {path.suffix!r} ({path})")

    source: str = path.read_text(encoding="utf-8")

    try:
        parsed = ast.parse(source, filename=str(path))
        logger.info("Parsing completed", extra={"event": "parser.parse.completed", "path": str(path)})
        return parsed
    except SyntaxError as exc:
        logger.exception(
            "Syntax error while parsing",
            extra={"event": "parser.parse.syntax_error", "path": str(path), "line": exc.lineno},
        )
        raise SentinelSyntaxError(
            file_path=path,
            line_number=exc.lineno,
            detail=exc.msg,
        ) from exc


class _FunctionCollector(ast.NodeVisitor):
    """AST visitor that collects function and method definitions."""

    def __init__(self) -> None:
        self.functions: list[dict[str, str | int]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Record a function definition and continue traversal."""
        self.functions.append({
            "name": node.name,
            "lineno": node.lineno,
            "end_lineno": node.end_lineno if node.end_lineno is not None else node.lineno,
        })
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Record an async function definition and continue traversal."""
        self.functions.append({
            "name": node.name,
            "lineno": node.lineno,
            "end_lineno": node.end_lineno if node.end_lineno is not None else node.lineno,
        })
        self.generic_visit(node)


def extract_functions(tree: ast.AST) -> list[dict[str, str | int]]:
    """Extract all function definitions from an AST.

    Args:
        tree: A parsed abstract syntax tree.

    Returns:
        A list of dictionaries, each containing:
            - name: The function name.
            - lineno: The starting line number.
            - end_lineno: The ending line number.
    """
    logger.debug("Extracting functions", extra={"event": "parser.extract_functions.start"})
    collector = _FunctionCollector()
    collector.visit(tree)
    logger.info(
        "Function extraction completed",
        extra={"event": "parser.extract_functions.completed", "count": len(collector.functions)},
    )
    return collector.functions


class _ImportCollector(ast.NodeVisitor):
    """AST visitor that collects imported module names."""

    def __init__(self) -> None:
        self.modules: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Record module names from an import statement."""
        for alias in node.names:
            self.modules.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Record the module name from a from-import statement."""
        if node.module is not None:
            self.modules.append(node.module)
        self.generic_visit(node)


def extract_imports(tree: ast.AST) -> list[str]:
    """Extract all imported module names from an AST.

    Handles both ``import x`` and ``from x import y`` forms.

    Args:
        tree: A parsed abstract syntax tree.

    Returns:
        A flat list of module name strings in the order they appear.
    """
    logger.debug("Extracting imports", extra={"event": "parser.extract_imports.start"})
    collector = _ImportCollector()
    collector.visit(tree)
    logger.info(
        "Import extraction completed",
        extra={"event": "parser.extract_imports.completed", "count": len(collector.modules)},
    )
    return collector.modules


class _ClassCollector(ast.NodeVisitor):
    """AST visitor that collects class definitions."""

    def __init__(self) -> None:
        self.classes: list[dict[str, str | int]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Record a class definition and continue traversal."""
        self.classes.append({
            "name": node.name,
            "lineno": node.lineno,
        })
        self.generic_visit(node)


def extract_classes(tree: ast.AST) -> list[dict[str, str | int]]:
    """Extract all class definitions from an AST.

    Args:
        tree: A parsed abstract syntax tree.

    Returns:
        A list of dictionaries, each containing:
            - name: The class name.
            - lineno: The starting line number.
    """
    logger.debug("Extracting classes", extra={"event": "parser.extract_classes.start"})
    collector = _ClassCollector()
    collector.visit(tree)
    logger.info(
        "Class extraction completed",
        extra={"event": "parser.extract_classes.completed", "count": len(collector.classes)},
    )
    return collector.classes
