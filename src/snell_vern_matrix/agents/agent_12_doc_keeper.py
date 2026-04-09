"""Agent 12: Doc_Keeper — auto-documentation and manifest updates."""

from __future__ import annotations

from typing import Any

from . import AgentRole, BaseAgent, Task, TaskType


class DocKeeperAgent(BaseAgent):
    """Manages automatic documentation and manifest updates."""

    role = AgentRole.DOC_KEEPER
    capabilities = frozenset({TaskType.DOCUMENTATION})

    def __init__(self, agent_id: str) -> None:
        super().__init__(agent_id)
        self._manifest: dict[str, str] = {}

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        action = payload.get("action", "update")

        if action == "update":
            key = payload.get("key", "")
            value = payload.get("value", "")
            self._manifest[key] = value
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "updated",
                "key": key,
            }
        elif action == "manifest":
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "manifest": dict(self._manifest),
            }
        else:
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "noop",
            }
