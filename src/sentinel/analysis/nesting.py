"""Maximum nesting depth computation for Python ASTs."""

import ast

_NESTING_NODE_TYPES: tuple[type, ...] = (
    ast.If,
    ast.For,
    ast.While,
    ast.With,
    ast.Try,
    ast.AsyncFor,
    ast.AsyncWith,
)


class _NestingVisitor(ast.NodeVisitor):
    """AST visitor that tracks maximum nesting depth per function via DFS."""

    def __init__(self) -> None:
        self._current_function: str | None = None
        self._current_depth: int = 0
        self._max_depths: dict[str, int] = {}

    @property
    def results(self) -> dict[str, int]:
        """Return the collected nesting depth mapping."""
        return self._max_depths

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Enter a function scope and track its maximum nesting depth."""
        enclosing_function = self._current_function
        enclosing_depth = self._current_depth
        self._current_function = node.name
        self._current_depth = 0
        self._max_depths[node.name] = 0
        self.generic_visit(node)
        self._current_function = enclosing_function
        self._current_depth = enclosing_depth

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a synchronous function definition."""
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an asynchronous function definition."""
        self._visit_function(node)

    def generic_visit(self, node: ast.AST) -> None:
        """Override generic traversal to track nesting depth for control-flow nodes."""
        if self._current_function is not None and isinstance(node, _NESTING_NODE_TYPES):
            self._current_depth += 1
            if self._current_depth > self._max_depths[self._current_function]:
                self._max_depths[self._current_function] = self._current_depth
            for child in ast.iter_child_nodes(node):
                self.visit(child)
            self._current_depth -= 1
        else:
            super().generic_visit(node)


def compute_nesting_depth(tree: ast.AST) -> dict[str, int]:
    """Compute the maximum nesting depth for each function in an AST.

    Nesting depth increments for each nested control-flow structure:
    ``if``, ``for``, ``while``, ``with``, ``try``, ``async for``, ``async with``.

    Args:
        tree: A parsed abstract syntax tree.

    Returns:
        A mapping of function name to its maximum nesting depth.
    """
    visitor = _NestingVisitor()
    visitor.visit(tree)
    return visitor.results
