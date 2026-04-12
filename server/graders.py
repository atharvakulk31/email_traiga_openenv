"""
server/graders.py — Grader classes for Scaler Phase 2 validator.

The validator imports these via openenv.yaml:
    grader: server.graders:EasyGrader
    grader: server.graders:MediumGrader
    grader: server.graders:HardGrader

Supports two calling conventions:
  1. grade(env)                      — env-based: validator passes live EmailTriageEnv
  2. grade(predicted, ground_truth)  — standalone: validator passes strings directly

All scores are strictly between 0 and 1 (exclusive), never 0.0 or 1.0.
"""

import re


def _clamp(score: float) -> float:
    """Ensure score is strictly between 0 and 1 (exclusive). Never 0.0 or 1.0."""
    return max(0.01, min(0.99, float(score)))


def _to_str(val) -> str:
    """Convert any input to a plain string safely."""
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        for key in ("reply", "category", "priority", "text", "content"):
            if key in val and isinstance(val[key], str):
                return val[key]
    return str(val)


_PRIORITY_ORDER = {"low": 0, "medium": 1, "high": 2}

_APOLOGY_KW = [
    "sorry", "apologize", "apologies", "regret", "inconvenience",
    "understand your frustration", "sincerely apologize",
    "we're sorry", "we are sorry",
]
_SOLUTION_KW = [
    "will", "we'll", "resolve", "fix", "refund", "reset", "update",
    "help you", "assist", "investigate", "process", "escalate",
    "follow up", "team will", "happy to", "glad to",
]
_INFORMAL_RE = [
    r"\bhey\b", r"\byo\b", r"\blol\b", r"\bomg\b", r"\bbtw\b",
    r"\bgonna\b", r"\bwanna\b", r"\bdunno\b", r"\bdude\b", r"\bbro\b",
]
_CLOSINGS = [
    "regards", "sincerely", "thank you", "best wishes",
    "warm regards", "kind regards", "respectfully",
]
_SCORE_MAP = {0: 0.01, 1: 0.26, 2: 0.50, 3: 0.74, 4: 0.99}


class EasyGrader:
    """Task 1: Email category classification.

    Returns 0.99 for correct classification, 0.01 for incorrect.
    Supports both env-based and standalone predicted/ground_truth calling.
    """

    def grade(self, predicted=None, ground_truth=None, **kwargs) -> float:
        # Calling convention 1: grade(env) — env object with _grade_task1 method
        if (predicted is not None
                and not isinstance(predicted, (str, int, float, bool))
                and hasattr(predicted, "_grade_task1")):
            try:
                real_env = getattr(predicted, "unwrapped", predicted)
                return _clamp(float(real_env._grade_task1()))
            except Exception:
                pass

        # Calling convention 2: grade(predicted_str, ground_truth_str)
        p = _to_str(predicted).strip().lower()
        g = _to_str(ground_truth).strip().lower()
        if p and g:
            return _clamp(0.99 if p == g else 0.01)

        # Only predicted provided — can't compare, return neutral
        if p:
            return 0.50

        # No meaningful input
        return 0.50

    def __call__(self, *args, **kwargs) -> float:
        predicted = (args[0] if len(args) > 0
                     else kwargs.get("predicted",
                         kwargs.get("action",
                         kwargs.get("env", None))))
        ground_truth = (args[1] if len(args) > 1
                        else kwargs.get("ground_truth",
                            kwargs.get("observation", None)))
        return self.grade(predicted, ground_truth)

    def describe(self):
        return {
            "task": "Email Classification",
            "difficulty": "easy",
            "scoring": "0.99 correct / 0.01 incorrect",
            "weight": 0.5,
        }


