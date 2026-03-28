"""Analysis engine orchestration for Sentinel."""

import logging
from pathlib import Path
from typing import Any

from sentinel.analysis.callgraph import build_call_graph
from sentinel.analysis.complexity import compute_cyclomatic_complexity
from sentinel.analysis.globals import detect_global_variables
from sentinel.analysis.nesting import compute_nesting_depth
from sentinel.analysis.recursion import detect_recursion
from sentinel.parser.ast_extractor import (
    extract_classes,
    extract_functions,
    extract_imports,
    parse_python_file,
)
from sentinel.scoring.maintainability import calculate_score

logger = logging.getLogger(__name__)


def analyze_file(path: Path) -> dict[str, Any]:
    """Parse a Python file, compute all metrics, and return an aggregated report.

    Steps performed in order:
        1. Parse the source file into an AST.
        2. Extract structural elements: functions, imports, classes.
        3. Compute per-function metrics: cyclomatic complexity, nesting depth,
           recursion, and call graph.
        4. Detect module-level globals.
        5. Compute maintainability score.
        6. Aggregate all results into a single dictionary.

    Args:
        path: Path to a Python source file.

    Returns:
        A dictionary with the following keys:

        - ``"file"``: Absolute path string of the analysed file.
        - ``"functions"``: list[dict] — name, lineno, end_lineno per function.
        - ``"imports"``: list[str] — imported module names.
        - ``"classes"``: list[dict] — name and lineno per class.
        - ``"complexity"``: dict[str, int] — cyclomatic complexity per function.
        - ``"nesting"``: dict[str, int] — max nesting depth per function.
        - ``"recursion"``: dict[str, bool] — direct recursion flag per function.
        - ``"call_graph"``: dict[str, list[str]] — callees per function.
        - ``"globals"``: list[str] — module-level variable names.
        - ``"score"``: float — maintainability score in [0.0, 100.0].
        - ``"risk"``: str — one of ``"LOW"``, ``"MEDIUM"``, or ``"HIGH"``.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a .py file.
        sentinel.parser.ast_extractor.SentinelSyntaxError: On invalid syntax.
        OSError: If the file cannot be read.
    """
    logger.info("Analysis pipeline started", extra={"event": "analysis.engine.start", "path": str(path)})
    tree = parse_python_file(path)

    functions = extract_functions(tree)
    imports = extract_imports(tree)
    classes = extract_classes(tree)

    complexity = compute_cyclomatic_complexity(tree)
    nesting = compute_nesting_depth(tree)
    recursion = detect_recursion(tree)
    call_graph = build_call_graph(tree)
    globals_list = detect_global_variables(tree)

    score_result = calculate_score(
        complexities=complexity,
        nesting=nesting,
        globals_count=len(globals_list),
    )

    logger.info(
        "Analysis pipeline completed",
        extra={
            "event": "analysis.engine.completed",
            "path": str(path),
            "functions": len(functions),
            "classes": len(classes),
            "imports": len(imports),
            "globals": len(globals_list),
        },
    )

    return {
        "file": str(path.resolve()),
        "functions": functions,
        "imports": imports,
        "classes": classes,
        "complexity": complexity,
        "nesting": nesting,
        "recursion": recursion,
        "call_graph": call_graph,
        "globals": globals_list,
        "score": score_result["score"],
        "risk": score_result["risk"],
    }
