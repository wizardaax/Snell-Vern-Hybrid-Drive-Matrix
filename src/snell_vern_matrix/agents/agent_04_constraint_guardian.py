"""Agent 4: Constraint_Guardian — SCE-88 validation."""

from __future__ import annotations

from typing import Any

from . import AgentRole, BaseAgent, Task, TaskType


class ConstraintGuardianAgent(BaseAgent):
    """Validates outputs against SCE-88 constraint topology."""

    role = AgentRole.CONSTRAINT_GUARDIAN
    capabilities = frozenset({TaskType.CONSTRAINT})

    def execute(self, task: Task) -> dict[str, Any]:
        from ..self_model import (
            _validate_coherence,
            _validate_ternary_balance,
            _validate_uncertainty,
        )

        payload = task.payload
        violations: list[str] = []

        coherence = payload.get("coherence_score")
        if coherence is not None:
            try:
                _validate_coherence(float(coherence))
            except Exception as exc:
                violations.append(str(exc))

        uncertainty = payload.get("uncertainty")
        if uncertainty is not None:
            try:
                _validate_uncertainty(float(uncertainty))
            except Exception as exc:
                violations.append(str(exc))

        ternary = payload.get("ternary_balance")
        if ternary is not None:
            try:
                _validate_ternary_balance(tuple(float(x) for x in ternary))
            except Exception as exc:
                violations.append(str(exc))

        return {
            "status": "completed",
            "agent": self.agent_id,
            "task": task.task_id,
            "valid": len(violations) == 0,
            "violations": violations,
        }
