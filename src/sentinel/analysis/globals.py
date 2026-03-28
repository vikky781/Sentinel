"""Global variable detection for Python ASTs."""

import ast
import logging

logger = logging.getLogger(__name__)


def detect_global_variables(tree: ast.AST) -> list[str]:
    """Detect top-level variable assignments in an AST.

    Only considers simple name targets (``ast.Name``) at the module body
    level. Ignores function definitions, class definitions, and imports.

    Args:
        tree: A parsed abstract syntax tree (expected to be ``ast.Module``).

    Returns:
        A list of variable names assigned at module scope, in source order.
    """
    logger.debug("Detecting global variables", extra={"event": "analysis.globals.start"})
    if not isinstance(tree, ast.Module):
        logger.debug("AST is not a module; returning empty globals list", extra={"event": "analysis.globals.non_module"})
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
    logger.info(
        "Global variable detection completed",
        extra={"event": "analysis.globals.completed", "count": len(names)},
    )
    return names
