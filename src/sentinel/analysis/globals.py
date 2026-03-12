"""Global variable detection for Python ASTs."""

import ast


def detect_global_variables(tree: ast.AST) -> list[str]:
    """Detect top-level variable assignments in an AST.

    Only considers simple name targets (``ast.Name``) at the module body
    level. Ignores function definitions, class definitions, and imports.

    Args:
        tree: A parsed abstract syntax tree (expected to be ``ast.Module``).

    Returns:
        A list of variable names assigned at module scope, in source order.
    """
    if not isinstance(tree, ast.Module):
        return []

    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.append(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                names.append(node.target.id)
        elif isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Name):
                names.append(node.target.id)
    return names
