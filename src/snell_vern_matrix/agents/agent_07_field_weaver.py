"""Agent 7: Field_Weaver — phyllotaxis and golden-angle field analysis."""

from __future__ import annotations

from typing import Any

from ..recursive_field import angle, golden_angle, position, radius
from . import AgentRole, BaseAgent, Task, TaskType


class FieldWeaverAgent(BaseAgent):
    """Computes phyllotaxis field patterns using golden-angle geometry."""

    role = AgentRole.FIELD_WEAVER
    capabilities = frozenset({TaskType.FIELD})

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        action = payload.get("action", "field")
        n = int(payload.get("n", 10))

        if action == "field":
            points = [
                {"n": i, "x": position(i)[0], "y": position(i)[1]}
                for i in range(1, n + 1)
            ]
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "golden_angle": golden_angle(),
                "points": points,
            }
        elif action == "analysis":
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "golden_angle": golden_angle(),
                "radius": radius(max(n, 1)),
                "angle": angle(n),
            }
        else:
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "noop",
            }
