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

    Provides coherence-gated access to RFM-Pro core functionality
    (math, field, signature analysis).  Since RFM-Pro is an external
    dependency, this adapter wraps available functions with fallback
    handling if the dependency is unavailable.
    """

    _SUPPORTED_TYPES = frozenset({"math", "field", "coherence"})

    def __init__(self) -> None:
        self._task_log: dict[str, dict[str, Any]] = {}
        self._available = self._probe_availability()
        self._coherence: float = 0.5

    @property
    def repo_name(self) -> str:
        return "recursive-field-math-pro"

    @property
    def supported_task_types(self) -> frozenset[str]:
        return self._SUPPORTED_TYPES

    @property
    def agent_count(self) -> int:
        return 0  # RFM-Pro has no local agent system

    def _probe_availability(self) -> bool:
        """Check if recursive_field_math is importable."""
        try:
            import recursive_field_math  # noqa: F401

            return True
        except ImportError:
            return False

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Dispatch a task to RFM-Pro core.

        Performs coherence gating: rejects tasks when coherence is below
        COHERENCE_THRESHOLD, unless a force flag is set.
        """
        if not self._available:
            return {"status": "unavailable", "error": "recursive_field_math not found"}

        if self._coherence < COHERENCE_THRESHOLD and not payload.get("force", False):
            return {
                "status": "coherence_gated",
                "coherence": self._coherence,
                "threshold": COHERENCE_THRESHOLD,
            }

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
        """Execute an RFM-Pro operation based on task type."""
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
        """Return status of the RFM-Pro adapter."""
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
        """RFM-Pro has no queue; load is always 0."""
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

    return mesh
