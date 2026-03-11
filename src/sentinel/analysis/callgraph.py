"""Call graph construction for Python ASTs."""

import ast


class _CallGraphBuilder(ast.NodeVisitor):
    """AST visitor that builds a caller-to-callees mapping."""

    def __init__(self) -> None:
        self._current_function: str | None = None
        self._graph: dict[str, list[str]] = {}

    @property
    def results(self) -> dict[str, list[str]]:
        """Return the collected call graph."""
        return self._graph

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Enter a function scope and record its outgoing calls."""
        enclosing = self._current_function
        self._current_function = node.name
        self._graph[node.name] = []
        self.generic_visit(node)
        self._current_function = enclosing

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a synchronous function definition."""
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an asynchronous function definition."""
        self._visit_function(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Record a function call if inside a function scope."""
        if self._current_function is not None:
            callee = _resolve_call_name(node.func)
            if callee is not None:
                self._graph[self._current_function].append(callee)
        self.generic_visit(node)


def _resolve_call_name(node: ast.expr) -> str | None:
    """Resolve a call target to a dotted name string.

    Args:
        node: The ``func`` attribute of an ``ast.Call`` node.

    Returns:
        The resolved name as a string, or ``None`` if the call target
        cannot be statically resolved (e.g. subscript calls).
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        value = _resolve_call_name(node.value)
        if value is not None:
            return f"{value}.{node.attr}"
    return None


def build_call_graph(tree: ast.AST) -> dict[str, list[str]]:
    """Build a call graph from an AST.

    Each key is a function name and its value is an ordered list of
    callee names (including dotted attribute calls) as they appear
    in the source.

    Args:
        tree: A parsed abstract syntax tree.

    Returns:
        A mapping of function name to list of callee names.
    """
    builder = _CallGraphBuilder()
    builder.visit(tree)
    return builder.results
