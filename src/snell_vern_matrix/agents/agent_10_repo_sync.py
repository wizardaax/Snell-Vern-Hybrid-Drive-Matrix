"""Agent 10: Repo_Sync — cross-repository consistency checks (real git status).

The `status` action discovers all `.git` repos under a base path and runs
`git status --porcelain` + `git rev-list --left-right origin/main...HEAD` to
report dirty/clean, ahead/behind. The `check`/`sync` actions retain the
in-memory state machine for the existing test suite.

Stdlib only.
"""

from __future__ import annotations

import os
import subprocess
from typing import Any

from . import AgentRole, BaseAgent, Task, TaskType

_DEFAULT_BASE = r"D:\github\wizardaax"


def _discover_repos(base: str) -> list[str]:
    """Find all immediate-child directories under base that contain .git/."""
    if not os.path.isdir(base):
        return []
    out = []
    try:
        for name in sorted(os.listdir(base)):
            path = os.path.join(base, name)
            if os.path.isdir(path) and os.path.isdir(os.path.join(path, ".git")):
                out.append(path)
    except Exception:
        pass
    return out


def _git(args: list[str], cwd: str, timeout: int = 15) -> tuple[int, str, str]:
    """Run git with the given args, return (exit_code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except FileNotFoundError:
        return -1, "", "git not on PATH"
    except subprocess.TimeoutExpired:
        return -2, "", f"timed out after {timeout}s"


def _repo_status(path: str) -> dict[str, Any]:
    """Snapshot the state of a single repo: dirty file count, ahead/behind, branch."""
    rc, out, err = _git(["status", "--porcelain"], path)
    if rc != 0:
        return {"path": path, "name": os.path.basename(path), "error": err.strip() or "git status failed"}
    dirty_files = [ln for ln in out.splitlines() if ln.strip()]

    rc_branch, branch_out, _ = _git(["rev-parse", "--abbrev-ref", "HEAD"], path)
    branch = branch_out.strip() if rc_branch == 0 else "?"

    # Ahead/behind requires a tracked upstream; @{u} resolves to it. If no upstream,
    # just leave both at 0 — that's still a useful signal.
    ahead, behind = 0, 0
    rc_ab, ab_out, _ = _git(["rev-list", "--left-right", "--count", "@{u}...HEAD"], path)
    if rc_ab == 0 and ab_out.strip():
        try:
            parts = ab_out.strip().split()
            if len(parts) == 2:
                behind = int(parts[0])
                ahead = int(parts[1])
        except Exception:
            pass

    return {
        "path": path,
        "name": os.path.basename(path),
        "branch": branch,
        "dirty_count": len(dirty_files),
        "clean": len(dirty_files) == 0,
        "ahead": ahead,
        "behind": behind,
    }


class RepoSyncAgent(BaseAgent):
    """Checks and maintains cross-repository consistency."""

    role = AgentRole.REPO_SYNC
    capabilities = frozenset({TaskType.SYNC})

    def __init__(self, agent_id: str) -> None:
        super().__init__(agent_id)
        self._sync_state: dict[str, str] = {}

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        action = payload.get("action", "check")

        if action == "status":
            base = payload.get("base", _DEFAULT_BASE)
            repos = _discover_repos(base)
            statuses = [_repo_status(p) for p in repos]
            dirty = [s for s in statuses if not s.get("error") and not s.get("clean", True)]
            clean = [s for s in statuses if not s.get("error") and s.get("clean")]
            ahead = [s for s in statuses if s.get("ahead", 0) > 0]
            behind = [s for s in statuses if s.get("behind", 0) > 0]
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "status",
                "base": base,
                "total": len(statuses),
                "clean_count": len(clean),
                "dirty_count": len(dirty),
                "ahead_count": len(ahead),
                "behind_count": len(behind),
                "repos": statuses,
            }

        # Legacy actions preserved for the existing test suite.
        repo = payload.get("repo", "default")
        if action == "check":
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "repo": repo,
                "sync_status": self._sync_state.get(repo, "unsynced"),
            }
        if action == "sync":
            self._sync_state[repo] = "synced"
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "repo": repo,
                "sync_status": "synced",
            }
        return {
            "status": "completed",
            "agent": self.agent_id,
            "task": task.task_id,
            "action": "noop",
        }
