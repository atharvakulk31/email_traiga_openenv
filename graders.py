"""
graders.py — Standalone grader classes at repo root.

Scaler's Phase 2 validator imports graders by dotted path from openenv.yaml.
These classes have ZERO external dependencies (no fastapi, pydantic, etc.)
so they're importable in any Python environment the validator may use.

Each grader exposes:
    .grade(predicted: str, ground_truth: str) -> float
        Returns a score strictly in (0, 1) — never 0.0 or 1.0.
"""

import re

# ─── Score Clamping ──────────────────────────────────────────────────────────

def _clamp(score: float) -> float:
    """Ensure score is strictly between 0 and 1 (exclusive)."""
    return max(0.01, min(0.99, score))


# ─── Task 1: Email Classification (Easy) ────────────────────────────────────

class EasyGrader:
    """Binary classification grader — correct category or not."""

    def grade(self, predicted: str, ground_truth: str = "") -> float:
        match = predicted.strip().lower() == ground_truth.strip().lower()
        return _clamp(0.99 if match else 0.01)

    def describe(self):
        return {
            "task": "Email Classification",
            "difficulty": "Easy",
            "scoring": "0.99 (correct) or 0.01 (incorrect)",
            "weight": 0.5,
        }


# ─── Task 2: Priority Detection (Medium) ────────────────────────────────────

_PRIORITY_ORDER = {"Low": 0, "Medium": 1, "High": 2}


class MediumGrader:
    """Priority grader with partial credit for adjacent levels."""

    def grade(self, predicted: str, ground_truth: str = "") -> float:
        pred  = _PRIORITY_ORDER.get(predicted.strip().capitalize())
        truth = _PRIORITY_ORDER.get(ground_truth.strip().capitalize())
        if pred is None or truth is None:
            return 0.01
        diff = abs(pred - truth)
        return _clamp({0: 0.99, 1: 0.50}.get(diff, 0.01))

    def describe(self):
        return {
            "task": "Priority Detection",
            "difficulty": "Medium",
            "scoring": "0.99 (exact), 0.50 (adjacent), 0.01 (two off)",
            "weight": 0.3,
        }


# ─── Task 3: Reply Generation (Hard) ────────────────────────────────────────

_APOLOGY_KW = [
    "sorry", "apologize", "apologies", "regret", "inconvenience",
    "understand your frustration", "sincerely apologize",
]
_SOLUTION_KW = [
    "will", "can", "we'll", "please", "resolve", "fix", "refund",
    "reset", "update", "help you", "assist", "investigate", "process",
    "escalate", "follow up", "team will", "happy to",
]
_INFORMAL_RE = [
    r"\bhey\b", r"\byo\b", r"\blol\b", r"\bomg\b", r"\bbtw\b",
    r"\bgonna\b", r"\bwanna\b", r"\bdunno\b", r"\bdude\b", r"\bbro\b",
    r"\bnah\b", r"\byep\b", r"\byup\b", r"\bpls\b", r"\bthx\b",
]
_CLOSINGS = [
    "regards", "sincerely", "thank you", "best wishes",
    "warm regards", "kind regards", "respectfully",
]
_SCORE_MAP = {0: 0.01, 1: 0.26, 2: 0.50, 3: 0.74, 4: 0.99}


class HardGrader:
    """Reply quality grader — 4 checks, partial credit."""

    def grade(self, predicted: str, ground_truth: str = "") -> float:
        reply = predicted.lower()
        subject = ground_truth.lower() if isinstance(ground_truth, str) else ""
        checks = 0
        # 1. Apology / empathy
        if any(kw in reply for kw in _APOLOGY_KW):
            checks += 1
        # 2. Solution / next step
        if any(kw in reply for kw in _SOLUTION_KW):
            checks += 1
        # 3. Professional tone
        informal = any(re.search(p, reply) for p in _INFORMAL_RE)
        closing = any(kw in reply for kw in _CLOSINGS)
        long_enough = len(predicted.split()) >= 20
        if (not informal) and closing and long_enough:
            checks += 1
        # 4. Addresses subject
        words = set(re.findall(r"\b\w{4,}\b", subject))
        stops = {"your", "with", "this", "that", "have", "from", "will",
                 "they", "when", "what", "where", "been", "does", "please"}
        relevant = words - stops
        if relevant and any(w in reply for w in relevant):
            checks += 1
        return _clamp(_SCORE_MAP.get(checks, 0.01))

    def describe(self):
        return {
            "task": "Reply Generation",
            "difficulty": "Hard",
            "scoring": "4 checks: apology, solution, tone, relevance",
            "weight": 0.2,
        }
