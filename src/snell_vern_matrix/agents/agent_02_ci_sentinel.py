"""Agent 2: CI_Sentinel — monitor and maintain CI health."""

from __future__ import annotations

from typing import Any

from . import AgentRole, BaseAgent, Task, TaskType


class CISentinelAgent(BaseAgent):
    """Monitors CI pipelines and reports health status."""

    role = AgentRole.CI_SENTINEL
    capabilities = frozenset({TaskType.CI_HEALTH})

    def __init__(self, agent_id: str) -> None:
        super().__init__(agent_id)
        self._pipeline_status: dict[str, str] = {}

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        pipeline = payload.get("pipeline", "default")
        action = payload.get("action", "check")

        if action == "check":
            status = self._pipeline_status.get(pipeline, "unknown")
        elif action == "update":
            status = payload.get("status", "green")
            self._pipeline_status[pipeline] = status
        else:
            status = "unknown"

        return {
            "status": "completed",
            "agent": self.agent_id,
            "task": task.task_id,
            "pipeline": pipeline,
            "ci_status": status,
        }
