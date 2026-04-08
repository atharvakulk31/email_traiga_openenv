"""
Easy Grader — Task 1: Email Category Classification.

Binary score: 1.0 if category matches ground truth, 0.0 otherwise.
"""


class EasyGrader:
    """Grades email category classification (Task 1)."""

    def grade(self, predicted: str, ground_truth: str) -> float:
        """
        Returns:
            1.0 if predicted matches ground_truth (case-insensitive)
            0.0 otherwise
        """
        return 1.0 if predicted.strip().lower() == ground_truth.strip().lower() else 0.0

    def describe(self) -> dict:
        return {
            "task": "Email Classification",
            "difficulty": "Easy",
            "description": "Agent must correctly classify the email into one of: "
                           "Billing Refund, Account, Feature Request, Technical Support.",
            "scoring": "Binary: 1.0 (correct) or 0.0 (incorrect)",
            "weight": 0.5
        }
