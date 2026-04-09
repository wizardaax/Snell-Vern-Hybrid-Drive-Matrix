"""Agent 1: Orchestrator — task routing and coordination."""

from __future__ import annotations

from typing import Any

from . import AgentRole, BaseAgent, Task, TaskType


class OrchestratorAgent(BaseAgent):
    """Routes incoming tasks to specialised agents and coordinates workflows."""

    role = AgentRole.ORCHESTRATOR
    capabilities = frozenset({TaskType.COORDINATION})

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        action = payload.get("action", "route")
        return {
            "status": "completed",
            "agent": self.agent_id,
            "task": task.task_id,
            "action": action,
            "routed": True,
        }
