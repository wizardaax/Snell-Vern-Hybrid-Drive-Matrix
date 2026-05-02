"""
Tests for the cross-repo federation mesh.

Covers:
- FederationMesh registry, routing, coherence, load balancing, state persistence
- SnellVernAdapter and RFMProAdapter dispatch, status, recall, fallback
- CLI 'mesh' subcommand end-to-end
- 79 tests, all deterministic
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from snell_vern_matrix.cli import main as cli_main
from snell_vern_matrix.federation.adapters import (
    RFMProAdapter,
    SnellVernAdapter,
    create_default_mesh,
)
from snell_vern_matrix.federation.mesh import (
    CoherenceSnapshot,
    FederationMesh,
    RepoCapability,
    RoutingDecision,
)

# =========================================================================
# RepoCapability
# =========================================================================


class TestRepoCapability:
    def test_init_defaults(self) -> None:
        cap = RepoCapability("test-repo", frozenset({"math", "phase"}), 5)
        assert cap.repo_name == "test-repo"
        assert cap.agent_count == 5
        assert cap.healthy is True
        assert cap.load == 0.0
        assert cap.coherence == 0.5

    def test_to_dict(self) -> None:
        cap = RepoCapability("r", frozenset({"a"}), 2)
        d = cap.to_dict()
        assert d["repo_name"] == "r"
        assert d["task_types"] == ["a"]
        assert d["agent_count"] == 2

    def test_from_dict_roundtrip(self) -> None:
        cap = RepoCapability("r", frozenset({"x", "y"}), 3)
        cap.load = 0.7
        cap.coherence = 0.9
        d = cap.to_dict()
        restored = RepoCapability.from_dict(d)
        assert restored.repo_name == "r"
        assert restored.task_types == frozenset({"x", "y"})
        assert restored.load == 0.7
        assert restored.coherence == 0.9


# =========================================================================
# RoutingDecision
# =========================================================================


class TestRoutingDecision:
    def test_deterministic_task_id(self) -> None:
        d1 = RoutingDecision("repo", "math", {"n": 1}, True, "ok")
        d2 = RoutingDecision("repo", "math", {"n": 1}, True, "ok")
        assert d1.task_id == d2.task_id

    def test_different_payload_different_id(self) -> None:
        d1 = RoutingDecision("repo", "math", {"n": 1}, True, "ok")
        d2 = RoutingDecision("repo", "math", {"n": 2}, True, "ok")
        assert d1.task_id != d2.task_id

    def test_to_dict(self) -> None:
        d = RoutingDecision("repo", "math", {}, True, "ok")
        out = d.to_dict()
        assert out["repo_name"] == "repo"
        assert out["routed"] is True


# =========================================================================
# CoherenceSnapshot
# =========================================================================


class TestCoherenceSnapshot:
    def test_to_dict(self) -> None:
        s = CoherenceSnapshot(0.8, {"a": 0.9}, 0, 0.01)
        d = s.to_dict()
        assert d["global_coherence"] == 0.8
        assert d["repo_coherences"] == {"a": 0.9}
        assert d["constraint_violations"] == 0
        assert d["drift"] == 0.01


# =========================================================================
# FederationMesh — Registry
# =========================================================================


class TestMeshRegistry:
    def test_register_and_count(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset({"math"}), 5)
        assert mesh.repo_count == 1
        assert mesh.registered_repos == ["a"]

    def test_register_multiple(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset({"math"}))
        mesh.register_repo("b", frozenset({"phase"}))
        assert mesh.repo_count == 2

    def test_get_repo(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("r", frozenset({"math"}), 7)
        cap = mesh.get_repo("r")
        assert cap is not None
        assert cap.agent_count == 7

    def test_get_unknown_repo(self) -> None:
        mesh = FederationMesh()
        assert mesh.get_repo("missing") is None

    def test_unregister(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("r", frozenset({"math"}))
        assert mesh.unregister_repo("r") is True
        assert mesh.repo_count == 0

    def test_unregister_missing(self) -> None:
        mesh = FederationMesh()
        assert mesh.unregister_repo("x") is False


# =========================================================================
# FederationMesh — Health & Load
# =========================================================================


class TestMeshHealth:
    def test_update_health(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("r", frozenset({"math"}))
        ok = mesh.update_repo_health("r", True, 0.5, 0.8)
        assert ok is True
        cap = mesh.get_repo("r")
        assert cap is not None
        assert cap.load == 0.5
        assert cap.coherence == 0.8

    def test_update_unknown_repo(self) -> None:
        mesh = FederationMesh()
        assert mesh.update_repo_health("x", True, 0.0, 0.5) is False

    def test_load_clamped(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("r", frozenset({"math"}))
        mesh.update_repo_health("r", True, 2.0, -0.5)
        cap = mesh.get_repo("r")
        assert cap is not None
        assert cap.load == 1.0
        assert cap.coherence == 0.0


# =========================================================================
# FederationMesh — Routing
# =========================================================================


class TestMeshRouting:
    def test_route_to_only_repo(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset({"math"}))
        decision = mesh.route("math", {})
        assert decision.routed is True
        assert decision.repo_name == "a"

    def test_route_no_match(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset({"math"}))
        decision = mesh.route("phase", {})
        assert decision.routed is False

    def test_route_prefers_lower_load(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset({"math"}))
        mesh.register_repo("b", frozenset({"math"}))
        mesh.update_repo_health("a", True, 0.8, 0.9)
        mesh.update_repo_health("b", True, 0.2, 0.9)
        decision = mesh.route("math", {})
        assert decision.repo_name == "b"

    def test_route_skips_unhealthy_prefers_healthy(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset({"math"}))
        mesh.register_repo("b", frozenset({"math"}))
        mesh.update_repo_health("a", False, 0.0, 0.9)
        mesh.update_repo_health("b", True, 0.5, 0.9)
        decision = mesh.route("math", {})
        assert decision.repo_name == "b"

    def test_route_skips_low_coherence(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset({"math"}))
        mesh.register_repo("b", frozenset({"math"}))
        mesh.update_repo_health("a", True, 0.0, 0.1)  # below threshold
        mesh.update_repo_health("b", True, 0.5, 0.9)
        decision = mesh.route("math", {})
        assert decision.repo_name == "b"

    def test_route_fallback_when_all_unhealthy(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset({"math"}))
        mesh.update_repo_health("a", False, 0.0, 0.1)
        decision = mesh.route("math", {})
        # Fallback ignores health
        assert decision.routed is True
        assert decision.repo_name == "a"

    def test_route_deterministic_tiebreak(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("b-repo", frozenset({"math"}))
        mesh.register_repo("a-repo", frozenset({"math"}))
        decision = mesh.route("math", {})
        # Same load, alphabetical tiebreak
        assert decision.repo_name == "a-repo"


# =========================================================================
# FederationMesh — Dispatch
# =========================================================================


class TestMeshDispatch:
    def test_dispatch_no_adapter(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("r", frozenset({"math"}))
        result = mesh.dispatch("math", {})
        assert result["routed"] is True
        assert result["result"]["adapter"] == "none"

    def test_dispatch_no_match(self) -> None:
        mesh = FederationMesh()
        result = mesh.dispatch("unknown", {})
        assert result["routed"] is False

    def test_dispatch_with_adapter(self) -> None:
        mesh = FederationMesh()

        class FakeAdapter:
            def dispatch(
                self, task_type: str, payload: dict[str, Any]
            ) -> dict[str, Any]:
                return {"fake": True}

        mesh.register_repo("r", frozenset({"math"}), adapter=FakeAdapter())
        result = mesh.dispatch("math", {})
        assert result["routed"] is True
        assert result["result"]["fake"] is True

    def test_dispatch_adapter_error(self) -> None:
        mesh = FederationMesh()

        class BadAdapter:
            def dispatch(
                self, task_type: str, payload: dict[str, Any]
            ) -> dict[str, Any]:
                raise RuntimeError("boom")

        mesh.register_repo("r", frozenset({"math"}), adapter=BadAdapter())
        result = mesh.dispatch("math", {})
        assert "error" in result
        assert mesh.constraint_violations == 1


# =========================================================================
# FederationMesh — Coherence
# =========================================================================


class TestMeshCoherence:
    def test_coherence_empty_mesh(self) -> None:
        mesh = FederationMesh()
        snap = mesh.coherence_snapshot()
        assert snap.global_coherence == 0.5
        assert snap.constraint_violations == 0

    def test_coherence_with_repos(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset({"math"}))
        mesh.update_repo_health("a", True, 0.0, 0.9)
        snap = mesh.coherence_snapshot()
        assert 0.0 <= snap.global_coherence <= 1.0
        assert snap.repo_coherences["a"] == 0.9

    def test_coherence_drift_zero_initially(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset())
        snap = mesh.coherence_snapshot()
        assert snap.drift == 0.0

    def test_constraint_violations_counter(self) -> None:
        mesh = FederationMesh()
        assert mesh.constraint_violations == 0


# =========================================================================
# FederationMesh — Load Balancing
# =========================================================================


class TestMeshLoadBalance:
    def test_balance_empty(self) -> None:
        mesh = FederationMesh()
        result = mesh.balance_load()
        assert result["repos"] == 0
        assert result["balanced"] is True

    def test_balance_single_repo(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset({"math"}))
        result = mesh.balance_load()
        assert result["repos"] == 1
        assert result["balanced"] is True

    def test_balance_recommends_shed(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset({"math"}))
        mesh.register_repo("b", frozenset({"math"}))
        mesh.update_repo_health("a", True, 0.9, 0.5)
        mesh.update_repo_health("b", True, 0.1, 0.5)
        result = mesh.balance_load()
        assert not result["balanced"]
        actions = {r["action"] for r in result["recommendations"]}
        assert "shed_load" in actions
        assert "accept_load" in actions


# =========================================================================
# FederationMesh — State Persistence
# =========================================================================


class TestMeshPersistence:
    def test_json_roundtrip(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset({"math", "phase"}), 5)
        mesh.update_repo_health("a", True, 0.3, 0.7)
        raw = mesh.to_json()
        restored = FederationMesh.from_json(raw)
        assert restored.repo_count == 1
        cap = restored.get_repo("a")
        assert cap is not None
        assert cap.load == 0.3
        assert cap.coherence == 0.7
        assert cap.task_types == frozenset({"math", "phase"})

    def test_json_deterministic(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("b", frozenset({"x"}))
        mesh.register_repo("a", frozenset({"y"}))
        j1 = mesh.to_json()
        j2 = mesh.to_json()
        assert j1 == j2

    def test_json_valid(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("r", frozenset({"z"}))
        data = json.loads(mesh.to_json())
        assert "version" in data
        assert "registry" in data

    def test_reset(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset())
        mesh.reset()
        assert mesh.repo_count == 0


# =========================================================================
# FederationMesh — Status
# =========================================================================


class TestMeshStatus:
    def test_status_keys(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset(), 5)
        s = mesh.get_status()
        assert "version" in s
        assert "repos" in s
        assert s["total_agents"] == 5
        assert s["repo_count"] == 1

    def test_status_multiple_repos(self) -> None:
        mesh = FederationMesh()
        mesh.register_repo("a", frozenset(), 5)
        mesh.register_repo("b", frozenset(), 8)
        s = mesh.get_status()
        assert s["total_agents"] == 13
        assert s["repo_count"] == 2


# =========================================================================
# SnellVernAdapter
# =========================================================================


class TestSnellVernAdapter:
    def test_repo_name(self) -> None:
        adapter = SnellVernAdapter()
        assert adapter.repo_name == "snell-vern-hybrid-drive-matrix"

    def test_agent_count(self) -> None:
        adapter = SnellVernAdapter()
        assert adapter.agent_count == 13

    def test_supported_types(self) -> None:
        adapter = SnellVernAdapter()
        assert "math" in adapter.supported_task_types
        assert "phase" in adapter.supported_task_types

    def test_is_available(self) -> None:
        adapter = SnellVernAdapter()
        assert adapter.is_available() is True

    def test_dispatch_math(self) -> None:
        adapter = SnellVernAdapter()
        result = adapter.dispatch("math", {"n": 5})
        assert result["status"] == "completed"
        assert "task_id" in result

    def test_dispatch_phase(self) -> None:
        adapter = SnellVernAdapter()
        result = adapter.dispatch("phase", {"input": "test"})
        assert result["status"] == "completed"

    def test_dispatch_invalid_type(self) -> None:
        adapter = SnellVernAdapter()
        result = adapter.dispatch("nonexistent_type_xyz", {})
        assert result["status"] == "error"

    def test_recall(self) -> None:
        adapter = SnellVernAdapter()
        result = adapter.dispatch("math", {"n": 3})
        task_id = result.get("task_id", "")
        recalled = adapter.recall(task_id)
        assert recalled is not None

    def test_recall_missing(self) -> None:
        adapter = SnellVernAdapter()
        assert adapter.recall("nonexistent") is None

    def test_status(self) -> None:
        adapter = SnellVernAdapter()
        s = adapter.status()
        assert "agent_count" in s
        assert s["agent_count"] == 13

    def test_coherence_score(self) -> None:
        adapter = SnellVernAdapter()
        score = adapter.coherence_score()
        assert 0.0 <= score <= 1.0

    def test_current_load(self) -> None:
        adapter = SnellVernAdapter()
        load = adapter.current_load()
        assert 0.0 <= load <= 1.0

    def test_json_protocol_encode(self) -> None:
        adapter = SnellVernAdapter()
        msg = adapter.to_json_protocol("dispatch", task_type="math")
        parsed = json.loads(msg)
        assert parsed["action"] == "dispatch"
        assert parsed["repo"] == adapter.repo_name

    def test_json_protocol_decode(self) -> None:
        raw = json.dumps({"action": "status", "repo": "test"})
        parsed = SnellVernAdapter.parse_json_protocol(raw)
        assert parsed["action"] == "status"


# =========================================================================
# RFMProAdapter
# =========================================================================


class TestRFMProAdapter:
    def test_repo_name(self) -> None:
        adapter = RFMProAdapter()
        assert adapter.repo_name == "recursive-field-math-pro"

    def test_supported_types(self) -> None:
        adapter = RFMProAdapter()
        assert "math" in adapter.supported_task_types
        assert "field" in adapter.supported_task_types

    def test_is_available(self) -> None:
        adapter = RFMProAdapter()
        assert adapter.is_available() is True

    def test_dispatch_math(self) -> None:
        adapter = RFMProAdapter()
        result = adapter.dispatch("math", {"n": 10})
        assert result["status"] == "completed"
        assert "result" in result

    def test_dispatch_field(self) -> None:
        adapter = RFMProAdapter()
        result = adapter.dispatch("field", {"n": 5})
        assert result["status"] == "completed"

    def test_dispatch_coherence(self) -> None:
        adapter = RFMProAdapter()
        result = adapter.dispatch("coherence", {})
        assert result["status"] == "completed"
        assert "result" in result

    def test_dispatch_coherence_gated(self) -> None:
        adapter = RFMProAdapter()
        adapter.set_coherence(0.1)  # below threshold
        result = adapter.dispatch("math", {"n": 5})
        assert result["status"] == "coherence_gated"

    def test_dispatch_force_bypasses_gate(self) -> None:
        adapter = RFMProAdapter()
        adapter.set_coherence(0.1)
        result = adapter.dispatch("math", {"n": 5, "force": True})
        assert result["status"] == "completed"

    def test_recall(self) -> None:
        adapter = RFMProAdapter()
        result = adapter.dispatch("math", {"n": 7})
        tid = result.get("task_id", "")
        assert adapter.recall(tid) is not None

    def test_recall_missing(self) -> None:
        adapter = RFMProAdapter()
        assert adapter.recall("missing") is None

    def test_status(self) -> None:
        adapter = RFMProAdapter()
        s = adapter.status()
        assert s["repo"] == "recursive-field-math-pro"
        assert s["available"] is True

    def test_current_load(self) -> None:
        adapter = RFMProAdapter()
        assert adapter.current_load() == 0.0

    def test_set_coherence(self) -> None:
        adapter = RFMProAdapter()
        adapter.set_coherence(0.9)
        assert adapter.coherence_score() == 0.9

    def test_set_coherence_clamped(self) -> None:
        adapter = RFMProAdapter()
        adapter.set_coherence(5.0)
        assert adapter.coherence_score() == 1.0
        adapter.set_coherence(-1.0)
        assert adapter.coherence_score() == 0.0


# =========================================================================
# create_default_mesh
# =========================================================================


class TestCreateDefaultMesh:
    def test_creates_mesh_with_thirteen_repos(self) -> None:
        # 2 original (snell-vern, rfm-pro) + 1 phase (glyph) + 1 SCE-88
        # + 1 Codex-AEON + 5 doc/observation repos (recursive-field-math,
        # ziltrix-sch-core, wizardaax.github.io, rff-agent-logs, sim_outputs).
        # The 8 rfm-pro submodules (evolve/swarm/select/score/bridge/detect/
        # self_model/validate) are multiplexed inside RFMProAdapter, NOT
        # registered as separate repos.
        # PLUS 3 per-repo adapters added 2026-05-02 to close the federation
        # coverage gap: jarvis (voice butler daemon), memory-vault (append-only
        # snapshot store), xova (Tauri desktop agent). The ziltrix-sch-core
        # adapter overrides the pre-existing doc-style entry. Net: 10 + 3 = 13.
        mesh = create_default_mesh()
        assert mesh.repo_count == 13

    def test_repos_registered(self) -> None:
        mesh = create_default_mesh()
        names = mesh.registered_repos
        assert "snell-vern-hybrid-drive-matrix" in names
        assert "recursive-field-math-pro" in names

    def test_dispatch_phase_routes_to_snell_vern(self) -> None:
        mesh = create_default_mesh()
        result = mesh.dispatch("phase", {"input": "test"})
        assert result["routed"] is True

    def test_dispatch_math_routes(self) -> None:
        mesh = create_default_mesh()
        result = mesh.dispatch("math", {"n": 5})
        assert result["routed"] is True

    def test_status_includes_all_agents(self) -> None:
        # 13 from snell-vern-hybrid-drive-matrix + 13 from rfm-pro
        # (RFMProAdapter delegates agent_count to EvolutionEngineAdapter,
        # which represents the 13 federation agents in EvolutionEngine:
        # observer, planner, executor, validator, memory, router,
        # constraint_gate, integrator, evaluator, bridge, sentinel,
        # recovery, meta_learner).
        # PLUS the 4 per-repo adapters added 2026-05-02:
        #   - JarvisAdapter:        17 (Jarvis builtin tools)
        #   - MemoryVaultAdapter:    1
        #   - XovaAdapter:          41 (Tauri commands per agi_stack_architecture.md)
        #   - ZiltrixAdapter:        1 (overrides pre-existing doc adapter; baseline 1 agent)
        # = 26 + 17 + 1 + 41 + 1 = 86. (Doc adapters report agent_count 0,
        # so adding the Ziltrix adapter on top adds +1 net.)
        mesh = create_default_mesh()
        status = mesh.get_status()
        assert status["total_agents"] == 86


# =========================================================================
# CLI — mesh subcommand
# =========================================================================


class TestCLIMesh:
    def test_mesh_status(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["mesh", "--status"])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "repos" in data
        assert "version" in data

    def test_mesh_dispatch_math(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["mesh", "--dispatch", "math", '{"n": 5}'])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["routed"] is True

    def test_mesh_dispatch_phase(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["mesh", "--dispatch", "phase", '{"input": "abc"}'])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["routed"] is True

    def test_mesh_dispatch_bad_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["mesh", "--dispatch", "math", "not-json"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "invalid JSON" in err

    def test_mesh_balance(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["mesh", "--balance"])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "repos" in data

    def test_mesh_coherence(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["mesh", "--coherence"])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "global_coherence" in data
        assert "drift" in data
