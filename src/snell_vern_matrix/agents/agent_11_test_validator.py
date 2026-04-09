"""Agent 11: Test_Validator — coverage tracking and regression detection."""

from __future__ import annotations

from typing import Any

from . import AgentRole, BaseAgent, Task, TaskType


class TestValidatorAgent(BaseAgent):
    """Tracks test coverage and detects regressions."""

    role = AgentRole.TEST_VALIDATOR
    capabilities = frozenset({TaskType.TESTING})

    def __init__(self, agent_id: str) -> None:
        super().__init__(agent_id)
        self._results: list[dict[str, Any]] = []

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        action = payload.get("action", "report")

        if action == "report":
            passed = int(payload.get("passed", 0))
            failed = int(payload.get("failed", 0))
            total = passed + failed
            coverage = passed / total if total > 0 else 0.0
            entry = {
                "passed": passed,
                "failed": failed,
                "total": total,
                "coverage": coverage,
            }
            self._results.append(entry)

            regression = False
            if len(self._results) >= 2:
                prev = self._results[-2]
                regression = entry["failed"] > prev["failed"]

            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "passed": passed,
                "failed": failed,
                "coverage": coverage,
                "regression_detected": regression,
            }
        elif action == "history":
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "history": self._results,
            }
        else:
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "noop",
            }
