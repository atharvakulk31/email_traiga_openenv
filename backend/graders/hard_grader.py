"""
Hard Grader — Task 3: Reply Generation Quality.

Checks (each worth 1/4 of the score):
  1. Apology/empathy present
  2. Solution or next step provided
  3. Professional tone maintained
  4. Addresses the specific email subject
"""

import re
from typing import Tuple, Dict


APOLOGY_KEYWORDS = [
    "sorry", "apologize", "apologies", "regret", "understand your frustration",
    "sincerely apologize", "we're sorry", "we are sorry", "inconvenience",
    "we understand", "deeply regret"
]

SOLUTION_KEYWORDS = [
    "will", "can", "we'll", "we will", "please", "steps", "resolve",
    "fix", "refund", "reset", "update", "help you", "assist", "look into",
    "investigate", "send", "process", "escalate", "contact", "follow up",
    "happy to", "glad to", "reach out", "team will"
]

# Word-boundary regex patterns — prevents "yo" matching "you", "sup" matching "support"
INFORMAL_PATTERNS = [
    r"\bhey\b", r"\byo\b", r"\blol\b", r"\bomg\b", r"\bbtw\b",
    r"\bgonna\b", r"\bwanna\b", r"\bdunno\b", r"\bdude\b", r"\bbro\b",
    r"\bnah\b", r"\byep\b", r"\byup\b", r"\bpls\b", r"\bthx\b", r"\bok so\b"
]

PROFESSIONAL_CLOSINGS = [
    "regards", "sincerely", "thank you", "best wishes",
    "warm regards", "kind regards", "yours truly", "respectfully"
]


class HardGrader:
    """Grades reply quality on 4 dimensions (Task 3)."""

    def grade(self, reply: str, email) -> Tuple[float, Dict]:
        reply_lower = reply.lower()
        detail: Dict[str, bool] = {}

        # Check 1: Apology / empathy
        detail["apology_present"] = any(kw in reply_lower for kw in APOLOGY_KEYWORDS)

        # Check 2: Solution / next step
        detail["solution_provided"] = any(kw in reply_lower for kw in SOLUTION_KEYWORDS)

        # Check 3: Professional tone — regex word boundaries fix substring bug
        has_informal = any(re.search(p, reply_lower) for p in INFORMAL_PATTERNS)
        has_closing  = any(kw in reply_lower for kw in PROFESSIONAL_CLOSINGS)
        has_min_len  = len(reply.split()) >= 20
        detail["professional_tone"] = (not has_informal) and has_closing and has_min_len

        # Check 4: Addresses email subject
        subject_words = set(re.findall(r"\b\w{4,}\b", email.subject.lower()))
        stop_words = {"your", "with", "this", "that", "have", "from", "will",
                      "they", "when", "what", "where", "been", "does", "please"}
        relevant_words = subject_words - stop_words
        detail["addresses_subject"] = any(w in reply_lower for w in relevant_words)

        checks_passed = sum(detail.values())
        score = round(checks_passed / 4.0, 4)

        return score, detail

    def describe(self) -> dict:
        return {
            "task": "Reply Generation",
            "difficulty": "Hard",
            "description": "Agent must draft a professional customer support reply.",
            "scoring": "0.25 per check: apology, solution, professional tone, addresses subject",
            "weight": 0.2
        }
