"""
Repo adapters for the federation mesh.

Provides a standardised interface for Snell-Vern-Hybrid-Drive-Matrix and
recursive-field-math-pro (aeon-standards) repos.  Supports JSON protocol
for --dispatch, --status, --recall, with fallback routing and coherence
gating when an agent/repo is unavailable.

Zero new runtime dependencies.
"""

from __future__ import annotations

import json
import os as _os
from typing import Any, Optional, Protocol

from ..agents import COHERENCE_THRESHOLD, TaskType
from ..agents import AgentHealth as _AgentHealth


class RepoAdapter(Protocol):
    """Protocol that every repo adapter must satisfy."""

    @property
    def repo_name(self) -> str: ...

    @property
    def supported_task_types(self) -> frozenset[str]: ...

    @property
    def agent_count(self) -> int: ...

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]: ...

    def status(self) -> dict[str, Any]: ...

    def recall(self, task_id: str) -> Optional[dict[str, Any]]: ...

    def is_available(self) -> bool: ...

    def coherence_score(self) -> float: ...

    def current_load(self) -> float: ...


class SnellVernAdapter:
    """
    Adapter for the local Snell-Vern-Hybrid-Drive-Matrix 13-agent system.

    Routes tasks through the existing AgentOrchestrator, inheriting
    all SCE-88 coherence gating and load-balancing logic.
    """

    def __init__(self) -> None:
        from ..agents.orchestrator import AgentOrchestrator

        self._orchestrator = AgentOrchestrator()
        self._task_log: dict[str, dict[str, Any]] = {}

    @property
    def repo_name(self) -> str:
        return "snell-vern-hybrid-drive-matrix"

    @property
    def supported_task_types(self) -> frozenset[str]:
        return frozenset(t.value for t in TaskType)

    @property
    def agent_count(self) -> int:
        return self._orchestrator.agent_count

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Dispatch a task through the local orchestrator."""
        try:
            task = self._orchestrator.dispatch(task_type, payload)
            results = self._orchestrator.process_all()
            output = {
                "status": "completed",
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "assigned_agent": task.assigned_agent,
                "results": results,
            }
            self._task_log[task.task_id] = output
            return output
        except (ValueError, RuntimeError) as exc:
            return {"status": "error", "error": str(exc)}

    def status(self) -> dict[str, Any]:
        """Return status of the local 13-agent orchestrator."""
        return self._orchestrator.get_status()

    def recall(self, task_id: str) -> Optional[dict[str, Any]]:
        """Recall a previously dispatched task result."""
        return self._task_log.get(task_id)

    def is_available(self) -> bool:
        """Check if the orchestrator is healthy."""
        agents = self._orchestrator.agents
        healthy_count = sum(
            1
            for a in agents.values()
            if a.state.health in (_AgentHealth.HEALTHY, _AgentHealth.DEGRADED)
        )
        return healthy_count > 0

    def coherence_score(self) -> float:
        """Aggregate coherence across all local agents."""
        agents = self._orchestrator.agents
        if not agents:
            return 0.5
        scores = [a.state.coherence_score for a in agents.values()]
        return sum(scores) / len(scores)

    def current_load(self) -> float:
        """Compute normalised load across all local agents."""
        agents = self._orchestrator.agents
        if not agents:
            return 0.0
        total_queued = sum(a.state.queue_length for a in agents.values())
        max_capacity = len(agents) * 10  # MAX_QUEUE_LENGTH per agent
        return min(1.0, total_queued / max_capacity) if max_capacity > 0 else 0.0

    def to_json_protocol(self, action: str, **kwargs: Any) -> str:
        """Encode a request in the federation JSON protocol."""
        msg: dict[str, Any] = {"action": action, "repo": self.repo_name}
        msg.update(kwargs)
        return json.dumps(msg, sort_keys=True)

    @staticmethod
    def parse_json_protocol(raw: str) -> dict[str, Any]:
        """Decode a federation JSON protocol message."""
        return dict(json.loads(raw))


class RFMProAdapter:
    """
    Adapter for the recursive-field-math-pro (aeon-standards) repo.

    Multiplexes across rfm-pro's submodules under a single mesh registration.
    The repo registers ONCE in the federation mesh — task_types span the full
    rfm-pro surface: math, field, coherence (handled inline) plus evolve,
    swarm, select, score, bridge, detect, self_model, validate (delegated to
    sub-adapter classes for each submodule).

    Module-level routing inside one repo, not 9 separate repo entries:
        math, field, coherence  → handled inline by _execute_rfm
        evolve                  → EvolutionEngineAdapter
        swarm                   → SwarmAdapter
        select                  → PhiUCBAdapter
        score                   → EvalAPIAdapter
        bridge                  → BridgeAdapter
        detect                  → DetectorAdapter
        self_model              → SelfModelAdapter
        validate                → ContainmentValidatorAdapter

    Coherence gating, fail-closed availability, and recall() all work
    transparently across the multiplexed submodules.
    """

    _CORE_TYPES = frozenset({"math", "field", "coherence"})

    def __init__(self) -> None:
        self._task_log: dict[str, dict[str, Any]] = {}
        self._available = self._probe_availability()
        self._coherence: float = 0.5

        # Sub-adapter handlers for non-core task types. Lazily owned —
        # each sub-adapter probes its own submodule on construction.
        self._submodules: dict[str, Any] = {
            "evolve": EvolutionEngineAdapter(),
            "swarm": SwarmAdapter(),
            "select": PhiUCBAdapter(),
            "score": EvalAPIAdapter(),
            "bridge": BridgeAdapter(),
            "detect": DetectorAdapter(),
            "self_model": SelfModelAdapter(),
            "validate": ContainmentValidatorAdapter(),
        }

    @property
    def repo_name(self) -> str:
        return "recursive-field-math-pro"

    @property
    def supported_task_types(self) -> frozenset[str]:
        # Union: 3 core types + 8 submodule task types
        return self._CORE_TYPES | frozenset(self._submodules.keys())

    @property
    def agent_count(self) -> int:
        # 13 federation agents inside EvolutionEngine; surface that count here.
        return self._submodules["evolve"].agent_count

    def _probe_availability(self) -> bool:
        """Check if recursive_field_math is importable."""
        try:
            import recursive_field_math  # noqa: F401

            return True
        except ImportError:
            return False

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Dispatch a task to RFM-Pro.

        Routes core task types (math/field/coherence) inline; delegates
        submodule task types (evolve/swarm/select/score/bridge/detect/
        self_model/validate) to the corresponding sub-adapter.

        Performs coherence gating at the repo level. Sub-adapters apply
        their own gates as well — both must pass for a dispatch to land.
        """
        if not self._available:
            return {"status": "unavailable", "error": "recursive_field_math not found"}

        if self._coherence < COHERENCE_THRESHOLD and not payload.get("force", False):
            return {
                "status": "coherence_gated",
                "coherence": self._coherence,
                "threshold": COHERENCE_THRESHOLD,
            }

        # Submodule routing
        if task_type in self._submodules:
            sub = self._submodules[task_type]
            result = sub.dispatch(task_type, payload)
            # Surface the submodule that actually handled the call so callers
            # can introspect routing in the unified rfm-pro response shape.
            if isinstance(result, dict) and "module" not in result:
                result = {**result, "module": task_type}
            return result

        # Core task types handled inline
        if task_type not in self._CORE_TYPES:
            return {"status": "error", "error": f"unsupported task_type: {task_type}"}

        try:
            result = self._execute_rfm(task_type, payload)
            task_id = _generate_task_id(task_type, payload)
            output = {
                "status": "completed",
                "task_id": task_id,
                "task_type": task_type,
                "result": result,
            }
            self._task_log[task_id] = output
            return output
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def _execute_rfm(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute an RFM-Pro core operation (math/field/coherence)."""
        import recursive_field_math as rfm

        if task_type == "math":
            n = int(payload.get("n", 10))
            return {
                "lucas": rfm.L(n),
                "fibonacci": rfm.F(n),
                "ratio": rfm.ratio(max(n, 1)),
                "phi": rfm.PHI,
            }
        elif task_type == "field":
            n = int(payload.get("n", 5))
            return {
                "r_theta": rfm.r_theta(n),
                "egypt_4_7_11": list(rfm.egypt_4_7_11()),
            }
        elif task_type == "coherence":
            sig = rfm.signature_summary()
            return {
                "signature": {
                    "L3": sig["L3"],
                    "L4": sig["L4"],
                    "L5": sig["L5"],
                },
                "phi": rfm.PHI,
            }
        else:
            return {"echo": task_type, "payload": payload}

    def status(self) -> dict[str, Any]:
        """Return status of the RFM-Pro adapter and its submodules."""
        return {
            "repo": self.repo_name,
            "available": self._available,
            "coherence": self._coherence,
            "task_log_length": len(self._task_log),
            "supported_types": sorted(self.supported_task_types),
            "submodules": {
                tt: sub.is_available() for tt, sub in self._submodules.items()
            },
        }

    def recall(self, task_id: str) -> Optional[dict[str, Any]]:
        """Recall a task result — checks core log first, then each submodule."""
        if task_id in self._task_log:
            return self._task_log[task_id]
        for sub in self._submodules.values():
            hit = sub.recall(task_id)
            if hit is not None:
                return hit
        return None

    def is_available(self) -> bool:
        return self._available

    def coherence_score(self) -> float:
        return self._coherence

    def set_coherence(self, score: float) -> None:
        """Update repo coherence — propagates to all submodules so gating stays consistent."""
        clamped = max(0.0, min(1.0, score))
        self._coherence = clamped
        for sub in self._submodules.values():
            sub.set_coherence(clamped)

    def current_load(self) -> float:
        """RFM-Pro core has no queue; load reflects the busiest submodule."""
        loads = [sub.current_load() for sub in self._submodules.values()]
        return max(loads) if loads else 0.0

    def to_json_protocol(self, action: str, **kwargs: Any) -> str:
        """Encode a request in the federation JSON protocol."""
        msg: dict[str, Any] = {"action": action, "repo": self.repo_name}
        msg.update(kwargs)
        return json.dumps(msg, sort_keys=True)

    @staticmethod
    def parse_json_protocol(raw: str) -> dict[str, Any]:
        """Decode a federation JSON protocol message."""
        return dict(json.loads(raw))


class GlyphPhaseAdapter:
    """
    Adapter for the glyph_phase_engine PyPI package.

    Routes "phase" tasks to GlyphPhaseEngine.process_symbolic_input.
    Stateless wrapper: each dispatch creates a fresh engine instance and
    returns the resulting PhaseState plus a snapshot of the engine's info.
    """

    _SUPPORTED_TYPES = frozenset({"phase"})

    def __init__(self) -> None:
        self._task_log: dict[str, dict[str, Any]] = {}
        self._available = self._probe_availability()
        self._coherence: float = 0.5

    @property
    def repo_name(self) -> str:
        return "glyph_phase_engine"

    @property
    def supported_task_types(self) -> frozenset[str]:
        return self._SUPPORTED_TYPES

    @property
    def agent_count(self) -> int:
        return 0

    def _probe_availability(self) -> bool:
        """Check if glyph_phase_engine is importable."""
        try:
            import glyph_phase_engine  # noqa: F401

            return True
        except ImportError:
            return False

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Dispatch a phase-tracking task.

        Performs coherence gating: rejects tasks when coherence is below
        COHERENCE_THRESHOLD, unless a force flag is set.
        """
        if not self._available:
            return {"status": "unavailable", "error": "glyph_phase_engine not found"}

        if self._coherence < COHERENCE_THRESHOLD and not payload.get("force", False):
            return {
                "status": "coherence_gated",
                "coherence": self._coherence,
                "threshold": COHERENCE_THRESHOLD,
            }

        if task_type != "phase":
            return {"status": "error", "error": f"unsupported task_type: {task_type}"}

        symbolic_input = payload.get("input", "")
        if not isinstance(symbolic_input, str):
            return {"status": "error", "error": "payload['input'] must be a string"}

        try:
            from glyph_phase_engine import GlyphPhaseEngine

            engine = GlyphPhaseEngine()
            phase = engine.process_symbolic_input(symbolic_input)
            info = engine.get_phase_info()
            task_id = _generate_task_id(task_type, payload)
            phase_value = phase.value if hasattr(phase, "value") else str(phase)
            output = {
                "status": "completed",
                "task_id": task_id,
                "task_type": task_type,
                "result": {
                    "phase": phase_value,
                    "info": info,
                },
            }
            self._task_log[task_id] = output
            return output
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def status(self) -> dict[str, Any]:
        """Return adapter status."""
        return {
            "repo": self.repo_name,
            "available": self._available,
            "coherence": self._coherence,
            "task_log_length": len(self._task_log),
            "supported_types": sorted(self._SUPPORTED_TYPES),
        }

    def recall(self, task_id: str) -> Optional[dict[str, Any]]:
        """Recall a previously dispatched task result."""
        return self._task_log.get(task_id)

    def is_available(self) -> bool:
        return self._available

    def coherence_score(self) -> float:
        return self._coherence

    def set_coherence(self, score: float) -> None:
        """Update the adapter's coherence score (called by mesh monitor)."""
        self._coherence = max(0.0, min(1.0, score))

    def current_load(self) -> float:
        """Stateless engine; load is always 0."""
        return 0.0

    def to_json_protocol(self, action: str, **kwargs: Any) -> str:
        """Encode a request in the federation JSON protocol."""
        msg: dict[str, Any] = {"action": action, "repo": self.repo_name}
        msg.update(kwargs)
        return json.dumps(msg, sort_keys=True)

    @staticmethod
    def parse_json_protocol(raw: str) -> dict[str, Any]:
        """Decode a federation JSON protocol message."""
        return dict(json.loads(raw))


WIZARDAAX_ROOT = _os.environ.get("WIZARDAAX_ROOT", r"D:\github\wizardaax")
SCE88_REPO_PATH = _os.environ.get("SCE88_REPO_PATH", _os.path.join(WIZARDAAX_ROOT, "SCE-88"))


class SCE88Adapter:
    """
    Adapter for the SCE-88 architectural validator.

    Routes "constraint" and "coherence" tasks to validation/validator.py in
    the SCE-88 repo. Validates 4 domains x 22 levels (isolation, ordering,
    closure at level 19). Pure stdlib — no extra dependencies required.

    The adapter sys.path-injects the SCE-88 repo root at import time so
    `from validation.validator import instantiate_unit` resolves.
    """

    _SUPPORTED_TYPES = frozenset({"constraint", "coherence"})

    def __init__(self) -> None:
        self._task_log: dict[str, dict[str, Any]] = {}
        self._available = self._probe_availability()
        self._coherence: float = 0.5

    @property
    def repo_name(self) -> str:
        return "SCE-88"

    @property
    def supported_task_types(self) -> frozenset[str]:
        return self._SUPPORTED_TYPES

    @property
    def agent_count(self) -> int:
        return 0

    def _probe_availability(self) -> bool:
        """Check if SCE-88 validator is importable; sys.path-inject if needed."""
        import os
        import sys

        if not os.path.isdir(SCE88_REPO_PATH):
            return False
        if SCE88_REPO_PATH not in sys.path:
            sys.path.insert(0, SCE88_REPO_PATH)
        try:
            from validation.validator import instantiate_unit  # noqa: F401

            return True
        except ImportError:
            return False

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Dispatch a constraint/coherence task: run SCE-88 architectural validation.

        Performs coherence gating: rejects tasks when adapter coherence is below
        COHERENCE_THRESHOLD, unless a force flag is set.
        """
        if not self._available:
            return {
                "status": "unavailable",
                "error": f"SCE-88 validator not found at {SCE88_REPO_PATH}",
            }

        if self._coherence < COHERENCE_THRESHOLD and not payload.get("force", False):
            return {
                "status": "coherence_gated",
                "coherence": self._coherence,
                "threshold": COHERENCE_THRESHOLD,
            }

        if task_type not in self._SUPPORTED_TYPES:
            return {"status": "error", "error": f"unsupported task_type: {task_type}"}

        try:
            from validation.validator import instantiate_unit

            unit = instantiate_unit()
            unit.validate()
            task_id = _generate_task_id(task_type, payload)
            output = {
                "status": "completed",
                "task_id": task_id,
                "task_type": task_type,
                "result": {
                    "validation": "pass",
                    "domains": 4,
                    "levels_per_domain": 22,
                    "closure_level": 19,
                },
            }
            self._task_log[task_id] = output
            return output
        except ValueError as exc:
            task_id = _generate_task_id(task_type, payload)
            output = {
                "status": "violation",
                "task_id": task_id,
                "task_type": task_type,
                "result": {"validation": "fail", "violation": str(exc)},
            }
            self._task_log[task_id] = output
            return output
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def status(self) -> dict[str, Any]:
        """Return adapter status."""
        return {
            "repo": self.repo_name,
            "available": self._available,
            "coherence": self._coherence,
            "task_log_length": len(self._task_log),
            "supported_types": sorted(self._SUPPORTED_TYPES),
            "repo_path": SCE88_REPO_PATH,
        }

    def recall(self, task_id: str) -> Optional[dict[str, Any]]:
        """Recall a previously dispatched task result."""
        return self._task_log.get(task_id)

    def is_available(self) -> bool:
        return self._available

    def coherence_score(self) -> float:
        return self._coherence

    def set_coherence(self, score: float) -> None:
        """Update the adapter's coherence score (called by mesh monitor)."""
        self._coherence = max(0.0, min(1.0, score))

    def current_load(self) -> float:
        """Stateless validator; load is always 0."""
        return 0.0

    def to_json_protocol(self, action: str, **kwargs: Any) -> str:
        """Encode a request in the federation JSON protocol."""
        msg: dict[str, Any] = {"action": action, "repo": self.repo_name}
        msg.update(kwargs)
        return json.dumps(msg, sort_keys=True)

    @staticmethod
    def parse_json_protocol(raw: str) -> dict[str, Any]:
        """Decode a federation JSON protocol message."""
        return dict(json.loads(raw))


CODEX_AEON_REPO_PATH = _os.environ.get("CODEX_AEON_REPO_PATH", _os.path.join(WIZARDAAX_ROOT, "Codex-AEON-Resonator"))


class RepoDocumentAdapter:
    """
    Generic adapter for content-only repos (docs, logs, sim outputs, static
    sites, archives). Routes file listing and reading over a repo's filesystem
    path. No callable agents — just safe, size-capped content access.

    Configurable per instance with (repo_name, repo_path, task_types).
    """

    _MAX_READ_BYTES = 100_000
    _LIST_DEPTH_DEFAULT = 2
    _TEXT_EXTS = frozenset(
        {
            ".txt",
            ".md",
            ".html",
            ".css",
            ".json",
            ".yaml",
            ".yml",
            ".csv",
            ".log",
            ".cfg",
            ".ini",
            ".toml",
            ".rst",
            ".py",
            ".rs",
            ".js",
            ".ts",
            ".sh",
            ".tex",
        }
    )
    _SKIP_DIRS = frozenset({".git", "node_modules", "target", "__pycache__", ".venv"})

    def __init__(
        self,
        repo_name: str,
        repo_path: str,
        task_types: frozenset[str] = frozenset({"documentation"}),
    ) -> None:
        self._repo_name = repo_name
        self._repo_path = repo_path
        self._task_types = task_types
        self._task_log: dict[str, dict[str, Any]] = {}
        self._available = self._probe_availability()
        self._coherence: float = 0.5

    @property
    def repo_name(self) -> str:
        return self._repo_name

    @property
    def supported_task_types(self) -> frozenset[str]:
        return self._task_types

    @property
    def agent_count(self) -> int:
        return 0

    def _probe_availability(self) -> bool:
        import os

        return os.path.isdir(self._repo_path)

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._available:
            return {"status": "unavailable", "error": f"repo not found at {self._repo_path}"}

        if self._coherence < COHERENCE_THRESHOLD and not payload.get("force", False):
            return {
                "status": "coherence_gated",
                "coherence": self._coherence,
                "threshold": COHERENCE_THRESHOLD,
            }

        if task_type not in self._task_types:
            return {"status": "error", "error": f"unsupported task_type: {task_type}"}

        action = payload.get("action", "list")
        try:
            if action == "list":
                depth = int(payload.get("depth", self._LIST_DEPTH_DEFAULT))
                result = self._list_files(depth)
            elif action == "read":
                rel_path = payload.get("path", "")
                if not isinstance(rel_path, str) or not rel_path:
                    return {"status": "error", "error": "payload['path'] required for read action"}
                result = self._read_file(rel_path)
            else:
                return {"status": "error", "error": f"unknown action: {action}"}

            task_id = _generate_task_id(task_type, payload)
            output = {
                "status": "completed",
                "task_id": task_id,
                "task_type": task_type,
                "result": result,
            }
            self._task_log[task_id] = output
            return output
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def _list_files(self, depth: int) -> dict[str, Any]:
        import os

        files: list[dict[str, Any]] = []
        for root, dirs, names in os.walk(self._repo_path):
            dirs[:] = [d for d in dirs if d not in self._SKIP_DIRS and not d.startswith(".")]
            rel_root = os.path.relpath(root, self._repo_path)
            current_depth = 0 if rel_root == "." else rel_root.count(os.sep) + 1
            if current_depth > depth:
                dirs[:] = []
                continue
            for name in names:
                full = os.path.join(root, name)
                try:
                    size = os.path.getsize(full)
                except OSError:
                    size = -1
                rel = os.path.relpath(full, self._repo_path).replace(os.sep, "/")
                files.append({"path": rel, "size": size})
        return {"repo": self._repo_name, "file_count": len(files), "files": files}

    def _read_file(self, rel_path: str) -> dict[str, Any]:
        import os

        rel_norm = os.path.normpath(rel_path)
        if rel_norm.startswith("..") or os.path.isabs(rel_norm):
            return {"error": "path must be relative and within the repo"}
        full = os.path.join(self._repo_path, rel_norm)
        if not os.path.isfile(full):
            return {"error": f"not a file: {rel_path}"}
        ext = os.path.splitext(full)[1].lower()
        size = os.path.getsize(full)
        if ext not in self._TEXT_EXTS:
            return {
                "path": rel_path,
                "size": size,
                "binary": True,
                "content": None,
                "note": "binary or non-text extension; not read",
            }
        if size > self._MAX_READ_BYTES:
            with open(full, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(self._MAX_READ_BYTES)
            return {"path": rel_path, "size": size, "truncated": True, "content": content}
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"path": rel_path, "size": size, "truncated": False, "content": content}

    def status(self) -> dict[str, Any]:
        return {
            "repo": self._repo_name,
            "available": self._available,
            "coherence": self._coherence,
            "task_log_length": len(self._task_log),
            "supported_types": sorted(self._task_types),
            "repo_path": self._repo_path,
        }

    def recall(self, task_id: str) -> Optional[dict[str, Any]]:
        return self._task_log.get(task_id)

    def is_available(self) -> bool:
        return self._available

    def coherence_score(self) -> float:
        return self._coherence

    def set_coherence(self, score: float) -> None:
        self._coherence = max(0.0, min(1.0, score))

    def current_load(self) -> float:
        return 0.0

    def to_json_protocol(self, action: str, **kwargs: Any) -> str:
        msg: dict[str, Any] = {"action": action, "repo": self._repo_name}
        msg.update(kwargs)
        return json.dumps(msg, sort_keys=True)

    @staticmethod
    def parse_json_protocol(raw: str) -> dict[str, Any]:
        return dict(json.loads(raw))


class CodexAeonAdapter:
    """
    Adapter for Codex-AEON-Resonator research pipelines.

    Routes "documentation"/"observation" tasks to a chosen pipeline script:
      - voynich: pipeline/voynich_morphological_comparison.py
      - extraction_topology: pipeline/extraction_topology.py

    Subprocess invocation; requires numpy + scipy in the dispatching Python.
    Output stdout is captured and returned (truncated to 4 KB).
    """

    _SUPPORTED_TYPES = frozenset({"observation"})
    _PIPELINES = {
        "voynich": "pipeline/voynich_morphological_comparison.py",
        "extraction_topology": "pipeline/extraction_topology.py",
    }
    _TIMEOUT_SEC = 120

    def __init__(self) -> None:
        self._task_log: dict[str, dict[str, Any]] = {}
        self._available = self._probe_availability()
        self._coherence: float = 0.5

    @property
    def repo_name(self) -> str:
        return "Codex-AEON-Resonator"

    @property
    def supported_task_types(self) -> frozenset[str]:
        return self._SUPPORTED_TYPES

    @property
    def agent_count(self) -> int:
        return 0

    def _probe_availability(self) -> bool:
        import os
        import subprocess
        import sys

        if not os.path.isdir(CODEX_AEON_REPO_PATH):
            return False
        for rel in self._PIPELINES.values():
            if not os.path.isfile(os.path.join(CODEX_AEON_REPO_PATH, rel)):
                return False
        # Verify numpy + scipy are actually importable; pipeline scripts require both.
        try:
            result = subprocess.run(
                [sys.executable, "-c", "import numpy, scipy"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode != 0:
                return False
        except Exception:
            return False
        return True

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        import os
        import subprocess
        import sys

        if not self._available:
            return {
                "status": "unavailable",
                "error": f"Codex-AEON-Resonator not found at {CODEX_AEON_REPO_PATH}",
            }

        if self._coherence < COHERENCE_THRESHOLD and not payload.get("force", False):
            return {
                "status": "coherence_gated",
                "coherence": self._coherence,
                "threshold": COHERENCE_THRESHOLD,
            }

        if task_type not in self._SUPPORTED_TYPES:
            return {"status": "error", "error": f"unsupported task_type: {task_type}"}

        pipeline = payload.get("pipeline", "voynich")
        if pipeline not in self._PIPELINES:
            return {
                "status": "error",
                "error": f"unknown pipeline: {pipeline}; supported: {sorted(self._PIPELINES)}",
            }

        script = os.path.join(CODEX_AEON_REPO_PATH, self._PIPELINES[pipeline])
        try:
            result = subprocess.run(
                [sys.executable, script],
                capture_output=True,
                text=True,
                timeout=self._TIMEOUT_SEC,
                cwd=CODEX_AEON_REPO_PATH,
            )
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": f"pipeline {pipeline} timed out after {self._TIMEOUT_SEC}s"}
        except Exception as exc:
            return {"status": "error", "error": f"subprocess failed: {exc}"}

        if result.returncode != 0:
            return {
                "status": "error",
                "error": f"pipeline {pipeline} exit {result.returncode}",
                "stderr": (result.stderr or "")[:1000],
            }

        task_id = _generate_task_id(task_type, payload)
        stdout = result.stdout or ""
        output = {
            "status": "completed",
            "task_id": task_id,
            "task_type": task_type,
            "result": {
                "pipeline": pipeline,
                "stdout": stdout[:4000],
                "stdout_truncated": len(stdout) > 4000,
            },
        }
        self._task_log[task_id] = output
        return output

    def status(self) -> dict[str, Any]:
        return {
            "repo": self.repo_name,
            "available": self._available,
            "coherence": self._coherence,
            "task_log_length": len(self._task_log),
            "supported_types": sorted(self._SUPPORTED_TYPES),
            "repo_path": CODEX_AEON_REPO_PATH,
            "pipelines": sorted(self._PIPELINES.keys()),
        }

    def recall(self, task_id: str) -> Optional[dict[str, Any]]:
        return self._task_log.get(task_id)

    def is_available(self) -> bool:
        return self._available

    def coherence_score(self) -> float:
        return self._coherence

    def set_coherence(self, score: float) -> None:
        self._coherence = max(0.0, min(1.0, score))

    def current_load(self) -> float:
        return 0.0

    def to_json_protocol(self, action: str, **kwargs: Any) -> str:
        msg: dict[str, Any] = {"action": action, "repo": self.repo_name}
        msg.update(kwargs)
        return json.dumps(msg, sort_keys=True)

    @staticmethod
    def parse_json_protocol(raw: str) -> dict[str, Any]:
        return dict(json.loads(raw))


# ===========================================================================
# Extended adapters: EvolutionEngine, SwarmOrchestrator, phi_ucb, eval_api,
# xdomain_bridge, structural_detector, SelfModel, containment_validator
#
# All eight follow the same shape:
#   - own task_type (one per adapter)
#   - fail-closed (`_available` probe at __init__, dispatch returns
#     status="unavailable" if missing)
#   - coherence-gated (`_coherence` field, dispatch rejects when below
#     COHERENCE_THRESHOLD unless payload["force"]=True)
#   - recall() returns task results from self._task_log
#   - to_json_protocol / parse_json_protocol helpers
#
# Each delegates to recursive_field_math.* and returns JSON-serialisable dicts.
# ===========================================================================


def _to_jsonable(obj: Any) -> Any:
    """Coerce numpy arrays and tuples in nested structures to JSON-friendly types."""
    try:
        import numpy as np  # type: ignore

        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.floating, np.integer, np.bool_)):
            return obj.item()
    except ImportError:
        pass
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    return obj


class EvolutionEngineAdapter:
    """
    Adapter for recursive_field_math.evolution.EvolutionEngine.

    Task type: "evolve". Subcommands via payload["action"]:
        observe   — scan agent performance, return gap report
        propose   — generate SCE-88-validated proposals
        simulate  — sandbox-validate proposals, measure coherence delta
        apply     — output versioned change-set with provenance
        state     — engine internal state snapshot
        pipeline  — full pipeline summary

    Stateful: one EvolutionEngine instance per adapter, lazily instantiated.
    """

    _SUPPORTED_TYPES = frozenset({"evolve"})

    def __init__(self) -> None:
        self._task_log: dict[str, dict[str, Any]] = {}
        self._available = self._probe_availability()
        self._coherence: float = 0.5
        self._engine: Any = None

    @property
    def repo_name(self) -> str:
        return "rfm-pro:evolution"

    @property
    def supported_task_types(self) -> frozenset[str]:
        return self._SUPPORTED_TYPES

    @property
    def agent_count(self) -> int:
        return 13

    def _probe_availability(self) -> bool:
        try:
            from recursive_field_math.evolution import EvolutionEngine  # noqa: F401

            return True
        except ImportError:
            return False

    def _ensure_engine(self) -> Any:
        if self._engine is None:
            from recursive_field_math.evolution import EvolutionEngine

            self._engine = EvolutionEngine()
        return self._engine

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._available:
            return {"status": "unavailable", "error": "recursive_field_math.evolution not importable"}
        if self._coherence < COHERENCE_THRESHOLD and not payload.get("force", False):
            return {"status": "coherence_gated", "coherence": self._coherence, "threshold": COHERENCE_THRESHOLD}
        if task_type not in self._SUPPORTED_TYPES:
            return {"status": "error", "error": f"unsupported task_type: {task_type}"}

        action = payload.get("action", "observe")
        try:
            engine = self._ensure_engine()
            if action == "observe":
                metrics = payload.get("metrics")
                result = engine.observe(metrics) if metrics is not None else engine.observe()
            elif action == "propose":
                result = {"proposals": engine.propose()}
            elif action == "simulate":
                proposals = payload.get("proposals")
                result = engine.simulate(proposals) if proposals is not None else engine.simulate()
            elif action == "apply":
                simulation = payload.get("simulation")
                result = engine.apply(simulation) if simulation is not None else engine.apply()
            elif action == "state":
                result = engine.state()
            elif action == "pipeline":
                result = engine.pipeline()
            else:
                return {"status": "error", "error": f"unknown action: {action}"}

            task_id = _generate_task_id(task_type, payload)
            output = {
                "status": "completed",
                "task_id": task_id,
                "task_type": task_type,
                "result": _to_jsonable(result),
            }
            self._task_log[task_id] = output
            return output
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def status(self) -> dict[str, Any]:
        return {
            "repo": self.repo_name,
            "available": self._available,
            "coherence": self._coherence,
            "task_log_length": len(self._task_log),
            "supported_types": sorted(self._SUPPORTED_TYPES),
            "engine_initialized": self._engine is not None,
        }

    def recall(self, task_id: str) -> Optional[dict[str, Any]]:
        return self._task_log.get(task_id)

    def is_available(self) -> bool:
        return self._available

    def coherence_score(self) -> float:
        return self._coherence

    def set_coherence(self, score: float) -> None:
        self._coherence = max(0.0, min(1.0, score))

    def current_load(self) -> float:
        return 0.0

    def to_json_protocol(self, action: str, **kwargs: Any) -> str:
        msg: dict[str, Any] = {"action": action, "repo": self.repo_name}
        msg.update(kwargs)
        return json.dumps(msg, sort_keys=True)

    @staticmethod
    def parse_json_protocol(raw: str) -> dict[str, Any]:
        return dict(json.loads(raw))


class SwarmAdapter:
    """
    Adapter for recursive_field_math.swarm.SwarmOrchestrator.

    Task type: "swarm". Subcommands via payload["action"]:
        status        — orchestrator status (healthy shards, load, coherence)
        scale_auto    — request hardware-aware auto-scale; returns recommendations
        run           — run a batch of input strings; payload["inputs"] = [str, ...]
        balance       — load-balancing recommendations
    """

    _SUPPORTED_TYPES = frozenset({"swarm"})

    def __init__(self) -> None:
        self._task_log: dict[str, dict[str, Any]] = {}
        self._available = self._probe_availability()
        self._coherence: float = 0.5
        self._orch: Any = None

    @property
    def repo_name(self) -> str:
        return "rfm-pro:swarm"

    @property
    def supported_task_types(self) -> frozenset[str]:
        return self._SUPPORTED_TYPES

    @property
    def agent_count(self) -> int:
        if self._orch is not None:
            try:
                return self._orch._num_shards * self._orch._workers_per_shard
            except Exception:
                return 0
        return 0

    def _probe_availability(self) -> bool:
        try:
            from recursive_field_math.swarm import SwarmOrchestrator  # noqa: F401

            return True
        except ImportError:
            return False

    def _ensure_orch(self, num_shards: int = 4, workers_per_shard: int = 4) -> Any:
        if self._orch is None:
            from recursive_field_math.swarm import SwarmOrchestrator

            self._orch = SwarmOrchestrator(
                num_shards=num_shards,
                workers_per_shard=workers_per_shard,
            )
        return self._orch

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._available:
            return {"status": "unavailable", "error": "recursive_field_math.swarm not importable"}
        if self._coherence < COHERENCE_THRESHOLD and not payload.get("force", False):
            return {"status": "coherence_gated", "coherence": self._coherence, "threshold": COHERENCE_THRESHOLD}
        if task_type not in self._SUPPORTED_TYPES:
            return {"status": "error", "error": f"unsupported task_type: {task_type}"}

        action = payload.get("action", "status")
        try:
            orch = self._ensure_orch(
                num_shards=int(payload.get("num_shards", 4)),
                workers_per_shard=int(payload.get("workers_per_shard", 4)),
            )
            if action == "status":
                result = orch.status()
            elif action == "balance":
                result = orch.governor.metrics() if hasattr(orch, "governor") else {"error": "no governor"}
            elif action == "scale_auto":
                if not orch.started:
                    orch.start()
                result = orch.scale_auto()
            elif action == "run":
                inputs = payload.get("inputs", [])
                if not isinstance(inputs, list):
                    return {"status": "error", "error": "payload['inputs'] must be a list of strings"}
                if not orch.started:
                    orch.start()
                results = orch.execute_batch(lambda x: x, [str(i) for i in inputs])
                result = {"inputs": inputs, "results": results, "status": orch.status()}
            else:
                return {"status": "error", "error": f"unknown action: {action}"}

            task_id = _generate_task_id(task_type, payload)
            output = {
                "status": "completed",
                "task_id": task_id,
                "task_type": task_type,
                "result": _to_jsonable(result),
            }
            self._task_log[task_id] = output
            return output
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def status(self) -> dict[str, Any]:
        return {
            "repo": self.repo_name,
            "available": self._available,
            "coherence": self._coherence,
            "task_log_length": len(self._task_log),
            "supported_types": sorted(self._SUPPORTED_TYPES),
            "orchestrator_started": self._orch.started if self._orch is not None else False,
        }

    def recall(self, task_id: str) -> Optional[dict[str, Any]]:
        return self._task_log.get(task_id)

    def is_available(self) -> bool:
        return self._available

    def coherence_score(self) -> float:
        return self._coherence

    def set_coherence(self, score: float) -> None:
        self._coherence = max(0.0, min(1.0, score))

    def current_load(self) -> float:
        if self._orch is None:
            return 0.0
        try:
            metrics = self._orch.governor.metrics()
            return float(metrics.get("coherence_compute_ratio", 0.0))
        except Exception:
            return 0.0

    def to_json_protocol(self, action: str, **kwargs: Any) -> str:
        msg: dict[str, Any] = {"action": action, "repo": self.repo_name}
        msg.update(kwargs)
        return json.dumps(msg, sort_keys=True)

    @staticmethod
    def parse_json_protocol(raw: str) -> dict[str, Any]:
        return dict(json.loads(raw))


class PhiUCBAdapter:
    """
    Adapter for recursive_field_math.phi_ucb (φ-modulated UCB selector).

    Task type: "select". Subcommands via payload["action"]:
        score      — phi_ucb_score(node_stats, t, alpha, beta)
        select     — select_best(children, t, alpha, beta) → index
        benchmark  — benchmark_phi_ucb_vs_ucb1(n_arms, n_steps, seed)
    """

    _SUPPORTED_TYPES = frozenset({"select"})

    def __init__(self) -> None:
        self._task_log: dict[str, dict[str, Any]] = {}
        self._available = self._probe_availability()
        self._coherence: float = 0.5

    @property
    def repo_name(self) -> str:
        return "rfm-pro:phi_ucb"

    @property
    def supported_task_types(self) -> frozenset[str]:
        return self._SUPPORTED_TYPES

    @property
    def agent_count(self) -> int:
        return 0

    def _probe_availability(self) -> bool:
        try:
            from recursive_field_math.phi_ucb import phi_ucb_score  # noqa: F401

            return True
        except ImportError:
            return False

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._available:
            return {"status": "unavailable", "error": "recursive_field_math.phi_ucb not importable"}
        if self._coherence < COHERENCE_THRESHOLD and not payload.get("force", False):
            return {"status": "coherence_gated", "coherence": self._coherence, "threshold": COHERENCE_THRESHOLD}
        if task_type not in self._SUPPORTED_TYPES:
            return {"status": "error", "error": f"unsupported task_type: {task_type}"}

        action = payload.get("action", "score")
        try:
            from recursive_field_math.phi_ucb import (
                DEFAULT_ALPHA,
                DEFAULT_BETA,
                benchmark_phi_ucb_vs_ucb1,
                phi_ucb_score,
                select_best,
            )

            alpha = float(payload.get("alpha", DEFAULT_ALPHA))
            beta = float(payload.get("beta", DEFAULT_BETA))

            if action == "score":
                node_stats = payload.get("node_stats")
                t = int(payload.get("t", 0))
                if not isinstance(node_stats, dict):
                    return {"status": "error", "error": "payload['node_stats'] must be a dict with 'q' and 'n'"}
                score = phi_ucb_score(node_stats, t=t, alpha=alpha, beta=beta)
                # math.inf is not JSON-serialisable
                if score == float("inf"):
                    score_repr = "inf"
                else:
                    score_repr = float(score)
                result = {"score": score_repr, "t": t, "alpha": alpha, "beta": beta}
            elif action == "select":
                children = payload.get("children")
                t = int(payload.get("t", 0))
                if not isinstance(children, list) or not children:
                    return {"status": "error", "error": "payload['children'] must be a non-empty list of dicts"}
                idx = select_best(children, t=t, alpha=alpha, beta=beta)
                result = {"index": int(idx), "t": t, "alpha": alpha, "beta": beta, "n_children": len(children)}
            elif action == "benchmark":
                n_arms = int(payload.get("n_arms", 10))
                n_steps = int(payload.get("n_steps", 1000))
                seed = int(payload.get("seed", 42))
                bench = benchmark_phi_ucb_vs_ucb1(n_arms=n_arms, n_steps=n_steps, seed=seed, alpha=alpha, beta=beta)
                result = bench
            else:
                return {"status": "error", "error": f"unknown action: {action}"}

            task_id = _generate_task_id(task_type, payload)
            output = {
                "status": "completed",
                "task_id": task_id,
                "task_type": task_type,
                "result": _to_jsonable(result),
            }
            self._task_log[task_id] = output
            return output
        except ValueError as exc:
            return {"status": "error", "error": str(exc)}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def status(self) -> dict[str, Any]:
        return {
            "repo": self.repo_name,
            "available": self._available,
            "coherence": self._coherence,
            "task_log_length": len(self._task_log),
            "supported_types": sorted(self._SUPPORTED_TYPES),
        }

    def recall(self, task_id: str) -> Optional[dict[str, Any]]:
        return self._task_log.get(task_id)

    def is_available(self) -> bool:
        return self._available

    def coherence_score(self) -> float:
        return self._coherence

    def set_coherence(self, score: float) -> None:
        self._coherence = max(0.0, min(1.0, score))

    def current_load(self) -> float:
        return 0.0

    def to_json_protocol(self, action: str, **kwargs: Any) -> str:
        msg: dict[str, Any] = {"action": action, "repo": self.repo_name}
        msg.update(kwargs)
        return json.dumps(msg, sort_keys=True)

    @staticmethod
    def parse_json_protocol(raw: str) -> dict[str, Any]:
        return dict(json.loads(raw))


class EvalAPIAdapter:
    """
    Adapter for recursive_field_math.eval_api.score / calibration_report.

    Task type: "score". Subcommands via payload["action"]:
        score        — score a single sequence (mode="numeric" | "tokens" | "actions")
        calibration  — score a list of sequences and aggregate
    """

    _SUPPORTED_TYPES = frozenset({"score"})

    def __init__(self) -> None:
        self._task_log: dict[str, dict[str, Any]] = {}
        self._available = self._probe_availability()
        self._coherence: float = 0.5

    @property
    def repo_name(self) -> str:
        return "rfm-pro:eval_api"

    @property
    def supported_task_types(self) -> frozenset[str]:
        return self._SUPPORTED_TYPES

    @property
    def agent_count(self) -> int:
        return 0

    def _probe_availability(self) -> bool:
        try:
            from recursive_field_math.eval_api import score  # noqa: F401

            return True
        except ImportError:
            return False

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._available:
            return {"status": "unavailable", "error": "recursive_field_math.eval_api not importable"}
        if self._coherence < COHERENCE_THRESHOLD and not payload.get("force", False):
            return {"status": "coherence_gated", "coherence": self._coherence, "threshold": COHERENCE_THRESHOLD}
        if task_type not in self._SUPPORTED_TYPES:
            return {"status": "error", "error": f"unsupported task_type: {task_type}"}

        action = payload.get("action", "score")
        try:
            from recursive_field_math.eval_api import (
                PROFILE_NAME,
                calibration_report,
                score as eval_score,
            )

            mode = payload.get("mode", "numeric")
            profile = payload.get("profile", PROFILE_NAME)

            if action == "score":
                sequence = payload.get("sequence")
                if not isinstance(sequence, list):
                    return {"status": "error", "error": "payload['sequence'] must be a list"}
                result = eval_score(sequence, mode=mode, profile=profile)
            elif action == "calibration":
                sequences = payload.get("sequences")
                if not isinstance(sequences, list) or not all(isinstance(s, list) for s in sequences):
                    return {"status": "error", "error": "payload['sequences'] must be a list of lists"}
                result = calibration_report(sequences, profile=profile)
            else:
                return {"status": "error", "error": f"unknown action: {action}"}

            task_id = _generate_task_id(task_type, payload)
            output = {
                "status": "completed",
                "task_id": task_id,
                "task_type": task_type,
                "result": _to_jsonable(result),
            }
            self._task_log[task_id] = output
            return output
        except ValueError as exc:
            return {"status": "error", "error": str(exc)}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def status(self) -> dict[str, Any]:
        return {
            "repo": self.repo_name,
            "available": self._available,
            "coherence": self._coherence,
            "task_log_length": len(self._task_log),
            "supported_types": sorted(self._SUPPORTED_TYPES),
        }

    def recall(self, task_id: str) -> Optional[dict[str, Any]]:
        return self._task_log.get(task_id)

    def is_available(self) -> bool:
        return self._available

    def coherence_score(self) -> float:
        return self._coherence

    def set_coherence(self, score: float) -> None:
        self._coherence = max(0.0, min(1.0, score))

    def current_load(self) -> float:
        return 0.0

    def to_json_protocol(self, action: str, **kwargs: Any) -> str:
        msg: dict[str, Any] = {"action": action, "repo": self.repo_name}
        msg.update(kwargs)
        return json.dumps(msg, sort_keys=True)

    @staticmethod
    def parse_json_protocol(raw: str) -> dict[str, Any]:
        return dict(json.loads(raw))


class BridgeAdapter:
    """
    Adapter for recursive_field_math.xdomain_bridge (encode / decode / bridge).

    Task type: "bridge". Subcommands via payload["action"]:
        encode  — encode(sequence, domain) → LatentVector dict
        decode  — decode(latent_vector) → reconstructed sequence
        bridge  — bridge(sequence, src_domain, dst_domain) → cross-domain
    """

    _SUPPORTED_TYPES = frozenset({"bridge"})

    def __init__(self) -> None:
        self._task_log: dict[str, dict[str, Any]] = {}
        self._available = self._probe_availability()
        self._coherence: float = 0.5

    @property
    def repo_name(self) -> str:
        return "rfm-pro:xdomain_bridge"

    @property
    def supported_task_types(self) -> frozenset[str]:
        return self._SUPPORTED_TYPES

    @property
    def agent_count(self) -> int:
        return 0

    def _probe_availability(self) -> bool:
        try:
            from recursive_field_math.xdomain_bridge import encode  # noqa: F401

            return True
        except ImportError:
            return False

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._available:
            return {"status": "unavailable", "error": "recursive_field_math.xdomain_bridge not importable"}
        if self._coherence < COHERENCE_THRESHOLD and not payload.get("force", False):
            return {"status": "coherence_gated", "coherence": self._coherence, "threshold": COHERENCE_THRESHOLD}
        if task_type not in self._SUPPORTED_TYPES:
            return {"status": "error", "error": f"unsupported task_type: {task_type}"}

        action = payload.get("action", "encode")
        try:
            from recursive_field_math.xdomain_bridge import (
                BridgeError,
                N_LATENT,
                bridge as bridge_fn,
                decode,
                encode,
            )

            n_latent = int(payload.get("n_latent", N_LATENT))

            if action == "encode":
                sequence = payload.get("sequence")
                domain = payload.get("domain", "numeric")
                if not isinstance(sequence, list):
                    return {"status": "error", "error": "payload['sequence'] must be a list"}
                result = encode(sequence, domain=domain, n_latent=n_latent)
            elif action == "decode":
                latent = payload.get("latent_vector")
                if not isinstance(latent, dict):
                    return {"status": "error", "error": "payload['latent_vector'] must be a dict from encode()"}
                reconstructed = decode(latent, check_error_bound=False)
                result = {"reconstructed": reconstructed, "n_output": len(reconstructed)}
            elif action == "bridge":
                sequence = payload.get("sequence")
                src = payload.get("src_domain", "numeric")
                dst = payload.get("dst_domain", "numeric")
                if not isinstance(sequence, list):
                    return {"status": "error", "error": "payload['sequence'] must be a list"}
                result = bridge_fn(sequence, src_domain=src, dst_domain=dst, n_latent=n_latent)
            else:
                return {"status": "error", "error": f"unknown action: {action}"}

            task_id = _generate_task_id(task_type, payload)
            output = {
                "status": "completed",
                "task_id": task_id,
                "task_type": task_type,
                "result": _to_jsonable(result),
            }
            self._task_log[task_id] = output
            return output
        except BridgeError as exc:
            return {"status": "error", "error": f"BridgeError: {exc}"}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def status(self) -> dict[str, Any]:
        return {
            "repo": self.repo_name,
            "available": self._available,
            "coherence": self._coherence,
            "task_log_length": len(self._task_log),
            "supported_types": sorted(self._SUPPORTED_TYPES),
        }

    def recall(self, task_id: str) -> Optional[dict[str, Any]]:
        return self._task_log.get(task_id)

    def is_available(self) -> bool:
        return self._available

    def coherence_score(self) -> float:
        return self._coherence

    def set_coherence(self, score: float) -> None:
        self._coherence = max(0.0, min(1.0, score))

    def current_load(self) -> float:
        return 0.0

    def to_json_protocol(self, action: str, **kwargs: Any) -> str:
        msg: dict[str, Any] = {"action": action, "repo": self.repo_name}
        msg.update(kwargs)
        return json.dumps(msg, sort_keys=True)

    @staticmethod
    def parse_json_protocol(raw: str) -> dict[str, Any]:
        return dict(json.loads(raw))


class DetectorAdapter:
    """
    Adapter for recursive_field_math.structural_detector.detect().

    Task type: "detect". Single action returns structural_signature,
    anomaly_index, coherence_trace from a numeric sequence.
    """

    _SUPPORTED_TYPES = frozenset({"detect"})

    def __init__(self) -> None:
        self._task_log: dict[str, dict[str, Any]] = {}
        self._available = self._probe_availability()
        self._coherence: float = 0.5

    @property
    def repo_name(self) -> str:
        return "rfm-pro:structural_detector"

    @property
    def supported_task_types(self) -> frozenset[str]:
        return self._SUPPORTED_TYPES

    @property
    def agent_count(self) -> int:
        return 0

    def _probe_availability(self) -> bool:
        try:
            from recursive_field_math.structural_detector import detect  # noqa: F401

            return True
        except ImportError:
            return False

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._available:
            return {"status": "unavailable", "error": "recursive_field_math.structural_detector not importable"}
        if self._coherence < COHERENCE_THRESHOLD and not payload.get("force", False):
            return {"status": "coherence_gated", "coherence": self._coherence, "threshold": COHERENCE_THRESHOLD}
        if task_type not in self._SUPPORTED_TYPES:
            return {"status": "error", "error": f"unsupported task_type: {task_type}"}

        try:
            from recursive_field_math.structural_detector import (
                N_HARMONICS,
                WINDOW_SIZE,
                detect,
            )

            sequence = payload.get("sequence")
            if not isinstance(sequence, list):
                return {"status": "error", "error": "payload['sequence'] must be a list"}
            window_size = int(payload.get("window_size", WINDOW_SIZE))
            n_harmonics = int(payload.get("n_harmonics", N_HARMONICS))

            result = detect(sequence, window_size=window_size, n_harmonics=n_harmonics)

            task_id = _generate_task_id(task_type, payload)
            output = {
                "status": "completed",
                "task_id": task_id,
                "task_type": task_type,
                "result": _to_jsonable(result),
            }
            self._task_log[task_id] = output
            return output
        except ValueError as exc:
            return {"status": "error", "error": str(exc)}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def status(self) -> dict[str, Any]:
        return {
            "repo": self.repo_name,
            "available": self._available,
            "coherence": self._coherence,
            "task_log_length": len(self._task_log),
            "supported_types": sorted(self._SUPPORTED_TYPES),
        }

    def recall(self, task_id: str) -> Optional[dict[str, Any]]:
        return self._task_log.get(task_id)

    def is_available(self) -> bool:
        return self._available

    def coherence_score(self) -> float:
        return self._coherence

    def set_coherence(self, score: float) -> None:
        self._coherence = max(0.0, min(1.0, score))

    def current_load(self) -> float:
        return 0.0

    def to_json_protocol(self, action: str, **kwargs: Any) -> str:
        msg: dict[str, Any] = {"action": action, "repo": self.repo_name}
        msg.update(kwargs)
        return json.dumps(msg, sort_keys=True)

    @staticmethod
    def parse_json_protocol(raw: str) -> dict[str, Any]:
        return dict(json.loads(raw))


class SelfModelAdapter:
    """
    Adapter for recursive_field_math.self_model.SelfModel.

    Task type: "self_model". Stateful: holds a single SelfModel instance.
    Subcommands via payload["action"]:
        observe    — observe(input_pattern) → delta
        ask        — ask() → query dict or null
        integrate  — integrate(new_data) → ok + state
        state      — state() snapshot
        reset      — discard the instance, recreate on next call
    """

    _SUPPORTED_TYPES = frozenset({"self_model"})

    def __init__(self) -> None:
        self._task_log: dict[str, dict[str, Any]] = {}
        self._available = self._probe_availability()
        self._coherence: float = 0.5
        self._sm: Any = None

    @property
    def repo_name(self) -> str:
        return "rfm-pro:self_model"

    @property
    def supported_task_types(self) -> frozenset[str]:
        return self._SUPPORTED_TYPES

    @property
    def agent_count(self) -> int:
        return 0

    def _probe_availability(self) -> bool:
        try:
            from recursive_field_math.self_model import SelfModel  # noqa: F401

            return True
        except ImportError:
            return False

    def _ensure_sm(self) -> Any:
        if self._sm is None:
            from recursive_field_math.self_model import SelfModel

            self._sm = SelfModel()
        return self._sm

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._available:
            return {"status": "unavailable", "error": "recursive_field_math.self_model not importable"}
        if self._coherence < COHERENCE_THRESHOLD and not payload.get("force", False):
            return {"status": "coherence_gated", "coherence": self._coherence, "threshold": COHERENCE_THRESHOLD}
        if task_type not in self._SUPPORTED_TYPES:
            return {"status": "error", "error": f"unsupported task_type: {task_type}"}

        action = payload.get("action", "state")
        try:
            if action == "reset":
                self._sm = None
                result = {"reset": True}
            else:
                sm = self._ensure_sm()
                if action == "observe":
                    pattern = payload.get("input", "")
                    if not isinstance(pattern, str):
                        return {"status": "error", "error": "payload['input'] must be a string"}
                    delta = sm.observe(pattern)
                    result = {"delta": delta, "state": sm.state()}
                elif action == "ask":
                    q = sm.ask()
                    result = {"query": q}
                elif action == "integrate":
                    new_data = payload.get("data", "")
                    if not isinstance(new_data, str):
                        return {"status": "error", "error": "payload['data'] must be a plain string; sm.integrate() accepts raw text, not parsed dicts"}
                    result = sm.integrate(new_data)
                elif action == "state":
                    result = sm.state()  # state() is a method on RFM-Pro SelfModel, not a property
                else:
                    return {"status": "error", "error": f"unknown action: {action}"}

            task_id = _generate_task_id(task_type, payload)
            output = {
                "status": "completed",
                "task_id": task_id,
                "task_type": task_type,
                "result": _to_jsonable(result),
            }
            self._task_log[task_id] = output
            return output
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def status(self) -> dict[str, Any]:
        return {
            "repo": self.repo_name,
            "available": self._available,
            "coherence": self._coherence,
            "task_log_length": len(self._task_log),
            "supported_types": sorted(self._SUPPORTED_TYPES),
            "sm_initialized": self._sm is not None,
        }

    def recall(self, task_id: str) -> Optional[dict[str, Any]]:
        return self._task_log.get(task_id)

    def is_available(self) -> bool:
        return self._available

    def coherence_score(self) -> float:
        return self._coherence

    def set_coherence(self, score: float) -> None:
        self._coherence = max(0.0, min(1.0, score))

    def current_load(self) -> float:
        return 0.0

    def to_json_protocol(self, action: str, **kwargs: Any) -> str:
        msg: dict[str, Any] = {"action": action, "repo": self.repo_name}
        msg.update(kwargs)
        return json.dumps(msg, sort_keys=True)

    @staticmethod
    def parse_json_protocol(raw: str) -> dict[str, Any]:
        return dict(json.loads(raw))


class ContainmentValidatorAdapter:
    """
    Adapter for recursive_field_math.containment_validator.validate().

    Task type: "validate". Validates an architecture spec dict and returns
    containment_score, weak_layer_map, escape_path_candidates.

    Distinct from SCE-88's adapter which validates the fixed 4-domain × 22-level
    canonical SCE-88 unit. This one validates arbitrary user-provided specs.
    """

    _SUPPORTED_TYPES = frozenset({"validate"})

    def __init__(self) -> None:
        self._task_log: dict[str, dict[str, Any]] = {}
        self._available = self._probe_availability()
        self._coherence: float = 0.5

    @property
    def repo_name(self) -> str:
        return "rfm-pro:containment_validator"

    @property
    def supported_task_types(self) -> frozenset[str]:
        return self._SUPPORTED_TYPES

    @property
    def agent_count(self) -> int:
        return 0

    def _probe_availability(self) -> bool:
        try:
            from recursive_field_math.containment_validator import validate  # noqa: F401

            return True
        except ImportError:
            return False

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._available:
            return {"status": "unavailable", "error": "recursive_field_math.containment_validator not importable"}
        if self._coherence < COHERENCE_THRESHOLD and not payload.get("force", False):
            return {"status": "coherence_gated", "coherence": self._coherence, "threshold": COHERENCE_THRESHOLD}
        if task_type not in self._SUPPORTED_TYPES:
            return {"status": "error", "error": f"unsupported task_type: {task_type}"}

        try:
            from recursive_field_math.containment_validator import validate

            spec = payload.get("spec")
            if not isinstance(spec, dict):
                return {"status": "error", "error": "payload['spec'] must be a dict with a 'layers' key"}
            top_k = int(payload.get("top_k_escapes", 5))

            result = validate(spec, top_k_escapes=top_k)

            task_id = _generate_task_id(task_type, payload)
            output = {
                "status": "completed" if result.get("ok") else "violation",
                "task_id": task_id,
                "task_type": task_type,
                "result": _to_jsonable(result),
            }
            self._task_log[task_id] = output
            return output
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def status(self) -> dict[str, Any]:
        return {
            "repo": self.repo_name,
            "available": self._available,
            "coherence": self._coherence,
            "task_log_length": len(self._task_log),
            "supported_types": sorted(self._SUPPORTED_TYPES),
        }

    def recall(self, task_id: str) -> Optional[dict[str, Any]]:
        return self._task_log.get(task_id)

    def is_available(self) -> bool:
        return self._available

    def coherence_score(self) -> float:
        return self._coherence

    def set_coherence(self, score: float) -> None:
        self._coherence = max(0.0, min(1.0, score))

    def current_load(self) -> float:
        return 0.0

    def to_json_protocol(self, action: str, **kwargs: Any) -> str:
        msg: dict[str, Any] = {"action": action, "repo": self.repo_name}
        msg.update(kwargs)
        return json.dumps(msg, sort_keys=True)

    @staticmethod
    def parse_json_protocol(raw: str) -> dict[str, Any]:
        return dict(json.loads(raw))


def _generate_task_id(task_type: str, payload: dict[str, Any]) -> str:
    """Generate a deterministic task ID."""
    import hashlib

    raw = f"{task_type}:{json.dumps(payload, sort_keys=True)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def create_default_mesh() -> Any:
    """
    Create a FederationMesh pre-configured with standard wizardaax adapters.

    Registers Snell-Vern-Hybrid-Drive-Matrix and recursive-field-math-pro.
    """
    from .mesh import FederationMesh

    mesh = FederationMesh()

    sv_adapter = SnellVernAdapter()
    mesh.register_repo(
        repo_name=sv_adapter.repo_name,
        task_types=sv_adapter.supported_task_types,
        agent_count=sv_adapter.agent_count,
        adapter=sv_adapter,
    )

    rfm_adapter = RFMProAdapter()
    mesh.register_repo(
        repo_name=rfm_adapter.repo_name,
        task_types=rfm_adapter.supported_task_types,
        agent_count=rfm_adapter.agent_count,
        adapter=rfm_adapter,
    )

    glyph_adapter = GlyphPhaseAdapter()
    mesh.register_repo(
        repo_name=glyph_adapter.repo_name,
        task_types=glyph_adapter.supported_task_types,
        agent_count=glyph_adapter.agent_count,
        adapter=glyph_adapter,
    )

    sce88_adapter = SCE88Adapter()
    mesh.register_repo(
        repo_name=sce88_adapter.repo_name,
        task_types=sce88_adapter.supported_task_types,
        agent_count=sce88_adapter.agent_count,
        adapter=sce88_adapter,
    )

    codex_adapter = CodexAeonAdapter()
    mesh.register_repo(
        repo_name=codex_adapter.repo_name,
        task_types=codex_adapter.supported_task_types,
        agent_count=codex_adapter.agent_count,
        adapter=codex_adapter,
    )

    # Content-only repos via the generic RepoDocumentAdapter.
    # task_types chosen per repo's natural fit:
    #   recursive-field-math, ziltrix-sch-core, wizardaax.github.io  -> documentation
    #   rff-agent-logs, sim_outputs                                  -> observation
    doc_repos = [
        ("recursive-field-math", "recursive-field-math", frozenset({"documentation"})),
        ("ziltrix-sch-core", "ziltrix-sch-core", frozenset({"documentation"})),
        ("wizardaax.github.io", "wizardaax.github.io", frozenset({"documentation"})),
        ("rff-agent-logs", "rff-agent-logs", frozenset({"observation"})),
        ("sim_outputs", "sim_outputs", frozenset({"observation"})),
    ]
    for repo_name, dirname, task_types in doc_repos:
        import os as _os

        repo_path = _os.path.join(WIZARDAAX_ROOT, dirname)
        adapter = RepoDocumentAdapter(
            repo_name=repo_name,
            repo_path=repo_path,
            task_types=task_types,
        )
        mesh.register_repo(
            repo_name=adapter.repo_name,
            task_types=adapter.supported_task_types,
            agent_count=adapter.agent_count,
            adapter=adapter,
        )

    # Note: EvolutionEngineAdapter / SwarmAdapter / PhiUCBAdapter / EvalAPIAdapter
    # / BridgeAdapter / DetectorAdapter / SelfModelAdapter / ContainmentValidatorAdapter
    # are NOT registered separately — they're submodules of recursive-field-math-pro
    # and are multiplexed inside RFMProAdapter under that single repo entry.
    # Mesh callers reach them via task_type (evolve / swarm / select / score /
    # bridge / detect / self_model / validate), all routing to repo
    # "recursive-field-math-pro".

    # Register the 4 previously-missing per-repo adapters (Jarvis, MemoryVault, Xova, Ziltrix).
    # These were gaps surfaced by the 2026-05-02 federation coverage audit — 4 of 11
    # wizardaax repos had no adapter, so the mesh couldn't route goals to them.
    for adapter_cls in (JarvisAdapter, MemoryVaultAdapter, XovaAdapter, ZiltrixAdapter):
        try:
            ad = adapter_cls()
            mesh.register_repo(
                repo_name=ad.repo_name,
                task_types=ad.supported_task_types,
                agent_count=ad.agent_count,
                adapter=ad,
            )
        except Exception:
            # Adapter scaffolds are placeholder; if their repo isn't on disk,
            # skip registration silently rather than fail the mesh build.
            continue

    return mesh


# ── Filesystem-probe adapters (added 2026-05-02 — close 4-of-11 gap) ─────────
#
# These four adapters were missing from the federation. Each is a minimal
# scaffold satisfying RepoAdapter Protocol — enough for FederationMesh routing
# to recognise the repo as available + report its status. Real dispatch logic
# (per task_type) can be filled in later as needed; the immediate purpose is
# closing the coverage gap so RoutingDecision sees all 11 wizardaax repos.

import os as _os
import time as _time
from typing import Any as _Any, Optional as _Optional


class _FilesystemRepoAdapter:
    """Shared base for adapters that detect the repo via its filesystem path
    and answer status() / coherence_score() / current_load() from disk state.
    Subclasses set ``REPO_NAME``, ``REPO_PATH``, ``TASK_TYPES``, ``AGENT_COUNT``."""

    REPO_NAME: str = ""
    REPO_PATH: str = ""
    TASK_TYPES: frozenset[str] = frozenset()
    AGENT_COUNT: int = 1

    def __init__(self) -> None:
        self._task_log: dict[str, dict[str, _Any]] = {}

    @property
    def repo_name(self) -> str:
        return self.REPO_NAME

    @property
    def supported_task_types(self) -> frozenset[str]:
        return self.TASK_TYPES

    @property
    def agent_count(self) -> int:
        return self.AGENT_COUNT

    def is_available(self) -> bool:
        return _os.path.isdir(self.REPO_PATH)

    def coherence_score(self) -> float:
        # Default: present-on-disk = 0.7 (baseline healthy), missing = 0.0
        return 0.7 if self.is_available() else 0.0

    def current_load(self) -> float:
        # No live worker queue; report 0.0 (free). Subclasses can override.
        return 0.0

    def status(self) -> dict[str, _Any]:
        return {
            "repo_name": self.repo_name,
            "available": self.is_available(),
            "repo_path": self.REPO_PATH,
            "task_types": sorted(self.supported_task_types),
            "agent_count": self.agent_count,
            "coherence_score": self.coherence_score(),
            "current_load": self.current_load(),
            "tasks_logged": len(self._task_log),
        }

    def dispatch(self, task_type: str, payload: dict[str, _Any]) -> dict[str, _Any]:
        if not self.is_available():
            return {"status": "error", "error": f"{self.repo_name} repo not on disk at {self.REPO_PATH}"}
        if task_type not in self.supported_task_types:
            return {"status": "rejected", "reason": f"task_type {task_type!r} not in supported set",
                    "supported": sorted(self.supported_task_types)}
        # Placeholder dispatch — log + acknowledge. Real per-task logic lives in
        # the subclass (override this method when the repo gets a callable surface).
        task_id = _generate_task_id(task_type, payload)
        out = {
            "status": "acknowledged",
            "task_id": task_id,
            "task_type": task_type,
            "repo": self.repo_name,
            "note": "scaffold adapter — see per-repo adapter to enable real dispatch",
            "payload_keys": sorted(payload.keys()) if isinstance(payload, dict) else None,
        }
        self._task_log[task_id] = out
        return out

    def recall(self, task_id: str) -> _Optional[dict[str, _Any]]:
        return self._task_log.get(task_id)


class JarvisAdapter(_FilesystemRepoAdapter):
    """Jarvis voice-butler daemon at C:\\jarvis. Bridge: jarvis_inbox.json /
    voice_inbox.json. Adapter doesn't restart the daemon — only routes
    voice / butler-task goals through the existing file bridge."""

    REPO_NAME = "jarvis"
    REPO_PATH = r"C:\jarvis"
    TASK_TYPES = frozenset({"voice", "butler", "remind", "weather", "memory_query", "diary"})
    AGENT_COUNT = 17  # Jarvis has 17 builtin tools (per agi_stack_architecture.md)

    def coherence_score(self) -> float:
        # Use Jarvis SQLite WAL recency as the liveness proxy (privilege-independent
        # signal — same approach as D:\temp\jarvis_health.py). Younger = more coherent.
        if not self.is_available():
            return 0.0
        # Build path via os.path.join so it is correct on both Windows and Linux.
        # Jarvis stores its DB at ~/.local/share/jarvis/jarvis.db on both platforms
        # (Path.home() / ".local" / "share" / "jarvis" in jarvis/config.py).
        _db = _os.path.join(_os.path.expanduser("~"), ".local", "share", "jarvis", "jarvis.db")
        wal = _db + "-wal"
        # Prefer WAL (updated on every SQLite write); fall back to the .db itself.
        target = wal if _os.path.exists(wal) else (_db if _os.path.exists(_db) else None)
        if target is None:
            return 0.4  # daemon may be running without WAL writes lately
        age_s = _time.time() - _os.path.getmtime(target)
        # Linear: <60s = 0.95, 600s = 0.5, >3600s = 0.2
        if age_s < 60:
            return 0.95
        if age_s < 600:
            return 0.5 + 0.45 * (1 - (age_s - 60) / 540)
        if age_s < 3600:
            return 0.2 + 0.3 * (1 - (age_s - 600) / 3000)
        return 0.2


class MemoryVaultAdapter(_FilesystemRepoAdapter):
    """Append-only memory vault at C:\\memory-vault. Adapter routes
    snapshot / restore / search goals to the vault."""

    REPO_NAME = "memory-vault"
    REPO_PATH = r"C:\memory-vault"
    TASK_TYPES = frozenset({"snapshot", "restore", "vault_search", "vault_status"})
    AGENT_COUNT = 1

    def coherence_score(self) -> float:
        if not self.is_available():
            return 0.0
        # Count timestamped snapshot dirs as a health signal — more snapshots = healthier
        try:
            import re as _re
            snaps = [d for d in _os.listdir(self.REPO_PATH)
                     if _re.match(r"\d{8}_\d{6}$", d)]
            n = len(snaps)
            if n >= 30:
                return 0.95
            if n >= 10:
                return 0.7
            if n >= 1:
                return 0.5
            return 0.3
        except OSError:
            return 0.3


class XovaAdapter(_FilesystemRepoAdapter):
    """Xova Tauri desktop agent at C:\\Xova\\app. Adapter routes UI / chat /
    dispatch goals via the existing Tauri command surface (xova_run, etc.).
    Available when the source tree is on disk; the running app is reachable
    via the file-bridge inboxes (xova_chat_inbox, xova_command_inbox, etc.)."""

    REPO_NAME = "xova"
    REPO_PATH = r"C:\Xova\app"
    TASK_TYPES = frozenset({"chat", "ui", "dispatch", "vision", "screen", "panel_toggle"})
    AGENT_COUNT = 41  # 41 Tauri commands (per agi_stack_architecture.md)

    def coherence_score(self) -> float:
        if not self.is_available():
            return 0.0
        # Probe the Xova chat inbox file freshness — recent activity = high coherence
        inbox = r"C:\Xova\memory\xova_chat_inbox.json"
        if not _os.path.exists(inbox):
            return 0.6
        age_s = _time.time() - _os.path.getmtime(inbox)
        if age_s < 300:
            return 0.95
        if age_s < 3600:
            return 0.7
        return 0.5


class ZiltrixAdapter(_FilesystemRepoAdapter):
    """Ziltrix Sentinel Cognitive Hybridiser at D:\\github\\wizardaax\\ziltrix-sch-core.
    Houses AEON Engine v2.1 + 41 research PDFs. Routes AEON / glyph /
    cognition-research goals to the repo's runnable Python module.

    AEON Sprint 1: dispatch("aeon", ...) calls aeon_engine.aeon_summary()
    and returns the full thrust series + validation — real computation, not
    a scaffold acknowledgement.
    """

    REPO_NAME = "ziltrix-sch-core"
    REPO_PATH = r"D:\github\wizardaax\ziltrix-sch-core"
    TASK_TYPES = frozenset({"aeon", "glyph", "cognition_research", "scale_field", "thrust_sim"})
    AGENT_COUNT = 1

    def coherence_score(self) -> float:
        if not self.is_available():
            return 0.0
        mod = _os.path.join(self.REPO_PATH, "aeon_engine.py")
        return 0.9 if _os.path.exists(mod) else 0.5

    def dispatch(self, task_type: str, payload: dict[str, _Any]) -> dict[str, _Any]:
        if not self.is_available():
            return {"status": "error", "error": f"ziltrix-sch-core not on disk at {self.REPO_PATH}"}
        if task_type not in self.supported_task_types:
            return {"status": "rejected", "reason": f"task_type {task_type!r} not supported",
                    "supported": sorted(self.supported_task_types)}

        if task_type == "aeon":
            return self._dispatch_aeon(payload)

        # Other task types — scaffold acknowledgement until real dispatch is needed
        task_id = _generate_task_id(task_type, payload)
        out = {
            "status": "acknowledged",
            "task_id": task_id,
            "task_type": task_type,
            "repo": self.REPO_NAME,
            "note": f"task_type {task_type!r} — scaffold; aeon is the live path",
        }
        self._task_log[task_id] = out
        return out

    def _dispatch_aeon(self, payload: dict[str, _Any]) -> dict[str, _Any]:
        """Call aeon_engine.aeon_summary() from the ziltrix-sch-core repo."""
        import sys
        engine_path = self.REPO_PATH
        if engine_path not in sys.path:
            sys.path.insert(0, engine_path)
        try:
            import importlib
            # Reload in case the module was already cached from another path
            if "aeon_engine" not in sys.modules:
                import aeon_engine  # type: ignore[import-not-found]
            else:
                aeon_engine = sys.modules["aeon_engine"]  # type: ignore[assignment]
            summary = aeon_engine.aeon_summary()
            task_id = _generate_task_id("aeon", payload)
            out = {
                "status": "completed",
                "task_id": task_id,
                "task_type": "aeon",
                "repo": self.REPO_NAME,
                "action": "aeon",
                "ran": True,
                "constants": summary["constants"],
                "thrust_series": summary["thrust_series"],
                "validation": summary["validation"],
            }
            self._task_log[task_id] = out
            return out
        except Exception as exc:
            return {
                "status": "error",
                "task_type": "aeon",
                "repo": self.REPO_NAME,
                "action": "aeon",
                "ran": False,
                "reason": str(exc),
            }
