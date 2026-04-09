"""
Easy Grader — Task 1: Email Category Classification.

Scores are strictly between 0 and 1 (exclusive), required by OpenEnv Phase 2:
  correct   → 0.99
  incorrect → 0.01
"""

SCORE_CORRECT   = 0.99
SCORE_INCORRECT = 0.01


def _clamp(score: float) -> float:
    """Ensure score is strictly between 0 and 1 (exclusive)."""
    return max(0.01, min(0.99, score))


class EasyGrader:
    """Grades email category classification (Task 1)."""

    def grade(self, predicted: str, ground_truth: str = "") -> float:
        """
        Returns:
            0.99 if predicted matches ground_truth (case-insensitive)
            0.01 otherwise
        """
        match = predicted.strip().lower() == ground_truth.strip().lower()
        return _clamp(SCORE_CORRECT if match else SCORE_INCORRECT)

    def describe(self) -> dict:
        return {
            "task": "Email Classification",
            "difficulty": "Easy",
            "description": "Agent must correctly classify the email into one of: "
                           "Billing Refund, Account, Feature Request, Technical Support.",
            "scoring": "0.99 (correct) or 0.01 (incorrect)",
            "weight": 0.5
        }
