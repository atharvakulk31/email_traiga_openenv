"""
EmailTriageEnv — OpenEnv-compliant email triage environment.

Spec:
  reset()  -> Observation
  step(action) -> (Observation, Reward, done, info)
  state()  -> StateResponse
"""

import json
import random
import os
from typing import Optional, Tuple, Dict, Any

from backend.models import (
    Email, Observation, Action, Reward,
    StepResponse, StateResponse
)
from backend.graders.easy_grader import EasyGrader
from backend.graders.medium_grader import MediumGrader
from backend.graders.hard_grader import HardGrader


DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "emails.json")


class EmailTriageEnv:
    """OpenEnv email triage environment."""

    VALID_CATEGORIES = ["Billing Refund", "Account", "Feature Request", "Technical Support"]
    VALID_PRIORITIES = ["Low", "Medium", "High"]

    def __init__(self):
        self._emails: list[Email] = []
        self._current_email: Optional[Email] = None
        self._step_count: int = 0
        self._total_score: float = 0.0
        self._done: bool = False
        self._history: list[Dict[str, Any]] = []

        self._easy_grader = EasyGrader()
        self._medium_grader = MediumGrader()
        self._hard_grader = HardGrader()

        self._load_emails()

    def _load_emails(self) -> None:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self._emails = [Email(**e) for e in raw]

    def reset(self, email_id: Optional[str] = None) -> Observation:
        """Reset environment with a random (or specified) email."""
        if email_id:
            matches = [e for e in self._emails if e.id == email_id]
            self._current_email = matches[0] if matches else random.choice(self._emails)
        else:
            self._current_email = random.choice(self._emails)

        self._step_count = 0
        self._total_score = 0.0
        self._done = False
        self._history = []

        return self._build_observation()

    def step(self, action: Action) -> StepResponse:
        """
        Evaluate an action and return (observation, reward, done, info).

        Reward formula:
          reward = 0.5 * category_correct
                 + 0.3 * priority_correct
                 + 0.2 * reply_quality
        Penalties:
          invalid action  → -0.2
          empty reply     → -0.1 (when reply is expected)
        """
        if self._current_email is None:
            raise RuntimeError("Environment not reset. Call reset() first.")

        self._step_count += 1
        breakdown: Dict[str, Any] = {}
        penalty = 0.0
        explanation_parts = []

        # --- Validate action fields ---
        if action.category and action.category not in self.VALID_CATEGORIES:
            penalty += 0.2
            explanation_parts.append(f"Invalid category '{action.category}' (-0.20).")

        if action.priority and action.priority not in self.VALID_PRIORITIES:
            penalty += 0.2
            explanation_parts.append(f"Invalid priority '{action.priority}' (-0.20).")

        # --- Category grading (Task 1) ---
        cat_score = 0.0
        if action.category:
            cat_score = self._easy_grader.grade(
                predicted=action.category,
                ground_truth=self._current_email.category.value
            )
            breakdown["category"] = {
                "predicted": action.category,
                "expected": self._current_email.category.value,
                "score": cat_score
            }
            explanation_parts.append(
                f"Category {'correct' if cat_score == 1.0 else 'incorrect'} "
                f"(predicted: {action.category}, expected: {self._current_email.category.value}, "
                f"weight: 0.50, contribution: {0.5 * cat_score:.2f})."
            )

        # --- Priority grading (Task 2) ---
        pri_score = 0.0
        if action.priority:
            pri_score = self._medium_grader.grade(
                predicted=action.priority,
                ground_truth=self._current_email.priority.value
            )
            breakdown["priority"] = {
                "predicted": action.priority,
                "expected": self._current_email.priority.value,
                "score": pri_score
            }
            explanation_parts.append(
                f"Priority {'correct' if pri_score == 1.0 else 'incorrect'} "
                f"(predicted: {action.priority}, expected: {self._current_email.priority.value}, "
                f"weight: 0.30, contribution: {0.3 * pri_score:.2f})."
            )

        # --- Reply grading (Task 3) ---
        reply_score = 0.0
        if action.reply is not None:
            if not action.reply.strip():
                penalty += 0.1
                explanation_parts.append("Empty reply (-0.10).")
            else:
                reply_score, reply_detail = self._hard_grader.grade(
                    reply=action.reply,
                    email=self._current_email
                )
                breakdown["reply"] = {
                    "score": reply_score,
                    "detail": reply_detail
                }
                explanation_parts.append(
                    f"Reply quality score: {reply_score:.2f} "
                    f"(weight: 0.20, contribution: {0.2 * reply_score:.2f}). "
                    f"Checks: {reply_detail}."
                )

        # --- Final score ---
        raw_score = (0.5 * cat_score) + (0.3 * pri_score) + (0.2 * reply_score)
        final_score = max(0.0, raw_score - penalty)

        self._total_score += final_score
        self._done = True  # single-step episode per email

        step_record = {
            "step": self._step_count,
            "action": action.model_dump(),
            "score": final_score,
            "breakdown": breakdown
        }
        self._history.append(step_record)

        reward = Reward(
            score=round(final_score, 4),
            explanation=" ".join(explanation_parts) if explanation_parts else "No action fields provided.",
            breakdown=breakdown
        )

        return StepResponse(
            observation=self._build_observation(),
            reward=reward,
            done=self._done,
            info={"step": self._step_count, "total_score": self._total_score}
        )

    def state(self) -> StateResponse:
        """Return the current environment state."""
        return StateResponse(
            email_id=self._current_email.id if self._current_email else None,
            current_email=self._current_email,
            step_count=self._step_count,
            total_score=round(self._total_score, 4),
            done=self._done,
            history=self._history
        )

    def get_all_emails(self) -> list[Email]:
        return self._emails

    def get_email_by_id(self, email_id: str) -> Optional[Email]:
        for e in self._emails:
            if e.id == email_id:
                return e
        return None

    def _build_observation(self) -> Observation:
        if self._current_email is None:
            raise RuntimeError("No current email loaded.")
        return Observation(
            email_id=self._current_email.id,
            subject=self._current_email.subject,
            body=self._current_email.body,
            sender=self._current_email.sender,
            history=[str(h) for h in self._history]
        )
