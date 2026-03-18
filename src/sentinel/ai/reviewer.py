"""AI-assisted review generation for Sentinel analysis reports."""

import json
import os
from typing import Any, cast
from urllib import error, request


class ReviewerConfigurationError(RuntimeError):
    """Raised when AI review is requested but configuration is invalid."""


class ReviewerAIError(RuntimeError):
    """Raised when AI review generation fails at runtime."""


def _validate_structured_json(analysis: Any) -> dict[str, Any]:
    """Validate that analysis is a structured JSON object.

    Args:
        analysis: Candidate analysis payload.

    Returns:
        A validated dictionary representation.

    Raises:
        TypeError: If the payload is not a dictionary.
        ValueError: If the payload cannot be serialized as a JSON object.
    """
    if not isinstance(analysis, dict):
        raise TypeError("analysis must be a dictionary representing a JSON object")

    try:
        encoded = json.dumps(analysis, ensure_ascii=False, sort_keys=True)
        decoded = json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise ValueError("analysis must be JSON-serializable") from exc

    if not isinstance(decoded, dict):
        raise ValueError("analysis must encode to a JSON object")

    return cast(dict[str, Any], decoded)


def _generate_deterministic_summary(analysis: dict[str, Any]) -> str:
    """Generate a deterministic, human-readable summary.

    Args:
        analysis: Validated analysis dictionary.

    Returns:
        Deterministic plain-text summary.
    """
    file_path = str(analysis.get("file", ""))
    score = analysis.get("score", "")
    risk = str(analysis.get("risk", ""))

    functions_any = analysis.get("functions", [])
    classes_any = analysis.get("classes", [])
    imports_any = analysis.get("imports", [])
    globals_any = analysis.get("globals", [])

    functions: list[Any] = cast(list[Any], functions_any) if isinstance(functions_any, list) else []
    classes: list[Any] = cast(list[Any], classes_any) if isinstance(classes_any, list) else []
    imports: list[Any] = cast(list[Any], imports_any) if isinstance(imports_any, list) else []
    globals_list: list[Any] = cast(list[Any], globals_any) if isinstance(globals_any, list) else []

    function_count = len(functions)
    class_count = len(classes)
    import_count = len(imports)
    globals_count = len(globals_list)

    lines: list[str] = [
        "Sentinel Deterministic Review",
        f"File: {file_path}",
        f"Score: {score}",
        f"Risk: {risk}",
        f"Functions: {function_count}",
        f"Classes: {class_count}",
        f"Imports: {import_count}",
        f"Globals: {globals_count}",
    ]

    top_complexities_any = analysis.get("complexity", {})
    if isinstance(top_complexities_any, dict):
        top_complexities = cast(dict[str, Any], top_complexities_any)
        ranked = sorted(
            ((str(name), int(value)) for name, value in top_complexities.items() if isinstance(value, int)),
            key=lambda item: (-item[1], item[0]),
        )
        if ranked:
            lines.append("Top Complexity:")
            for name, value in ranked[:3]:
                lines.append(f"- {name}: {value}")

    return "\n".join(lines)


def _generate_ai_summary(analysis: dict[str, Any]) -> str:
    """Generate an AI summary using an OpenAI-compatible endpoint.

    Configuration via environment variables:
        - SENTINEL_AI_BASE_URL
        - SENTINEL_AI_API_KEY
        - SENTINEL_AI_MODEL

    Args:
        analysis: Validated analysis dictionary.

    Returns:
        AI-generated review text.

    Raises:
        ReviewerConfigurationError: If required configuration is missing.
        ReviewerAIError: If the request fails or response is malformed.
    """
    base_url = os.getenv("SENTINEL_AI_BASE_URL", "").strip()
    api_key = os.getenv("SENTINEL_AI_API_KEY", "").strip()
    model = os.getenv("SENTINEL_AI_MODEL", "").strip()

    if not base_url or not api_key or not model:
        raise ReviewerConfigurationError(
            "AI configuration is incomplete. Set SENTINEL_AI_BASE_URL, "
            "SENTINEL_AI_API_KEY, and SENTINEL_AI_MODEL.",
        )

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Sentinel Reviewer. Produce a concise code quality review "
                    "from structured static analysis data."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(analysis, sort_keys=True),
            },
        ],
        "temperature": 0,
    }

    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=f"{base_url.rstrip('/')}/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=20) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise ReviewerAIError(f"AI request failed: {exc}") from exc

    try:
        choices = response_payload["choices"]
        message = choices[0]["message"]
        content = message["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ReviewerAIError("AI response is malformed") from exc

    if not isinstance(content, str) or not content.strip():
        raise ReviewerAIError("AI response content is empty")

    return content.strip()


def generate_review(analysis: dict[str, Any], use_ai: bool) -> str:
    """Generate a review from a structured Sentinel analysis report.

    Args:
        analysis: Structured JSON object represented as a dictionary.
        use_ai: Whether to attempt AI-based review generation.

    Returns:
        Review text. If AI is disabled or unavailable, returns a deterministic
        summary.

    Raises:
        TypeError: If ``analysis`` is not a dictionary.
        ValueError: If ``analysis`` is not JSON-serializable.
    """
    validated = _validate_structured_json(analysis)

    if not use_ai:
        return _generate_deterministic_summary(validated)

    try:
        return _generate_ai_summary(validated)
    except (ReviewerConfigurationError, ReviewerAIError):
        return _generate_deterministic_summary(validated)
