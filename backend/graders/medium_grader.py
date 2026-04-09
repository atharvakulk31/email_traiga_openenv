"""
Medium Grader — Task 2: Priority Detection.

Scores are strictly between 0 and 1 (exclusive), required by OpenEnv Phase 2:
  Exact match  → 0.99
  Off by 1     → 0.50
  Off by 2     → 0.01
"""

PRIORITY_ORDER = {"Low": 0, "Medium": 1, "High": 2}


def _clamp(score: float) -> float:
    """Ensure score is strictly between 0 and 1 (exclusive)."""
    return max(0.01, min(0.99, score))


class MediumGrader:
    """Grades priority detection (Task 2) with partial credit."""

    def grade(self, predicted: str, ground_truth: str = "") -> float:
        """
        Returns:
            0.99 — exact match
            0.50 — adjacent priority (off by one level)
            0.01 — two levels off or invalid input
        """
        pred_norm  = predicted.strip().capitalize()
        truth_norm = ground_truth.strip().capitalize()

        pred_level  = PRIORITY_ORDER.get(pred_norm)
        truth_level = PRIORITY_ORDER.get(truth_norm)

        if pred_level is None or truth_level is None:
            return 0.01

        diff = abs(pred_level - truth_level)
        if diff == 0:
            raw = 0.99
        elif diff == 1:
            raw = 0.50
        else:
            raw = 0.01

        return _clamp(raw)

    def describe(self) -> dict:
        return {
            "task": "Priority Detection",
            "difficulty": "Medium",
            "description": "Agent must detect the urgency level: Low, Medium, or High.",
            "scoring": "0.99 (exact), 0.50 (adjacent level), 0.01 (two levels off)",
            "weight": 0.3
        }
