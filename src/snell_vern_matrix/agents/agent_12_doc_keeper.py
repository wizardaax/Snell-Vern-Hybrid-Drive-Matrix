"""Agent 12: Doc_Keeper — documentation health audit (real).

The `audit` action scans a repo for:
  • README presence + size + last-modified date
  • Python module docstring coverage (top-of-file docstrings)
  • Python function/class docstring coverage (via stdlib `ast`)

Reports a doc-health score and surfaces gaps.

Stdlib only — uses `os`, `ast`, `time`.
"""

from __future__ import annotations

import ast
import os
import time
from typing import Any

from . import AgentRole, BaseAgent, Task, TaskType

_DEFAULT_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _audit_python_docstrings(repo_path: str, src_subdir: str = "src") -> dict[str, int]:
    """Walk python files under repo/src/, count modules/functions/classes
    with vs without top-level docstrings."""
    base = os.path.join(repo_path, src_subdir)
    if not os.path.isdir(base):
        base = repo_path  # fall back to whole repo
    counts = {
        "py_files": 0,
        "modules_with_doc": 0,
        "modules_without_doc": 0,
        "funcs_with_doc": 0,
        "funcs_without_doc": 0,
        "classes_with_doc": 0,
        "classes_without_doc": 0,
    }
    for root, dirs, files in os.walk(base):
        # Skip noise
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", ".venv", "node_modules", "dist", "build")]
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            counts["py_files"] += 1
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    src = fh.read()
                tree = ast.parse(src)
            except Exception:
                continue
            # Module docstring?
            if ast.get_docstring(tree):
                counts["modules_with_doc"] += 1
            else:
                counts["modules_without_doc"] += 1
            # Walk for funcs/classes
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if ast.get_docstring(node):
                        counts["funcs_with_doc"] += 1
                    else:
                        counts["funcs_without_doc"] += 1
                elif isinstance(node, ast.ClassDef):
                    if ast.get_docstring(node):
                        counts["classes_with_doc"] += 1
                    else:
                        counts["classes_without_doc"] += 1
    return counts


def _readme_status(repo_path: str) -> dict[str, Any]:
    """Check README presence + freshness."""
    candidates = ["README.md", "README.rst", "README.txt", "readme.md"]
    for name in candidates:
        path = os.path.join(repo_path, name)
        if os.path.isfile(path):
            mt = os.path.getmtime(path)
            age_days = (time.time() - mt) / 86400.0
            return {
                "exists": True,
                "filename": name,
                "size_bytes": os.path.getsize(path),
                "age_days": round(age_days, 1),
            }
    return {"exists": False}


def _coverage_pct(with_doc: int, without_doc: int) -> float:
    total = with_doc + without_doc
    return round(with_doc / total, 4) if total > 0 else 0.0


class DocKeeperAgent(BaseAgent):
    """Manages automatic documentation and manifest updates."""

    role = AgentRole.DOC_KEEPER
    capabilities = frozenset({TaskType.DOCUMENTATION})

    def __init__(self, agent_id: str) -> None:
        super().__init__(agent_id)
        self._manifest: dict[str, str] = {}

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        action = payload.get("action", "update")

        if action == "audit":
            repo_path = payload.get("repo_path", _DEFAULT_REPO)
            src_subdir = payload.get("src_subdir", "src")
            counts = _audit_python_docstrings(repo_path, src_subdir)
            readme = _readme_status(repo_path)
            module_cov = _coverage_pct(counts["modules_with_doc"], counts["modules_without_doc"])
            func_cov = _coverage_pct(counts["funcs_with_doc"], counts["funcs_without_doc"])
            class_cov = _coverage_pct(counts["classes_with_doc"], counts["classes_without_doc"])
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "audit",
                "repo_path": repo_path,
                "readme": readme,
                "py_files": counts["py_files"],
                "module_doc_coverage": module_cov,
                "function_doc_coverage": func_cov,
                "class_doc_coverage": class_cov,
                "raw": counts,
            }

        if action == "update":
            key = payload.get("key", "")
            value = payload.get("value", "")
            self._manifest[key] = value
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "updated",
                "key": key,
            }

        if action == "manifest":
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "manifest": dict(self._manifest),
            }

        return {
            "status": "completed",
            "agent": self.agent_id,
            "task": task.task_id,
            "action": "noop",
        }
