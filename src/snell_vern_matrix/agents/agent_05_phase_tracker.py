"""Agent 5: Phase_Tracker — state transitions and drift prevention."""

from __future__ import annotations

from typing import Any

from . import AgentRole, BaseAgent, Task, TaskType


class PhaseTrackerAgent(BaseAgent):
    """Tracks phase-state transitions and prevents drift."""

    role = AgentRole.PHASE_TRACKER
    capabilities = frozenset({TaskType.PHASE})

    def __init__(self, agent_id: str) -> None:
        super().__init__(agent_id)
        self._history: list[str] = []

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        phase = payload.get("phase_state", "unknown")
        self._history.append(str(phase))

        drift = False
        if len(self._history) >= 3:
            recent = self._history[-3:]
            drift = len(set(recent)) == len(recent)

        return {
            "status": "completed",
            "agent": self.agent_id,
            "task": task.task_id,
            "current_phase": phase,
            "drift_detected": drift,
            "history_length": len(self._history),
        }
