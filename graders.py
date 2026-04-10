"""
graders.py — Standalone grader classes at repo root.

Imported by Scaler's Phase 2 validator via openenv.yaml:
    grader: graders:EasyGrader
    grader: graders:MediumGrader
    grader: graders:HardGrader

Each grader is completely standalone (zero external dependencies).
grade() is bulletproof — handles None, dicts, ints, or any input
without crashing. Always returns float strictly in (0, 1).
"""

import re


# ── Safe string coercion ─────────────────────────────────────────────────────

def _to_str(val) -> str:
    """Convert any input to a plain string safely. None → ''."""
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        # If passed an action/observation dict, extract the most useful field
        for key in ("reply", "category", "priority", "text", "content"):
            if key in val and isinstance(val[key], str):
                return val[key]
        return str(val)
    return str(val)


def _clamp(score: float) -> float:
    """Ensure score is strictly between 0 and 1 (exclusive). Never 0.0 or 1.0."""
    return max(0.01, min(0.99, float(score)))


# ── Task 1: Email Classification (Easy) ─────────────────────────────────────

class EasyGrader:
    """Binary grader — 0.99 if predicted category matches ground truth, else 0.01."""

    def grade(self, predicted=None, ground_truth=None) -> float:
        p = _to_str(predicted).strip().lower()
        g = _to_str(ground_truth).strip().lower()
        return _clamp(0.99 if (p == g and p != "") else 0.01)

    def __call__(self, *args, **kwargs) -> float:
        predicted    = args[0] if len(args) > 0 else kwargs.get("predicted", kwargs.get("action", None))
        ground_truth = args[1] if len(args) > 1 else kwargs.get("ground_truth", kwargs.get("observation", None))
        return self.grade(predicted, ground_truth)

    def describe(self):
        return {"task": "Email Classification", "difficulty": "easy",
                "scoring": "0.99 correct / 0.01 incorrect", "weight": 0.5}


# ── Task 2: Priority Detection (Medium) ──────────────────────────────────────

_PRIORITY_ORDER = {"low": 0, "medium": 1, "high": 2}


class MediumGrader:
    """Priority grader — partial credit for adjacent levels."""

    def grade(self, predicted=None, ground_truth=None) -> float:
        p = _to_str(predicted).strip().lower()
        g = _to_str(ground_truth).strip().lower()
        pred_lvl  = _PRIORITY_ORDER.get(p)
        truth_lvl = _PRIORITY_ORDER.get(g)
        if pred_lvl is None or truth_lvl is None:
            return 0.01
        diff = abs(pred_lvl - truth_lvl)
        return _clamp({0: 0.99, 1: 0.50}.get(diff, 0.01))

    def __call__(self, *args, **kwargs) -> float:
        predicted    = args[0] if len(args) > 0 else kwargs.get("predicted", kwargs.get("action", None))
        ground_truth = args[1] if len(args) > 1 else kwargs.get("ground_truth", kwargs.get("observation", None))
        return self.grade(predicted, ground_truth)

    def describe(self):
        return {"task": "Priority Detection", "difficulty": "medium",
                "scoring": "0.99 exact / 0.50 adjacent / 0.01 two-off", "weight": 0.3}


# ── Task 3: Reply Generation (Hard) ──────────────────────────────────────────

_APOLOGY_KW = [
    "sorry", "apologize", "apologies", "regret", "inconvenience",
    "understand your frustration", "sincerely apologize",
]
_SOLUTION_KW = [
    "will", "we'll", "resolve", "fix", "refund", "reset", "update",
    "help you", "assist", "investigate", "process", "escalate",
    "follow up", "team will", "happy to",
]
_INFORMAL_RE = [
    r"\bhey\b", r"\byo\b", r"\blol\b", r"\bomg\b", r"\bbtw\b",
    r"\bgonna\b", r"\bwanna\b", r"\bdunno\b", r"\bdude\b", r"\bbro\b",
]
_CLOSINGS = ["regards", "sincerely", "thank you", "best wishes",
             "warm regards", "kind regards", "respectfully"]
_SCORE_MAP = {0: 0.01, 1: 0.26, 2: 0.50, 3: 0.74, 4: 0.99}


class HardGrader:
    """Reply quality grader — 4 checks, partial credit per check passed."""

    def grade(self, predicted=None, ground_truth=None) -> float:
        reply   = _to_str(predicted).lower()
        subject = _to_str(ground_truth).lower()
        checks  = 0

        # 1. Apology / empathy present
        if any(kw in reply for kw in _APOLOGY_KW):
            checks += 1
        # 2. Solution / next step present
        if any(kw in reply for kw in _SOLUTION_KW):
            checks += 1
        # 3. Professional tone
        informal    = any(re.search(p, reply) for p in _INFORMAL_RE)
        has_closing = any(kw in reply for kw in _CLOSINGS)
        long_enough = len(reply.split()) >= 20
        if (not informal) and has_closing and long_enough:
            checks += 1
        # 4. Addresses subject content
        words    = set(re.findall(r"\b\w{4,}\b", subject))
        stops    = {"your", "with", "this", "that", "have", "from",
                    "will", "they", "when", "what", "been", "does"}
        relevant = words - stops
        if relevant and any(w in reply for w in relevant):
            checks += 1

        return _clamp(_SCORE_MAP.get(checks, 0.01))

    def __call__(self, *args, **kwargs) -> float:
        predicted    = args[0] if len(args) > 0 else kwargs.get("predicted", kwargs.get("action", None))
        ground_truth = args[1] if len(args) > 1 else kwargs.get("ground_truth", kwargs.get("observation", None))
        return self.grade(predicted, ground_truth)

    def describe(self):
        return {"task": "Reply Generation", "difficulty": "hard",
                "scoring": "4 checks: apology, solution, tone, relevance", "weight": 0.2}
