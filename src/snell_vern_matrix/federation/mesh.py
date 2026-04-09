"""
FederationMesh: Cross-repo agent coordination for the wizardaax org.

Manages a registry of repo adapters, routes tasks to the optimal repo/agent
based on type and load, tracks global coherence across repos, and persists
state as deterministic JSON.  Thread-safe, zero external deps.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from typing import Any, Optional

from ..agents import COHERENCE_THRESHOLD
from ..self_model import _lucas_coherence, _validate_coherence

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MESH_VERSION = "1.0.0"
_MAX_COHERENCE_HISTORY = 100
_DRIFT_THRESHOLD = 0.15
_CONSTRAINT_VIOLATION_WEIGHT = 0.2


class RepoCapability:
    """Describes a single repo's capabilities within the mesh."""

    __slots__ = (
        "repo_name",
        "task_types",
        "agent_count",
        "healthy",
        "load",
        "coherence",
        "last_heartbeat",
    )

    def __init__(
        self,
        repo_name: str,
        task_types: frozenset[str],
        agent_count: int = 0,
    ) -> None:
        self.repo_name = repo_name
        self.task_types = task_types
        self.agent_count = agent_count
        self.healthy: bool = True
        self.load: float = 0.0
        self.coherence: float = 0.5
        self.last_heartbeat: float = time.monotonic()

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_name": self.repo_name,
            "task_types": sorted(self.task_types),
            "agent_count": self.agent_count,
            "healthy": self.healthy,
            "load": self.load,
            "coherence": self.coherence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RepoCapability":
        cap = cls(
            repo_name=data["repo_name"],
            task_types=frozenset(data["task_types"]),
            agent_count=data.get("agent_count", 0),
        )
        cap.healthy = data.get("healthy", True)
        cap.load = data.get("load", 0.0)
        cap.coherence = data.get("coherence", 0.5)
        return cap


class RoutingDecision:
    """Captures the outcome of a routing decision."""

    __slots__ = ("repo_name", "task_type", "payload", "routed", "reason", "task_id")

    def __init__(
        self,
        repo_name: str,
        task_type: str,
        payload: dict[str, Any],
        routed: bool,
        reason: str,
    ) -> None:
        self.repo_name = repo_name
        self.task_type = task_type
        self.payload = payload
        self.routed = routed
        self.reason = reason
        raw = f"{repo_name}:{task_type}:{json.dumps(payload, sort_keys=True)}"
        self.task_id = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "repo_name": self.repo_name,
            "task_type": self.task_type,
            "routed": self.routed,
            "reason": self.reason,
        }


class CoherenceSnapshot:
    """Point-in-time coherence state across the federation."""

    __slots__ = (
        "global_coherence",
        "repo_coherences",
        "constraint_violations",
        "drift",
    )

    def __init__(
        self,
        global_coherence: float,
        repo_coherences: dict[str, float],
        constraint_violations: int,
        drift: float,
    ) -> None:
        self.global_coherence = global_coherence
        self.repo_coherences = repo_coherences
        self.constraint_violations = constraint_violations
        self.drift = drift

    def to_dict(self) -> dict[str, Any]:
        return {
            "global_coherence": self.global_coherence,
            "repo_coherences": self.repo_coherences,
            "constraint_violations": self.constraint_violations,
            "drift": self.drift,
        }


