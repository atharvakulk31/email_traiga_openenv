"""
server/graders.py — Grader classes for Scaler Phase 2 validator.

The validator imports these via openenv.yaml:
    grader: server.graders:EasyGrader
    grader: server.graders:MediumGrader
    grader: server.graders:HardGrader

Pattern mirrors the confirmed working submission (Aarohi1804):
    def grade(self, env, *args, **kwargs) -> float:
        - receives the live EmailTriageEnv instance
        - calls env._grade_task1/2/3() to get the score
        - blanket except → 0.01 (never crashes, always in (0,1))

All scores are strictly between 0 and 1 (never 0.0 or 1.0).
"""


def _clamp(score: float) -> float:
    """Ensure score is strictly between 0 and 1 (exclusive)."""
    return max(0.01, min(0.99, float(score)))


class EasyGrader:
    """Task 1: Email category classification."""

    def grade(self, env=None, *args, **kwargs) -> float:
        try:
            real_env = getattr(env, "unwrapped", env)
            raw_score = float(real_env._grade_task1())
            return _clamp(raw_score)
        except Exception:
            return 0.01

    def __call__(self, *args, **kwargs) -> float:
        return self.grade(*args, **kwargs)

    def describe(self):
        return {"task": "Email Classification", "difficulty": "easy", "weight": 0.5}


class MediumGrader:
    """Task 2: Priority level detection."""

    def grade(self, env=None, *args, **kwargs) -> float:
        try:
            real_env = getattr(env, "unwrapped", env)
            raw_score = float(real_env._grade_task2())
            return _clamp(raw_score)
        except Exception:
            return 0.01

    def __call__(self, *args, **kwargs) -> float:
        return self.grade(*args, **kwargs)

    def describe(self):
        return {"task": "Priority Detection", "difficulty": "medium", "weight": 0.3}


class HardGrader:
    """Task 3: Reply generation quality."""

    def grade(self, env=None, *args, **kwargs) -> float:
        try:
            real_env = getattr(env, "unwrapped", env)
            raw_score = float(real_env._grade_task3())
            return _clamp(raw_score)
        except Exception:
            return 0.01

    def __call__(self, *args, **kwargs) -> float:
        return self.grade(*args, **kwargs)

    def describe(self):
        return {"task": "Reply Generation", "difficulty": "hard", "weight": 0.2}
