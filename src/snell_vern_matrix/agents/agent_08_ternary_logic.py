"""Agent 8: Ternary_Logic — 3-state operations."""

from __future__ import annotations

from typing import Any

from ..self_model import _ternary_stability, _update_ternary_balance
from . import AgentRole, BaseAgent, Task, TaskType


class TernaryLogicAgent(BaseAgent):
    """Handles ternary (3-state) logic operations and balance tracking."""

    role = AgentRole.TERNARY_LOGIC
    capabilities = frozenset({TaskType.TERNARY})

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        action = payload.get("action", "evaluate")

        if action == "evaluate":
            balance = tuple(
                float(x) for x in payload.get("ternary_balance", (0.0, 0.0, 0.0))
            )
            stability = _ternary_stability(balance)
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "stability": stability.value,
                "balance": list(balance),
            }
        elif action == "update":
            current = tuple(float(x) for x in payload.get("current", (0.0, 0.0, 0.0)))
            delta = float(payload.get("delta", 0.0))
            new_balance = _update_ternary_balance(current, delta)
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "balance": list(new_balance),
                "stability": _ternary_stability(new_balance).value,
            }
        else:
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "noop",
            }
