"""Markdown report generation for Sentinel analysis results."""

from typing import Any, cast


def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    """Normalize an input value to a list of dictionaries."""
    if isinstance(value, list):
        typed_value = cast(list[Any], value)
        normalized: list[dict[str, Any]] = []
        for item in typed_value:
            if isinstance(item, dict):
                typed_item = cast(dict[Any, Any], item)
                normalized.append({str(key): val for key, val in typed_item.items()})
        return normalized
    return []


def _as_list_of_strings(value: Any) -> list[str]:
    """Normalize an input value to a list of strings."""
    if isinstance(value, list):
        typed_value = cast(list[Any], value)
        return [item for item in typed_value if isinstance(item, str)]
    return []


def _as_dict(value: Any) -> dict[str, Any]:
    """Normalize an input value to a dictionary with string keys."""
    if isinstance(value, dict):
        typed_value = cast(dict[Any, Any], value)
        return {str(key): val for key, val in typed_value.items()}
    return {}


def generate_markdown_report(analysis: dict[str, Any]) -> str:
    """Generate a deterministic Markdown report from analysis output.

    Args:
        analysis: Aggregated analysis result dictionary.

    Returns:
        A Markdown-formatted report string.
    """
    file_path = str(analysis.get("file", ""))
    score = analysis.get("score", "")
    risk = str(analysis.get("risk", ""))

    functions = _as_list_of_dicts(analysis.get("functions", []))
    classes = _as_list_of_dicts(analysis.get("classes", []))
    imports = _as_list_of_strings(analysis.get("imports", []))
    globals_list = _as_list_of_strings(analysis.get("globals", []))

    complexity = _as_dict(analysis.get("complexity", {}))
    nesting = _as_dict(analysis.get("nesting", {}))
    recursion = _as_dict(analysis.get("recursion", {}))
    call_graph = _as_dict(analysis.get("call_graph", {}))

    lines: list[str] = []
    lines.append("# Sentinel Analysis Report")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- File: {file_path}")
    lines.append(f"- Score: {score}")
    lines.append(f"- Risk: {risk}")
    lines.append("")

    lines.append("## Functions")
    if functions:
        lines.append("| Name | Line Start | Line End | Complexity | Nesting | Recursive |")
        lines.append("|---|---:|---:|---:|---:|---|")
        function_names = sorted(
            [str(function.get("name", "")) for function in functions if function.get("name")],
        )
        function_by_name: dict[str, dict[str, Any]] = {
            str(function.get("name")): function
            for function in functions
            if function.get("name")
        }
        for name in function_names:
            function = function_by_name[name]
            lineno = function.get("lineno", "")
            end_lineno = function.get("end_lineno", "")
            function_complexity = complexity.get(name, "")
            function_nesting = nesting.get(name, "")
            function_recursive = recursion.get(name, "")
            lines.append(
                f"| {name} | {lineno} | {end_lineno} | {function_complexity} | {function_nesting} | {function_recursive} |",
            )
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Classes")
    if classes:
        lines.append("| Name | Line Start |")
        lines.append("|---|---:|")
        class_names = sorted([str(cls.get("name", "")) for cls in classes if cls.get("name")])
        class_by_name: dict[str, dict[str, Any]] = {
            str(cls.get("name")): cls
            for cls in classes
            if cls.get("name")
        }
        for name in class_names:
            cls = class_by_name[name]
            lineno = cls.get("lineno", "")
            lines.append(f"| {name} | {lineno} |")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Imports")
    if imports:
        for module_name in sorted(imports):
            lines.append(f"- {module_name}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Global Variables")
    if globals_list:
        for global_name in sorted(globals_list):
            lines.append(f"- {global_name}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Call Graph")
    if call_graph:
        for caller in sorted(call_graph):
            raw_callees = call_graph.get(caller, [])
            if isinstance(raw_callees, list):
                typed_callees = cast(list[Any], raw_callees)
                callees = sorted(
                    [str(callee) for callee in typed_callees if isinstance(callee, (str, int, float, bool))],
                )
            else:
                callees = []
            if callees:
                lines.append(f"- {caller}: {', '.join(callees)}")
            else:
                lines.append(f"- {caller}: (none)")
    else:
        lines.append("- None")

    return "\n".join(lines)
