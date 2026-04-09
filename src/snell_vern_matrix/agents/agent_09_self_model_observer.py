"""Agent 9: Self_Model_Observer — observe, ask, and integrate cycle."""

from __future__ import annotations

from typing import Any

from ..self_model import SelfModel
from . import AgentRole, BaseAgent, Task, TaskType


class SelfModelObserverAgent(BaseAgent):
    """Drives the SelfModel observe/ask/integrate cycle."""

    role = AgentRole.SELF_MODEL_OBSERVER
    capabilities = frozenset({TaskType.OBSERVATION})

    def __init__(self, agent_id: str) -> None:
        super().__init__(agent_id)
        self._model = SelfModel()

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        action = payload.get("action", "observe")

        if action == "observe":
            pattern = payload.get("pattern", "default")
            result = self._model.observe(pattern)
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "observation": result,
            }
        elif action == "ask":
            query = self._model.ask()
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "query": query,
            }
        elif action == "integrate":
            data = payload.get("data", {})
            result = self._model.integrate(data)
            output = dict(result)
            output["phase_state"] = output["phase_state"].value
            output["ternary_balance"] = list(output["ternary_balance"])
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "state": output,
            }
        elif action == "state":
            state = self._model.state
            state["phase_state"] = state["phase_state"].value
            state["ternary_balance"] = list(state["ternary_balance"])
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "state": state,
            }
        else:
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "noop",
            }
