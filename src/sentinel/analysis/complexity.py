"""Cyclomatic complexity computation for Python ASTs."""

import ast
import logging

logger = logging.getLogger(__name__)


class _ComplexityVisitor(ast.NodeVisitor):
    """AST visitor that computes cyclomatic complexity per function."""

    def __init__(self) -> None:
        self._current_function: str | None = None
        self._complexity: dict[str, int] = {}

    @property
    def results(self) -> dict[str, int]:
        """Return the collected complexity mapping."""
        return self._complexity

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Process a function definition and compute its complexity."""
        enclosing = self._current_function
        self._current_function = node.name
        self._complexity[node.name] = 1
        self.generic_visit(node)
        self._current_function = enclosing

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a synchronous function definition."""
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an asynchronous function definition."""
        self._visit_function(node)

    def visit_If(self, node: ast.If) -> None:
        """Increment complexity for an if branch."""
        if self._current_function is not None:
            self._complexity[self._current_function] += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Increment complexity for a for loop."""
        if self._current_function is not None:
            self._complexity[self._current_function] += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        """Increment complexity for a while loop."""
        if self._current_function is not None:
            self._complexity[self._current_function] += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Increment complexity for an except handler."""
        if self._current_function is not None:
            self._complexity[self._current_function] += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        """Increment complexity for each additional boolean operand."""
        if self._current_function is not None:
            self._complexity[self._current_function] += len(node.values) - 1
        self.generic_visit(node)


def compute_cyclomatic_complexity(tree: ast.AST) -> dict[str, int]:
    """Compute cyclomatic complexity for each function in an AST.

    Complexity starts at 1 per function and increments for each:
        - ``if`` branch
        - ``for`` loop
        - ``while`` loop
        - ``except`` handler
        - boolean operator (``and``/``or``), once per additional operand

    Args:
        tree: A parsed abstract syntax tree.

    Returns:
        A mapping of function name to its cyclomatic complexity score.
    """
    logger.debug("Computing cyclomatic complexity", extra={"event": "analysis.complexity.start"})
    visitor = _ComplexityVisitor()
    visitor.visit(tree)
    logger.info(
        "Cyclomatic complexity computed",
        extra={"event": "analysis.complexity.completed", "functions": len(visitor.results)},
    )
    return visitor.results
