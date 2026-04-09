"""Agent 6: Lucas_Analyst — sequence math and convergence analysis."""

from __future__ import annotations

from typing import Any

from recursive_field_math import PHI, L, ratio

from . import AgentRole, BaseAgent, Task, TaskType


class LucasAnalystAgent(BaseAgent):
    """Performs Lucas sequence analysis and convergence checks."""

    role = AgentRole.LUCAS_ANALYST
    capabilities = frozenset({TaskType.MATH})

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        action = payload.get("action", "sequence")
        n = int(payload.get("n", 10))

        if action == "sequence":
            values = {str(i): L(i) for i in range(n + 1)}
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "sequence",
                "values": values,
            }
        elif action == "convergence":
            rat = ratio(max(n, 1))
            error = abs(rat - PHI)
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "convergence",
                "ratio": rat,
                "phi": PHI,
                "error": error,
                "converged": error < 1e-6,
            }
        else:
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "noop",
            }
