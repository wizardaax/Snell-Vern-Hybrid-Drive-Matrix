"""Agent 7: Field_Weaver — phyllotaxis, golden-angle, and AEON Engine."""

from __future__ import annotations

import os
import sys
from typing import Any

from ..recursive_field import angle, golden_angle, position, radius
from . import AgentRole, BaseAgent, Task, TaskType


def _aeon_summary() -> dict[str, Any] | None:
    """Lazy import of the AEON Engine from the sibling ziltrix-sch-core repo.

    Returns None if the module isn't reachable — fail soft, not hard.
    The repo lives at D:\\github\\wizardaax\\ziltrix-sch-core in the
    canonical layout; we add it to sys.path on first call.
    """
    candidates = [
        r"D:\github\wizardaax\ziltrix-sch-core",
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "ziltrix-sch-core"),
    ]
    for path in candidates:
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "aeon_engine.py")):
            if path not in sys.path:
                sys.path.insert(0, path)
            try:
                import aeon_engine  # type: ignore[import-not-found]
                return aeon_engine.aeon_summary()
            except Exception:
                return None
    return None


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
        elif action == "aeon":
            # Pulls in the runnable AEON Engine v2.1 from ziltrix-sch-core.
            # Returns canonical thrust series + validation against the
            # documented June 4 2025 PhaseII data.
            summary = _aeon_summary()
            if summary is None:
                return {
                    "status": "completed",
                    "agent": self.agent_id,
                    "task": task.task_id,
                    "action": "aeon",
                    "ran": False,
                    "reason": "aeon_engine module not reachable",
                }
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "aeon",
                "ran": True,
                "constants": summary["constants"],
                "thrust_series": summary["thrust_series"],
                "validation": summary["validation"],
            }
        else:
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "noop",
            }
