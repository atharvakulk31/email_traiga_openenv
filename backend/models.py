from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum


class EmailCategory(str, Enum):
    BILLING_REFUND = "Billing Refund"
    ACCOUNT = "Account"
    FEATURE_REQUEST = "Feature Request"
    TECHNICAL_SUPPORT = "Technical Support"


class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Email(BaseModel):
    id: str
    subject: str
    body: str
    sender: str
    category: EmailCategory
    priority: Priority
    timestamp: Optional[str] = None


class Observation(BaseModel):
    email_id: str
    subject: str
    body: str
    sender: str
    history: List[str] = []


class Action(BaseModel):
    category: Optional[str] = None
    priority: Optional[str] = None
    reply: Optional[str] = None


class Reward(BaseModel):
    score: float
    explanation: str
    breakdown: Optional[Dict[str, Any]] = None


class TaskScore(BaseModel):
    """Per-task graded score — required by OpenEnv Phase 2 validator."""
    task_id: str
    name: str
    grader: str
    score: float   # strictly between 0.0 and 1.0 (exclusive)
    weight: float


class StepResponse(BaseModel):
    """
    OpenEnv-compliant step response.

    IMPORTANT: `reward` must be a FLOAT (not an object) to satisfy
    openenv-core's StepResponse schema, which has `reward: Optional[float]`
    with `extra="forbid"`. The Scaler Phase 2 validator parses responses
    through openenv-core types and silently fails on type mismatches —
    that's why all 12 prior submissions reported "tasks with graders" errors.

    The rich reward info (explanation, breakdown) is preserved in
    `reward_detail` for our frontend/CLI use.
    """
    observation: Optional[Observation] = None
    reward: float                         # ← FLOAT scalar, openenv-core compliant
    done: bool
    info: Dict[str, Any] = {}
    tasks: List[TaskScore] = []           # ≥3 tasks required by OpenEnv Phase 2
    reward_detail: Optional[Reward] = None  # full explanation/breakdown for frontend


class StateResponse(BaseModel):
    email_id: Optional[str] = None
    current_email: Optional[Email] = None
    step_count: int
    total_score: float
    done: bool
    history: List[Dict[str, Any]] = []


class TaskInfo(BaseModel):
    id: str
    name: str
    description: str
    difficulty: str
    max_score: float
    grader: str


class ResetResponse(BaseModel):
    """openenv-core compatible reset response (extra fields omitted to avoid extra='forbid' rejection)."""
    observation: Observation
    reward: Optional[float] = None
    done: bool = False


class EmailListResponse(BaseModel):
    emails: List[Email]
    total: int


class SimulationRequest(BaseModel):
    email_id: Optional[str] = None
    task_ids: Optional[List[str]] = None


class SimulationResult(BaseModel):
    model_config = {"protected_namespaces": ()}

    email_id: str
    subject: str
    task_results: List[Dict[str, Any]]
    total_score: float
    model_used: str
