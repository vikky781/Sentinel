"""Maintainability scoring for Sentinel analysis results."""

import logging

logger = logging.getLogger(__name__)

_COMPLEXITY_WEIGHT: float = 4.0
_NESTING_WEIGHT: float = 6.0
_GLOBALS_WEIGHT: float = 2.0

_RISK_LOW_THRESHOLD: float = 70.0
_RISK_MEDIUM_THRESHOLD: float = 40.0


def _average(values: dict[str, int]) -> float:
    """Return the arithmetic mean of a mapping's values, or 0.0 if empty."""
    if not values:
        return 0.0
    return sum(values.values()) / len(values)


def calculate_score(
    complexities: dict[str, int],
    nesting: dict[str, int],
    globals_count: int,
) -> dict[str, float | str]:
    """Calculate a maintainability score from analysis metrics.

    The score is computed via a weighted penalty formula:

        penalty = (avg_complexity * 4.0) + (avg_nesting * 6.0) + (globals_count * 2.0)
        score   = clamp(100.0 - penalty, 0.0, 100.0)

    Risk levels:
        - ``"LOW"``    when score >= 70.0
        - ``"MEDIUM"`` when score >= 40.0
        - ``"HIGH"``   when score <  40.0

    Args:
        complexities: Mapping of function name to cyclomatic complexity.
        nesting: Mapping of function name to maximum nesting depth.
        globals_count: Number of global variables detected at module scope.

    Returns:
        A dictionary with:
            - ``"score"``: float in the range [0.0, 100.0].
            - ``"risk"``: one of ``"LOW"``, ``"MEDIUM"``, or ``"HIGH"``.
    """
    logger.debug(
        "Calculating maintainability score",
        extra={
            "event": "scoring.maintainability.start",
            "complexity_functions": len(complexities),
            "nesting_functions": len(nesting),
            "globals_count": globals_count,
        },
    )
    avg_complexity: float = _average(complexities)
    avg_nesting: float = _average(nesting)

    penalty: float = (
        avg_complexity * _COMPLEXITY_WEIGHT
        + avg_nesting * _NESTING_WEIGHT
        + globals_count * _GLOBALS_WEIGHT
    )

    score: float = max(0.0, min(100.0, 100.0 - penalty))

    if score >= _RISK_LOW_THRESHOLD:
        risk = "LOW"
    elif score >= _RISK_MEDIUM_THRESHOLD:
        risk = "MEDIUM"
    else:
        risk = "HIGH"

    logger.info(
        "Maintainability score calculated",
        extra={"event": "scoring.maintainability.completed", "score": round(score, 2), "risk": risk},
    )

    return {"score": round(score, 2), "risk": risk}
