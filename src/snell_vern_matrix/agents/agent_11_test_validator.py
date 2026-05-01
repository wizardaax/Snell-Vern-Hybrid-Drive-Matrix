"""Agent 11: Test_Validator — runs pytest, tracks coverage, detects regressions.

The `run` action subprocesses `python -m pytest <repo>` and parses the
result line to extract passed/failed counts. Then it calls the existing
`report` action so regression detection still works across runs.

Stdlib only — `subprocess` + `re`. No pytest plugin required.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from typing import Any, Optional

from . import AgentRole, BaseAgent, Task, TaskType

# Default to the Snell-Vern repo itself — the cycle tests itself by default.
_DEFAULT_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Match pytest summary lines like:  "364 passed, 1 warning in 1.81s"
#                                   "320 passed in 8.15s"
#                                   "1 failed, 361 passed, 1 warning in 1.66s"
_SUMMARY_RE = re.compile(
    r"=+\s*"
    r"(?:(?P<failed>\d+)\s+failed[,\s]*)?"
    r"(?:(?P<passed>\d+)\s+passed[,\s]*)?"
    r"(?:(?P<warnings>\d+)\s+warnings?[,\s]*)?"
    r"(?:in\s+[\d.]+s)?"
    r"\s*=+",
    re.IGNORECASE,
)


def _run_pytest(repo_path: str, target: str = "tests/", timeout: int = 120) -> dict[str, Any]:
    """Run pytest on a target repo. Returns parsed result + raw tail."""
    if not os.path.isdir(repo_path):
        return {"ok": False, "reason": f"repo path not found: {repo_path}"}
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", target, "-q", "--no-header"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return {"ok": False, "reason": "python or pytest not on PATH"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": f"timed out after {timeout}s"}

    output = (proc.stdout or "") + (proc.stderr or "")
    # Search the trailing summary line specifically — pytest prints it last.
    passed = 0
    failed = 0
    for m in _SUMMARY_RE.finditer(output):
        if m.group("passed"):
            passed = max(passed, int(m.group("passed")))
        if m.group("failed"):
            failed = max(failed, int(m.group("failed")))
    tail = "\n".join(output.strip().splitlines()[-12:])
    return {
        "ok": True,
        "passed": passed,
        "failed": failed,
        "exit_code": proc.returncode,
        "tail": tail,
        "repo_path": repo_path,
    }


class TestValidatorAgent(BaseAgent):
    """Tracks test coverage, detects regressions, and (now) actually runs pytest."""

    role = AgentRole.TEST_VALIDATOR
    capabilities = frozenset({TaskType.TESTING})

    def __init__(self, agent_id: str) -> None:
        super().__init__(agent_id)
        self._results: list[dict[str, Any]] = []

    def _report(self, passed: int, failed: int, task: Task, extras: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Record a result and detect regression vs prior runs."""
        total = passed + failed
        coverage = passed / total if total > 0 else 0.0
        entry = {"passed": passed, "failed": failed, "total": total, "coverage": coverage}
        self._results.append(entry)

        regression = False
        if len(self._results) >= 2:
            prev = self._results[-2]
            regression = entry["failed"] > prev["failed"]

        result = {
            "status": "completed",
            "agent": self.agent_id,
            "task": task.task_id,
            "passed": passed,
            "failed": failed,
            "coverage": coverage,
            "regression_detected": regression,
        }
        if extras:
            result.update(extras)
        return result

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        action = payload.get("action", "report")

        if action == "run":
            repo_path = payload.get("repo_path", _DEFAULT_REPO)
            target = payload.get("target", "tests/")
            timeout = int(payload.get("timeout", 120))
            run_result = _run_pytest(repo_path, target=target, timeout=timeout)
            if not run_result.get("ok"):
                return {
                    "status": "completed",
                    "agent": self.agent_id,
                    "task": task.task_id,
                    "action": "run",
                    "ran": False,
                    "reason": run_result.get("reason", "unknown failure"),
                }
            return {
                **self._report(
                    run_result["passed"],
                    run_result["failed"],
                    task,
                    extras={
                        "action": "run",
                        "ran": True,
                        "exit_code": run_result["exit_code"],
                        "repo_path": run_result["repo_path"],
                        "tail": run_result["tail"],
                    },
                ),
            }

        if action == "report":
            return self._report(
                int(payload.get("passed", 0)),
                int(payload.get("failed", 0)),
                task,
            )

        if action == "history":
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "history": self._results,
            }

        return {
            "status": "completed",
            "agent": self.agent_id,
            "task": task.task_id,
            "action": "noop",
        }
