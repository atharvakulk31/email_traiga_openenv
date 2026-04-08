"""
Medium Grader — Task 2: Priority Detection.

Scoring:
  Exact match → 1.0
  Off by 1 level → 0.5
  Off by 2 levels → 0.0
"""

PRIORITY_ORDER = {"Low": 0, "Medium": 1, "High": 2}


class MediumGrader:
    """Grades priority detection (Task 2) with partial credit."""

    def grade(self, predicted: str, ground_truth: str) -> float:
        """
        Returns:
            1.0  — exact match
            0.5  — adjacent priority (off by one level)
            0.0  — two levels off
        """
        pred_norm = predicted.strip().capitalize()
        truth_norm = ground_truth.strip().capitalize()

        pred_level = PRIORITY_ORDER.get(pred_norm)
        truth_level = PRIORITY_ORDER.get(truth_norm)

        if pred_level is None or truth_level is None:
            return 0.0

        diff = abs(pred_level - truth_level)
        if diff == 0:
            return 1.0
        elif diff == 1:
            return 0.5
        else:
            return 0.0

    def describe(self) -> dict:
        return {
            "task": "Priority Detection",
            "difficulty": "Medium",
            "description": "Agent must detect the urgency level: Low, Medium, or High.",
            "scoring": "1.0 (exact), 0.5 (adjacent level), 0.0 (two levels off)",
            "weight": 0.3
        }
