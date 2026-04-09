"""Agent 3: Memory_Keeper — associative memory management."""

from __future__ import annotations

from typing import Any

from . import AgentRole, BaseAgent, Task, TaskType


class MemoryKeeperAgent(BaseAgent):
    """Manages associative memory storage and retrieval."""

    role = AgentRole.MEMORY_KEEPER
    capabilities = frozenset({TaskType.MEMORY})

    def __init__(self, agent_id: str) -> None:
        super().__init__(agent_id)
        self._store: dict[str, Any] = {}

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        action = payload.get("action", "get")
        key = payload.get("key", "")

        if action == "store":
            value = payload.get("value")
            self._store[key] = value
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "stored",
                "key": key,
            }
        elif action == "get":
            value = self._store.get(key)
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "retrieved",
                "key": key,
                "value": value,
            }
        elif action == "list":
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "listed",
                "keys": sorted(self._store.keys()),
            }
        else:
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "noop",
            }
