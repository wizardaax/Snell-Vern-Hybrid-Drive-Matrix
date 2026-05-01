"""Agent 2: CI_Sentinel — real CI health audit via workflow file discovery.

The `audit` action walks repos under a base path looking for
`.github/workflows/*.yml` files. Reports which repos have CI, how many
workflows each has, and lists workflow names. No network calls — works
fully offline. For live workflow run status, use GitHub's API outside
the cycle (intentional 100-year-design limitation).

The legacy `check`/`update` actions retain in-memory state for the
existing test suite.

Stdlib only.
"""

from __future__ import annotations

import os
from typing import Any

from . import AgentRole, BaseAgent, Task, TaskType

_DEFAULT_BASE = r"D:\github\wizardaax"


def _discover_workflows(repo_path: str) -> list[str]:
    """Return list of workflow filenames in <repo>/.github/workflows/."""
    wf_dir = os.path.join(repo_path, ".github", "workflows")
    if not os.path.isdir(wf_dir):
        return []
    out = []
    try:
        for name in sorted(os.listdir(wf_dir)):
            if name.endswith((".yml", ".yaml")):
                out.append(name)
    except Exception:
        pass
    return out


def _audit_base(base: str) -> list[dict[str, Any]]:
    """Walk immediate children of base; for each, report CI presence."""
    if not os.path.isdir(base):
        return []
    rows = []
    try:
        for name in sorted(os.listdir(base)):
            path = os.path.join(base, name)
            if not os.path.isdir(path):
                continue
            if not os.path.isdir(os.path.join(path, ".git")):
                continue
            workflows = _discover_workflows(path)
            rows.append({
                "name": name,
                "path": path,
                "has_ci": len(workflows) > 0,
                "workflow_count": len(workflows),
                "workflows": workflows,
            })
    except Exception:
        pass
    return rows


class CISentinelAgent(BaseAgent):
    """Monitors CI pipelines and reports health status."""

    role = AgentRole.CI_SENTINEL
    capabilities = frozenset({TaskType.CI_HEALTH})

    def __init__(self, agent_id: str) -> None:
        super().__init__(agent_id)
        self._pipeline_status: dict[str, str] = {}

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        action = payload.get("action", "check")

        if action == "audit":
            base = payload.get("base", _DEFAULT_BASE)
            rows = _audit_base(base)
            with_ci = [r for r in rows if r["has_ci"]]
            without_ci = [r for r in rows if not r["has_ci"]]
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "audit",
                "base": base,
                "total_repos": len(rows),
                "with_ci": len(with_ci),
                "without_ci": len(without_ci),
                "total_workflows": sum(r["workflow_count"] for r in rows),
                "rows": rows,
            }

        # Legacy actions preserved for the existing test suite.
        pipeline = payload.get("pipeline", "default")
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
