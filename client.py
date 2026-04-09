"""
Root-level client.py — required by OpenEnv environment structure spec.

Provides an EnvClient subclass for the Email Triage environment so external
tools (and the validator) can connect to the running server.
"""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from models import EmailTriageAction, EmailTriageObservation


class EmailTriageEnv(EnvClient[EmailTriageAction, EmailTriageObservation, State]):
    """Client for the Email Triage Environment.

    Connects to a running Email Triage server (HuggingFace Space, Docker, or
    local uvicorn) and provides reset() / step() / state() methods.
    """

    def _step_payload(self, action: EmailTriageAction) -> Dict:
        return {
            "category": action.category,
            "priority": action.priority,
            "reply": action.reply,
        }

    def _parse_result(self, payload: Dict) -> StepResult[EmailTriageObservation]:
        obs_data = payload.get("observation", {}) or {}
        reward_obj = payload.get("reward")
        # Server returns reward as either a float or a {score, ...} dict
        reward_value = reward_obj.get("score") if isinstance(reward_obj, dict) else reward_obj

        observation = EmailTriageObservation(
            email_id=obs_data.get("email_id", ""),
            subject=obs_data.get("subject", ""),
            body=obs_data.get("body", ""),
            sender=obs_data.get("sender", ""),
            history=obs_data.get("history", []),
            done=payload.get("done", False),
            reward=reward_value,
        )

        return StepResult(
            observation=observation,
            reward=reward_value,
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("email_id"),
            step_count=payload.get("step_count", 0),
        )


__all__ = ["EmailTriageEnv"]