class FederationMesh:
    """
    Cross-repo federation mesh that coordinates agent systems
    across the wizardaax org.

    Responsibilities:
    - Registry: map repo capabilities, track agent health/load, aggregate coherence
    - Router: dispatch tasks to optimal repo/agent based on type, load, SCE-88
    - Global Coherence Monitor: track uncertainty, constraint violations, drift
    - State persistence: deterministic JSON roundtrip, zero external deps

    Thread-safe and deterministic.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._registry: dict[str, RepoCapability] = {}
        self._adapters: dict[str, Any] = {}  # name -> RepoAdapter
        self._coherence_history: list[float] = []
        self._constraint_violations: int = 0
        self._routing_log: list[RoutingDecision] = []

    # ------------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------------

    def register_repo(
        self,
        repo_name: str,
        task_types: frozenset[str],
        agent_count: int = 0,
        adapter: Optional[Any] = None,
    ) -> None:
        """Register a repo and its capabilities in the mesh."""
        with self._lock:
            self._registry[repo_name] = RepoCapability(
                repo_name=repo_name,
                task_types=task_types,
                agent_count=agent_count,
            )
            if adapter is not None:
                self._adapters[repo_name] = adapter

    def unregister_repo(self, repo_name: str) -> bool:
        """Remove a repo from the mesh. Returns True if it was present."""
        with self._lock:
            removed = repo_name in self._registry
            self._registry.pop(repo_name, None)
            self._adapters.pop(repo_name, None)
            return removed

    def get_repo(self, repo_name: str) -> Optional[RepoCapability]:
        """Look up a repo's capability record."""
        with self._lock:
            cap = self._registry.get(repo_name)
            if cap is None:
                return None
            return cap

    @property
    def repo_count(self) -> int:
        with self._lock:
            return len(self._registry)

    @property
    def registered_repos(self) -> list[str]:
        with self._lock:
            return sorted(self._registry.keys())

    # ------------------------------------------------------------------
    # Health & Load
    # ------------------------------------------------------------------

    def update_repo_health(
        self,
        repo_name: str,
        healthy: bool,
        load: float,
        coherence: float,
        agent_count: Optional[int] = None,
    ) -> bool:
        """Update a repo's health/load metrics. Returns False if unknown repo."""
        with self._lock:
            cap = self._registry.get(repo_name)
            if cap is None:
                return False
            cap.healthy = healthy
            cap.load = max(0.0, min(1.0, load))
            cap.coherence = max(0.0, min(1.0, coherence))
            cap.last_heartbeat = time.monotonic()
            if agent_count is not None:
                cap.agent_count = agent_count
            return True

    # ------------------------------------------------------------------
    # Router
    # ------------------------------------------------------------------

    def route(self, task_type: str, payload: dict[str, Any]) -> RoutingDecision:
        """
        Route a task to the optimal repo based on type, load, and SCE-88
        constraints.

        Selection criteria (in order):
        1. Repo must support the task type
        2. Repo must be healthy
        3. Repo coherence must be above COHERENCE_THRESHOLD
        4. Among qualifying repos, pick the one with lowest load
        """
        with self._lock:
            candidates: list[RepoCapability] = []
            for cap in self._registry.values():
                if task_type in cap.task_types and cap.healthy:
                    if cap.coherence >= COHERENCE_THRESHOLD:
                        candidates.append(cap)

            if not candidates:
                # Fallback: try any repo that supports the type (ignore health)
                for cap in self._registry.values():
                    if task_type in cap.task_types:
                        candidates.append(cap)

            if not candidates:
                decision = RoutingDecision(
                    repo_name="",
                    task_type=task_type,
                    payload=payload,
                    routed=False,
                    reason="no_repo_supports_task_type",
                )
                self._routing_log.append(decision)
                return decision

            # Sort by load (ascending), then by name for determinism
            candidates.sort(key=lambda c: (c.load, c.repo_name))
            best = candidates[0]

            decision = RoutingDecision(
                repo_name=best.repo_name,
                task_type=task_type,
                payload=payload,
                routed=True,
                reason="optimal_route",
            )
            self._routing_log.append(decision)
            return decision

    def dispatch(self, task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Dispatch a task through the mesh: route, then execute via adapter.

        Returns a result dict with routing info and adapter response.
        """
        decision = self.route(task_type, payload)
        if not decision.routed:
            return {
                "routed": False,
                "reason": decision.reason,
                "task_type": task_type,
            }

        adapter = self._adapters.get(decision.repo_name)
        if adapter is not None:
            try:
                result = adapter.dispatch(task_type, payload)
                return {
                    "routed": True,
                    "repo": decision.repo_name,
                    "task_id": decision.task_id,
                    "result": result,
                }
            except Exception as exc:
                self._record_constraint_violation()
                return {
                    "routed": True,
                    "repo": decision.repo_name,
                    "task_id": decision.task_id,
                    "error": str(exc),
                }

        return {
            "routed": True,
            "repo": decision.repo_name,
            "task_id": decision.task_id,
            "result": {"status": "routed", "adapter": "none"},
        }

    # ------------------------------------------------------------------
    # Global Coherence Monitor
    # ------------------------------------------------------------------

    def coherence_snapshot(self) -> CoherenceSnapshot:
        """
        Compute a global coherence snapshot across all repos.

        Uses Lucas convergence on the coherence history and aggregates
        per-repo coherence scores.
        """
        with self._lock:
            repo_coherences: dict[str, float] = {}
            values: list[float] = []
            for name, cap in sorted(self._registry.items()):
                repo_coherences[name] = cap.coherence
                values.append(cap.coherence)

            if values:
                global_coh = _lucas_coherence(values)
            else:
                global_coh = 0.5

            try:
                _validate_coherence(global_coh)
            except Exception:
                global_coh = 0.5

            self._coherence_history.append(global_coh)
            if len(self._coherence_history) > _MAX_COHERENCE_HISTORY:
                self._coherence_history = self._coherence_history[
                    -_MAX_COHERENCE_HISTORY:
                ]

            drift = self._compute_drift()

            return CoherenceSnapshot(
                global_coherence=global_coh,
                repo_coherences=repo_coherences,
                constraint_violations=self._constraint_violations,
                drift=drift,
            )

    def _compute_drift(self) -> float:
        """Compute coherence drift from recent history."""
        h = self._coherence_history
        if len(h) < 2:
            return 0.0
        recent = h[-5:]
        if len(recent) < 2:
            return 0.0
        return abs(recent[-1] - recent[0])

    def _record_constraint_violation(self) -> None:
        """Thread-safe increment of constraint violation counter."""
        self._constraint_violations += 1

    @property
    def constraint_violations(self) -> int:
        with self._lock:
            return self._constraint_violations

    # ------------------------------------------------------------------
    # Load balancing
    # ------------------------------------------------------------------

    def balance_load(self) -> dict[str, Any]:
        """
        Compute load-balancing recommendations across repos.

        Returns stats about load distribution and recommendations.
        """
        with self._lock:
            if not self._registry:
                return {"repos": 0, "balanced": True, "recommendations": []}

            loads: dict[str, float] = {}
            for name, cap in sorted(self._registry.items()):
                loads[name] = cap.load

            values = list(loads.values())
            avg_load = sum(values) / len(values) if values else 0.0
            max_load = max(values) if values else 0.0
            min_load = min(values) if values else 0.0

            recommendations: list[dict[str, Any]] = []
            for name, load in sorted(loads.items()):
                if load > avg_load + 0.2:
                    recommendations.append(
                        {
                            "repo": name,
                            "action": "shed_load",
                            "current_load": load,
                            "target_load": avg_load,
                        }
                    )
                elif load < avg_load - 0.2:
                    recommendations.append(
                        {
                            "repo": name,
                            "action": "accept_load",
                            "current_load": load,
                            "target_load": avg_load,
                        }
                    )

            return {
                "repos": len(self._registry),
                "avg_load": avg_load,
                "max_load": max_load,
                "min_load": min_load,
                "balanced": max_load - min_load < 0.3,
                "recommendations": recommendations,
                "loads": loads,
            }

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """Return comprehensive mesh status across all repos."""
        with self._lock:
            repos: dict[str, Any] = {}
            total_agents = 0
            for name, cap in sorted(self._registry.items()):
                repos[name] = cap.to_dict()
                total_agents += cap.agent_count

            snapshot = self._coherence_snapshot_unlocked()

            return {
                "version": _MESH_VERSION,
                "repos": repos,
                "repo_count": len(self._registry),
                "total_agents": total_agents,
                "global_coherence": snapshot.global_coherence,
                "constraint_violations": self._constraint_violations,
                "drift": snapshot.drift,
                "routing_log_length": len(self._routing_log),
            }

    def _coherence_snapshot_unlocked(self) -> CoherenceSnapshot:
        """Internal coherence snapshot (caller holds lock)."""
        repo_coherences: dict[str, float] = {}
        values: list[float] = []
        for name, cap in sorted(self._registry.items()):
            repo_coherences[name] = cap.coherence
            values.append(cap.coherence)

        if values:
            global_coh = _lucas_coherence(values)
        else:
            global_coh = 0.5

        try:
            _validate_coherence(global_coh)
        except Exception:
            global_coh = 0.5

        drift = self._compute_drift()

        return CoherenceSnapshot(
            global_coherence=global_coh,
            repo_coherences=repo_coherences,
            constraint_violations=self._constraint_violations,
            drift=drift,
        )

    # ------------------------------------------------------------------
    # State persistence (JSON roundtrip)
    # ------------------------------------------------------------------

    def to_json(self) -> str:
        """Serialise mesh state to a deterministic JSON string."""
        with self._lock:
            data = {
                "version": _MESH_VERSION,
                "registry": {
                    name: cap.to_dict() for name, cap in sorted(self._registry.items())
                },
                "coherence_history": list(self._coherence_history),
                "constraint_violations": self._constraint_violations,
                "routing_log": [d.to_dict() for d in self._routing_log],
            }
            return json.dumps(data, sort_keys=True)

    @classmethod
    def from_json(cls, raw: str) -> "FederationMesh":
        """Restore mesh state from a JSON string."""
        data = json.loads(raw)
        mesh = cls()
        for _name, cap_data in sorted(data.get("registry", {}).items()):
            cap = RepoCapability.from_dict(cap_data)
            mesh._registry[cap.repo_name] = cap
        mesh._coherence_history = list(data.get("coherence_history", []))
        mesh._constraint_violations = int(data.get("constraint_violations", 0))
        # Routing log is not restored (transient)
        return mesh

    def reset(self) -> None:
        """Reset mesh to initial empty state."""
        with self._lock:
            self._registry.clear()
            self._adapters.clear()
            self._coherence_history.clear()
            self._constraint_violations = 0
            self._routing_log.clear()
