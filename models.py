"""
Root-level models.py — required by OpenEnv environment structure spec.

Re-exports the Action / Observation classes used by this environment as
proper openenv-core types so that the validator can introspect them.
"""

from typing import List, Optional
from pydantic import Field, ConfigDict

from openenv.core.env_server.types import Action as _BaseAction, Observation as _BaseObservation


class EmailTriageAction(_BaseAction):
    """Action for the Email Triage environment.

    The agent submits one or more of: predicted category, predicted priority,
    and a drafted reply. All fields are optional so the agent can act on a
    subset of tasks per step.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    category: Optional[str] = Field(default=None, description="Predicted email category")
    priority: Optional[str] = Field(default=None, description="Predicted email priority")
    reply: Optional[str] = Field(default=None, description="Drafted customer support reply")


class EmailTriageObservation(_BaseObservation):
    """Observation for the Email Triage environment — the email to triage."""

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    email_id: str = Field(default="", description="ID of the current email")
    subject: str = Field(default="", description="Email subject line")
    body: str = Field(default="", description="Email body text")
    sender: str = Field(default="", description="Email sender address")
    history: List[str] = Field(default_factory=list, description="Previous step history")


# Aliases to match the names used by client.py / __init__.py
Action = EmailTriageAction
Observation = EmailTriageObservation


__all__ = [
    "EmailTriageAction",
    "EmailTriageObservation",
    "Action",
    "Observation",
]
