"""Agent 13: Coherence_Monitor — global health and uncertainty tracking."""

from __future__ import annotations

from typing import Any

from . import COHERENCE_THRESHOLD, AgentRole, BaseAgent, Task, TaskType


class CoherenceMonitorAgent(BaseAgent):
    """Monitors global system coherence, health, and uncertainty."""

    role = AgentRole.COHERENCE_MONITOR
    capabilities = frozenset({TaskType.COHERENCE})

    def __init__(self, agent_id: str) -> None:
        super().__init__(agent_id)
        self._readings: list[float] = []

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        action = payload.get("action", "check")

        if action == "check":
            scores: list[float] = [float(s) for s in payload.get("agent_scores", [])]
            if scores:
                self._readings.append(sum(scores) / len(scores))
            avg = self._readings[-1] if self._readings else 0.5
            below_threshold = [s for s in scores if s < COHERENCE_THRESHOLD]
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "average_coherence": avg,
                "agents_below_threshold": len(below_threshold),
                "system_healthy": len(below_threshold) == 0,
            }
        elif action == "history":
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "readings": self._readings,
            }
        else:
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "noop",
            }
