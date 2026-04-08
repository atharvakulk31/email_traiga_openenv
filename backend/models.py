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


class StepResponse(BaseModel):
    observation: Optional[Observation] = None
    reward: Reward
    done: bool
    info: Dict[str, Any] = {}


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
    observation: Observation
    message: str


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
