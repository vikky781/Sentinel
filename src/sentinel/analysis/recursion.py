"""Direct recursion detection for Python ASTs."""

import ast
import logging

logger = logging.getLogger(__name__)


class _RecursionDetector(ast.NodeVisitor):
    """AST visitor that detects direct recursion per function."""

    def __init__(self) -> None:
        self._current_function: str | None = None
        self._recursion: dict[str, bool] = {}

    @property
    def results(self) -> dict[str, bool]:
        """Return the collected recursion mapping."""
        return self._recursion

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Enter a function scope and scan for self-referencing calls."""
        enclosing = self._current_function
        self._current_function = node.name
        self._recursion[node.name] = False
        self.generic_visit(node)
        self._current_function = enclosing

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a synchronous function definition."""
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an asynchronous function definition."""
        self._visit_function(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Check if a call invokes the current function by name."""
        if self._current_function is not None:
            if isinstance(node.func, ast.Name) and node.func.id == self._current_function:
                self._recursion[self._current_function] = True
        self.generic_visit(node)


def detect_recursion(tree: ast.AST) -> dict[str, bool]:
    """Detect direct recursion for each function in an AST.

    A function is considered directly recursive if it contains a call
    to itself by name within its own body.

    Args:
        tree: A parsed abstract syntax tree.

    Returns:
        A mapping of function name to a boolean indicating whether
        the function is directly recursive.
    """
    logger.debug("Detecting direct recursion", extra={"event": "analysis.recursion.start"})
    detector = _RecursionDetector()
    detector.visit(tree)
    logger.info(
        "Recursion detection completed",
        extra={"event": "analysis.recursion.completed", "functions": len(detector.results)},
    )
    return detector.results