class MediumGrader:
    """Task 2: Priority level detection.

    Returns 0.99 exact match, 0.50 adjacent level, 0.01 two levels off.
    Supports both env-based and standalone calling.
    """

    def grade(self, predicted=None, ground_truth=None, **kwargs) -> float:
        # Calling convention 1: grade(env)
        if (predicted is not None
                and not isinstance(predicted, (str, int, float, bool))
                and hasattr(predicted, "_grade_task2")):
            try:
                real_env = getattr(predicted, "unwrapped", predicted)
                return _clamp(float(real_env._grade_task2()))
            except Exception:
                pass

        # Calling convention 2: grade(predicted_str, ground_truth_str)
        p = _to_str(predicted).strip().lower()
        g = _to_str(ground_truth).strip().lower()
        pred_lvl = _PRIORITY_ORDER.get(p)
        truth_lvl = _PRIORITY_ORDER.get(g)
        if pred_lvl is not None and truth_lvl is not None:
            diff = abs(pred_lvl - truth_lvl)
            return _clamp({0: 0.99, 1: 0.50}.get(diff, 0.01))

        # Neutral default
        return 0.50

    def __call__(self, *args, **kwargs) -> float:
        predicted = (args[0] if len(args) > 0
                     else kwargs.get("predicted",
                         kwargs.get("action",
                         kwargs.get("env", None))))
        ground_truth = (args[1] if len(args) > 1
                        else kwargs.get("ground_truth",
                            kwargs.get("observation", None)))
        return self.grade(predicted, ground_truth)

    def describe(self):
        return {
            "task": "Priority Detection",
            "difficulty": "medium",
            "scoring": "0.99 exact / 0.50 adjacent / 0.01 two-off",
            "weight": 0.3,
        }


class HardGrader:
    """Task 3: Reply generation quality.

    4 checks: apology/empathy, solution/next-step, professional tone, subject relevance.
    Scores: 0.99/0.74/0.50/0.26/0.01 for 4/3/2/1/0 checks passed.
    Supports both env-based and standalone calling.
    """

    def grade(self, predicted=None, ground_truth=None, **kwargs) -> float:
        # Calling convention 1: grade(env)
        if (predicted is not None
                and not isinstance(predicted, (str, int, float, bool))
                and hasattr(predicted, "_grade_task3")):
            try:
                real_env = getattr(predicted, "unwrapped", predicted)
                return _clamp(float(real_env._grade_task3()))
            except Exception:
                pass

        # Calling convention 2: grade(reply_str, subject_str)
        reply = _to_str(predicted).lower()
        subject = _to_str(ground_truth).lower()
        checks = 0

        # Check 1: Apology / empathy
        if any(kw in reply for kw in _APOLOGY_KW):
            checks += 1

        # Check 2: Solution / next step
        if any(kw in reply for kw in _SOLUTION_KW):
            checks += 1

        # Check 3: Professional tone
        informal = any(re.search(p, reply) for p in _INFORMAL_RE)
        has_closing = any(kw in reply for kw in _CLOSINGS)
        long_enough = len(reply.split()) >= 20
        if (not informal) and has_closing and long_enough:
            checks += 1

        # Check 4: Addresses email subject
        words = set(re.findall(r"\b\w{4,}\b", subject))
        stops = {"your", "with", "this", "that", "have", "from",
                 "will", "they", "when", "what", "been", "does"}
        relevant = words - stops
        if relevant and any(w in reply for w in relevant):
            checks += 1

        return _clamp(_SCORE_MAP.get(checks, 0.01))

    def __call__(self, *args, **kwargs) -> float:
        predicted = (args[0] if len(args) > 0
                     else kwargs.get("predicted",
                         kwargs.get("action",
                         kwargs.get("env", None))))
        ground_truth = (args[1] if len(args) > 1
                        else kwargs.get("ground_truth",
                            kwargs.get("observation", None)))
        return self.grade(predicted, ground_truth)

    def describe(self):
        return {
            "task": "Reply Generation",
            "difficulty": "hard",
            "scoring": "4 checks: apology, solution, tone, relevance",
            "weight": 0.2,
        }
