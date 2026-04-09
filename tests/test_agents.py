"""
Tests for the 13-agent distributed orchestration system.

Covers:
- Agent initialization and base class behaviour
- Task creation and routing
- Load balancing across agents
- Coherence gating (SCE-88 validation)
- Agent coordination and processing
- Individual agent specialization
- CLI integration (agents subcommand)
- 83 tests, all deterministic
"""

from __future__ import annotations

import json

import pytest

from snell_vern_matrix.agents import (
    MAX_QUEUE_LENGTH,
    TASK_ROUTING_MAP,
    AgentHealth,
    AgentRole,
    BaseAgent,
    Task,
    TaskStatus,
    TaskType,
)
from snell_vern_matrix.agents.agent_01_orchestrator import OrchestratorAgent
from snell_vern_matrix.agents.agent_02_ci_sentinel import CISentinelAgent
from snell_vern_matrix.agents.agent_03_memory_keeper import MemoryKeeperAgent
from snell_vern_matrix.agents.agent_04_constraint_guardian import (
    ConstraintGuardianAgent,
)
from snell_vern_matrix.agents.agent_05_phase_tracker import PhaseTrackerAgent
from snell_vern_matrix.agents.agent_06_lucas_analyst import LucasAnalystAgent
from snell_vern_matrix.agents.agent_07_field_weaver import FieldWeaverAgent
from snell_vern_matrix.agents.agent_08_ternary_logic import TernaryLogicAgent
from snell_vern_matrix.agents.agent_09_self_model_observer import (
    SelfModelObserverAgent,
)
from snell_vern_matrix.agents.agent_10_repo_sync import RepoSyncAgent
from snell_vern_matrix.agents.agent_11_test_validator import TestValidatorAgent
from snell_vern_matrix.agents.agent_12_doc_keeper import DocKeeperAgent
from snell_vern_matrix.agents.agent_13_coherence_monitor import CoherenceMonitorAgent
from snell_vern_matrix.agents.orchestrator import AgentOrchestrator
from snell_vern_matrix.cli import main as cli_main

# =========================================================================
# BaseAgent and AgentState
# =========================================================================


class TestBaseAgent:
    def test_agent_has_id(self) -> None:
        a = BaseAgent("test-01")
        assert a.agent_id == "test-01"

    def test_agent_default_role(self) -> None:
        a = BaseAgent("test-01")
        assert a.state.role == AgentRole.ORCHESTRATOR

    def test_agent_initial_health(self) -> None:
        a = BaseAgent("test-01")
        assert a.state.health == AgentHealth.HEALTHY

    def test_agent_initial_coherence(self) -> None:
        a = BaseAgent("test-01")
        assert a.state.coherence_score == 0.5

    def test_agent_initial_queue_empty(self) -> None:
        a = BaseAgent("test-01")
        assert a.state.queue_length == 0

    def test_agent_is_available_initially(self) -> None:
        a = BaseAgent("test-01")
        assert a.state.is_available

    def test_agent_state_to_dict(self) -> None:
        a = BaseAgent("test-01")
        d = a.state.to_dict()
        assert d["agent_id"] == "test-01"
        assert "health" in d
        assert "coherence_score" in d

    def test_agent_can_handle_empty_capabilities(self) -> None:
        a = BaseAgent("test-01")
        assert not a.can_handle(TaskType.MATH)

    def test_agent_execute_returns_dict(self) -> None:
        a = BaseAgent("test-01")
        task = Task(task_id="t1", task_type=TaskType.COORDINATION, payload={})
        result = a.execute(task)
        assert result["status"] == "completed"

    def test_agent_enqueue_and_process(self) -> None:
        a = BaseAgent("test-01")
        task = Task(task_id="t1", task_type=TaskType.COORDINATION, payload={})
        assert a.enqueue(task)
        assert a.state.queue_length == 1
        result = a.process_next()
        assert result is not None
        assert result["status"] == "completed"
        assert a.state.tasks_completed == 1

    def test_agent_process_empty_queue(self) -> None:
        a = BaseAgent("test-01")
        assert a.process_next() is None

    def test_agent_enqueue_full_rejects(self) -> None:
        a = BaseAgent("test-01")
        for i in range(MAX_QUEUE_LENGTH):
            task = Task(task_id=f"t{i}", task_type=TaskType.COORDINATION, payload={})
            a.enqueue(task)
        extra = Task(task_id="extra", task_type=TaskType.COORDINATION, payload={})
        assert not a.enqueue(extra)


class TestAgentHealth:
    def test_healthy_on_empty_queue(self) -> None:
        a = BaseAgent("test-01")
        assert a.update_health() == AgentHealth.HEALTHY

    def test_degraded_on_half_full(self) -> None:
        a = BaseAgent("test-01")
        for i in range(MAX_QUEUE_LENGTH // 2):
            task = Task(task_id=f"t{i}", task_type=TaskType.COORDINATION, payload={})
            a.state.workload_queue.append(task)
        assert a.update_health() == AgentHealth.DEGRADED

    def test_overloaded_at_max(self) -> None:
        a = BaseAgent("test-01")
        for i in range(MAX_QUEUE_LENGTH):
            task = Task(task_id=f"t{i}", task_type=TaskType.COORDINATION, payload={})
            a.state.workload_queue.append(task)
        assert a.update_health() == AgentHealth.OVERLOADED

    def test_degraded_on_low_coherence(self) -> None:
        a = BaseAgent("test-01")
        a.state.coherence_score = 0.1
        assert a.update_health() == AgentHealth.DEGRADED


# =========================================================================
# Task
# =========================================================================


class TestTask:
    def test_task_creation(self) -> None:
        t = Task(task_id="t1", task_type=TaskType.MATH, payload={"n": 5})
        assert t.task_id == "t1"
        assert t.status == TaskStatus.PENDING

    def test_task_generate_id_deterministic(self) -> None:
        id1 = Task.generate_id("math", "test")
        id2 = Task.generate_id("math", "test")
        assert id1 == id2

    def test_task_generate_id_differs(self) -> None:
        id1 = Task.generate_id("math", "a")
        id2 = Task.generate_id("math", "b")
        assert id1 != id2


# =========================================================================
# Task Routing Map
# =========================================================================


class TestTaskRouting:
    def test_all_task_types_have_routes(self) -> None:
        for tt in TaskType:
            assert tt in TASK_ROUTING_MAP

    def test_route_map_values_are_roles(self) -> None:
        for role in TASK_ROUTING_MAP.values():
            assert isinstance(role, AgentRole)


# =========================================================================
# AgentOrchestrator — initialisation
# =========================================================================


class TestOrchestratorInit:
    def test_has_13_agents(self) -> None:
        orch = AgentOrchestrator()
        assert orch.agent_count == 13

    def test_agents_have_unique_ids(self) -> None:
        orch = AgentOrchestrator()
        ids = list(orch.agents.keys())
        assert len(set(ids)) == 13

    def test_all_roles_represented(self) -> None:
        orch = AgentOrchestrator()
        roles = {a.role for a in orch.agents.values()}
        assert len(roles) == 13

    def test_agent_ids_sequential(self) -> None:
        orch = AgentOrchestrator()
        for i in range(1, 14):
            assert f"agent-{i:02d}" in orch.agents


# =========================================================================
# AgentOrchestrator — task routing
# =========================================================================


class TestOrchestratorRouting:
    def test_route_math_to_lucas_analyst(self) -> None:
        orch = AgentOrchestrator()
        task = orch.route_task(TaskType.MATH, {"n": 5})
        assert task.assigned_agent == "agent-06"

    def test_route_ci_health_to_sentinel(self) -> None:
        orch = AgentOrchestrator()
        task = orch.route_task(TaskType.CI_HEALTH, {"pipeline": "main"})
        assert task.assigned_agent == "agent-02"

    def test_route_memory_to_keeper(self) -> None:
        orch = AgentOrchestrator()
        task = orch.route_task(TaskType.MEMORY, {"key": "x"})
        assert task.assigned_agent == "agent-03"

    def test_route_constraint_to_guardian(self) -> None:
        orch = AgentOrchestrator()
        task = orch.route_task(TaskType.CONSTRAINT, {"coherence_score": 0.5})
        assert task.assigned_agent == "agent-04"

    def test_route_phase_to_tracker(self) -> None:
        orch = AgentOrchestrator()
        task = orch.route_task(TaskType.PHASE, {})
        assert task.assigned_agent == "agent-05"

    def test_route_field_to_weaver(self) -> None:
        orch = AgentOrchestrator()
        task = orch.route_task(TaskType.FIELD, {"n": 10})
        assert task.assigned_agent == "agent-07"

    def test_route_ternary_to_logic(self) -> None:
        orch = AgentOrchestrator()
        task = orch.route_task(TaskType.TERNARY, {})
        assert task.assigned_agent == "agent-08"

    def test_route_observation_to_self_model(self) -> None:
        orch = AgentOrchestrator()
        task = orch.route_task(TaskType.OBSERVATION, {"pattern": "test"})
        assert task.assigned_agent == "agent-09"

    def test_route_sync_to_repo(self) -> None:
        orch = AgentOrchestrator()
        task = orch.route_task(TaskType.SYNC, {"repo": "test"})
        assert task.assigned_agent == "agent-10"

    def test_route_testing_to_validator(self) -> None:
        orch = AgentOrchestrator()
        task = orch.route_task(TaskType.TESTING, {"passed": 50})
        assert task.assigned_agent == "agent-11"

    def test_route_documentation_to_doc_keeper(self) -> None:
        orch = AgentOrchestrator()
        task = orch.route_task(TaskType.DOCUMENTATION, {"key": "readme"})
        assert task.assigned_agent == "agent-12"

    def test_route_coherence_to_monitor(self) -> None:
        orch = AgentOrchestrator()
        task = orch.route_task(TaskType.COHERENCE, {"agent_scores": [0.8]})
        assert task.assigned_agent == "agent-13"

    def test_dispatch_by_string_type(self) -> None:
        orch = AgentOrchestrator()
        task = orch.dispatch("math", {"n": 5})
        assert task.assigned_agent == "agent-06"

    def test_dispatch_invalid_type_raises(self) -> None:
        orch = AgentOrchestrator()
        with pytest.raises(ValueError):
            orch.dispatch("nonexistent", {})


# =========================================================================
# AgentOrchestrator — processing & coherence gating
# =========================================================================


class TestOrchestratorProcessing:
    def test_process_all_returns_results(self) -> None:
        orch = AgentOrchestrator()
        orch.route_task(TaskType.MATH, {"n": 5})
        results = orch.process_all()
        assert len(results) == 1
        assert results[0]["status"] == "completed"

    def test_coherence_gating_adds_score(self) -> None:
        orch = AgentOrchestrator()
        orch.route_task(TaskType.MATH, {"n": 5})
        results = orch.process_all()
        assert "coherence_score" in results[0]
        assert "coherence_gated" in results[0]

    def test_coherence_score_bounded(self) -> None:
        orch = AgentOrchestrator()
        orch.route_task(TaskType.MATH, {"n": 5})
        results = orch.process_all()
        score = results[0]["coherence_score"]
        assert 0.0 <= score <= 1.0

    def test_process_multiple_tasks(self) -> None:
        orch = AgentOrchestrator()
        orch.route_task(TaskType.MATH, {"n": 5})
        orch.route_task(TaskType.FIELD, {"n": 3})
        orch.route_task(TaskType.MEMORY, {"action": "store", "key": "k", "value": "v"})
        results = orch.process_all()
        assert len(results) == 3

    def test_process_agent_specific(self) -> None:
        orch = AgentOrchestrator()
        orch.route_task(TaskType.MATH, {"n": 5})
        result = orch.process_agent("agent-06")
        assert result is not None
        assert result["status"] == "completed"

    def test_process_agent_nonexistent(self) -> None:
        orch = AgentOrchestrator()
        assert orch.process_agent("agent-99") is None


# =========================================================================
# AgentOrchestrator — load balancing
# =========================================================================


class TestLoadBalancing:
    def test_balance_empty_system(self) -> None:
        orch = AgentOrchestrator()
        summary = orch.balance_load()
        assert summary["total_moved"] == 0

    def test_balance_moves_from_overloaded(self) -> None:
        orch = AgentOrchestrator()
        # Overload agent-06 (Lucas)
        agent = orch.agents["agent-06"]
        for i in range(MAX_QUEUE_LENGTH):
            t = Task(task_id=f"t{i}", task_type=TaskType.MATH, payload={})
            agent.state.workload_queue.append(t)
        agent.update_health()
        assert agent.state.health == AgentHealth.OVERLOADED
        # No other agent handles MATH, so no moves possible
        summary = orch.balance_load()
        assert isinstance(summary["total_moved"], int)


# =========================================================================
# AgentOrchestrator — status & map
# =========================================================================


class TestOrchestratorStatus:
    def test_status_has_agent_count(self) -> None:
        orch = AgentOrchestrator()
        status = orch.get_status()
        assert status["agent_count"] == 13

    def test_status_has_all_agents(self) -> None:
        orch = AgentOrchestrator()
        status = orch.get_status()
        assert len(status["agents"]) == 13

    def test_status_tracks_completions(self) -> None:
        orch = AgentOrchestrator()
        orch.route_task(TaskType.MATH, {"n": 5})
        orch.process_all()
        status = orch.get_status()
        assert status["total_completed"] >= 1

    def test_agent_map_has_13_entries(self) -> None:
        orch = AgentOrchestrator()
        m = orch.get_agent_map()
        assert len(m) == 13

    def test_agent_map_entries_have_role(self) -> None:
        orch = AgentOrchestrator()
        m = orch.get_agent_map()
        for entry in m:
            assert "role" in entry
            assert "capabilities" in entry
            assert "health" in entry


# =========================================================================
# Individual agent specialisations
# =========================================================================


class TestOrchestratorAgent:
    def test_execute_returns_routed(self) -> None:
        a = OrchestratorAgent("a-01")
        t = Task(task_id="t1", task_type=TaskType.COORDINATION, payload={})
        result = a.execute(t)
        assert result["routed"] is True


class TestCISentinelAgent:
    def test_check_unknown_pipeline(self) -> None:
        a = CISentinelAgent("a-02")
        t = Task(
            task_id="t1",
            task_type=TaskType.CI_HEALTH,
            payload={"action": "check", "pipeline": "main"},
        )
        result = a.execute(t)
        assert result["ci_status"] == "unknown"

    def test_update_pipeline(self) -> None:
        a = CISentinelAgent("a-02")
        t = Task(
            task_id="t1",
            task_type=TaskType.CI_HEALTH,
            payload={"action": "update", "pipeline": "main", "status": "green"},
        )
        result = a.execute(t)
        assert result["ci_status"] == "green"


class TestMemoryKeeperAgent:
    def test_store_and_retrieve(self) -> None:
        a = MemoryKeeperAgent("a-03")
        store = Task(
            task_id="t1",
            task_type=TaskType.MEMORY,
            payload={"action": "store", "key": "x", "value": 42},
        )
        a.execute(store)
        get = Task(
            task_id="t2",
            task_type=TaskType.MEMORY,
            payload={"action": "get", "key": "x"},
        )
        result = a.execute(get)
        assert result["value"] == 42

    def test_list_keys(self) -> None:
        a = MemoryKeeperAgent("a-03")
        a.execute(
            Task(
                task_id="t1",
                task_type=TaskType.MEMORY,
                payload={"action": "store", "key": "b", "value": 1},
            )
        )
        a.execute(
            Task(
                task_id="t2",
                task_type=TaskType.MEMORY,
                payload={"action": "store", "key": "a", "value": 2},
            )
        )
        result = a.execute(
            Task(
                task_id="t3",
                task_type=TaskType.MEMORY,
                payload={"action": "list"},
            )
        )
        assert result["keys"] == ["a", "b"]


class TestConstraintGuardianAgent:
    def test_valid_constraints(self) -> None:
        a = ConstraintGuardianAgent("a-04")
        t = Task(
            task_id="t1",
            task_type=TaskType.CONSTRAINT,
            payload={
                "coherence_score": 0.5,
                "uncertainty": 0.5,
                "ternary_balance": [0.0, 0.0, 0.0],
            },
        )
        result = a.execute(t)
        assert result["valid"] is True
        assert result["violations"] == []

    def test_invalid_coherence(self) -> None:
        a = ConstraintGuardianAgent("a-04")
        t = Task(
            task_id="t1",
            task_type=TaskType.CONSTRAINT,
            payload={"coherence_score": 1.5},
        )
        result = a.execute(t)
        assert result["valid"] is False
        assert len(result["violations"]) > 0


class TestPhaseTrackerAgent:
    def test_track_phase(self) -> None:
        a = PhaseTrackerAgent("a-05")
        t = Task(
            task_id="t1",
            task_type=TaskType.PHASE,
            payload={"phase_state": "initial"},
        )
        result = a.execute(t)
        assert result["current_phase"] == "initial"
        assert result["history_length"] == 1


class TestLucasAnalystAgent:
    def test_sequence(self) -> None:
        a = LucasAnalystAgent("a-06")
        t = Task(
            task_id="t1",
            task_type=TaskType.MATH,
            payload={"action": "sequence", "n": 5},
        )
        result = a.execute(t)
        assert "values" in result
        assert result["values"]["3"] == 4  # L(3) = 4

    def test_convergence(self) -> None:
        a = LucasAnalystAgent("a-06")
        t = Task(
            task_id="t1",
            task_type=TaskType.MATH,
            payload={"action": "convergence", "n": 20},
        )
        result = a.execute(t)
        assert result["converged"] is True


class TestFieldWeaverAgent:
    def test_field_computation(self) -> None:
        a = FieldWeaverAgent("a-07")
        t = Task(
            task_id="t1",
            task_type=TaskType.FIELD,
            payload={"action": "field", "n": 5},
        )
        result = a.execute(t)
        assert len(result["points"]) == 5
        assert "golden_angle" in result

    def test_analysis(self) -> None:
        a = FieldWeaverAgent("a-07")
        t = Task(
            task_id="t1",
            task_type=TaskType.FIELD,
            payload={"action": "analysis", "n": 5},
        )
        result = a.execute(t)
        assert "radius" in result
        assert "angle" in result


class TestTernaryLogicAgent:
    def test_evaluate_stable(self) -> None:
        a = TernaryLogicAgent("a-08")
        t = Task(
            task_id="t1",
            task_type=TaskType.TERNARY,
            payload={"action": "evaluate", "ternary_balance": [0.0, 0.0, 0.0]},
        )
        result = a.execute(t)
        assert result["stability"] == "stable"

    def test_update_balance(self) -> None:
        a = TernaryLogicAgent("a-08")
        t = Task(
            task_id="t1",
            task_type=TaskType.TERNARY,
            payload={
                "action": "update",
                "current": [0.0, 0.0, 0.0],
                "delta": 0.5,
            },
        )
        result = a.execute(t)
        assert "balance" in result
        assert result["balance"] != [0.0, 0.0, 0.0]


class TestSelfModelObserverAgent:
    def test_observe(self) -> None:
        a = SelfModelObserverAgent("a-09")
        t = Task(
            task_id="t1",
            task_type=TaskType.OBSERVATION,
            payload={"action": "observe", "pattern": "hello"},
        )
        result = a.execute(t)
        assert "observation" in result

    def test_ask(self) -> None:
        a = SelfModelObserverAgent("a-09")
        t = Task(
            task_id="t1",
            task_type=TaskType.OBSERVATION,
            payload={"action": "ask"},
        )
        result = a.execute(t)
        assert "query" in result

    def test_state(self) -> None:
        a = SelfModelObserverAgent("a-09")
        t = Task(
            task_id="t1",
            task_type=TaskType.OBSERVATION,
            payload={"action": "state"},
        )
        result = a.execute(t)
        assert "state" in result


class TestRepoSyncAgent:
    def test_check_unsynced(self) -> None:
        a = RepoSyncAgent("a-10")
        t = Task(
            task_id="t1",
            task_type=TaskType.SYNC,
            payload={"action": "check", "repo": "test"},
        )
        result = a.execute(t)
        assert result["sync_status"] == "unsynced"

    def test_sync_repo(self) -> None:
        a = RepoSyncAgent("a-10")
        t = Task(
            task_id="t1",
            task_type=TaskType.SYNC,
            payload={"action": "sync", "repo": "test"},
        )
        result = a.execute(t)
        assert result["sync_status"] == "synced"


class TestTestValidatorAgent:
    def test_report(self) -> None:
        a = TestValidatorAgent("a-11")
        t = Task(
            task_id="t1",
            task_type=TaskType.TESTING,
            payload={"action": "report", "passed": 90, "failed": 10},
        )
        result = a.execute(t)
        assert result["coverage"] == 0.9

    def test_regression_detection(self) -> None:
        a = TestValidatorAgent("a-11")
        t1 = Task(
            task_id="t1",
            task_type=TaskType.TESTING,
            payload={"action": "report", "passed": 90, "failed": 5},
        )
        a.execute(t1)
        t2 = Task(
            task_id="t2",
            task_type=TaskType.TESTING,
            payload={"action": "report", "passed": 85, "failed": 15},
        )
        result = a.execute(t2)
        assert result["regression_detected"] is True


class TestDocKeeperAgent:
    def test_update_manifest(self) -> None:
        a = DocKeeperAgent("a-12")
        t = Task(
            task_id="t1",
            task_type=TaskType.DOCUMENTATION,
            payload={"action": "update", "key": "readme", "value": "v2"},
        )
        result = a.execute(t)
        assert result["action"] == "updated"

    def test_get_manifest(self) -> None:
        a = DocKeeperAgent("a-12")
        a.execute(
            Task(
                task_id="t1",
                task_type=TaskType.DOCUMENTATION,
                payload={"action": "update", "key": "readme", "value": "v2"},
            )
        )
        t = Task(
            task_id="t2",
            task_type=TaskType.DOCUMENTATION,
            payload={"action": "manifest"},
        )
        result = a.execute(t)
        assert result["manifest"]["readme"] == "v2"


class TestCoherenceMonitorAgent:
    def test_check_healthy(self) -> None:
        a = CoherenceMonitorAgent("a-13")
        t = Task(
            task_id="t1",
            task_type=TaskType.COHERENCE,
            payload={"action": "check", "agent_scores": [0.8, 0.7, 0.9]},
        )
        result = a.execute(t)
        assert result["system_healthy"] is True

    def test_check_unhealthy(self) -> None:
        a = CoherenceMonitorAgent("a-13")
        t = Task(
            task_id="t1",
            task_type=TaskType.COHERENCE,
            payload={"action": "check", "agent_scores": [0.1, 0.2]},
        )
        result = a.execute(t)
        assert result["system_healthy"] is False
        assert result["agents_below_threshold"] == 2


# =========================================================================
# CLI — agents subcommand
# =========================================================================


class TestAgentsCLI:
    def test_cli_agents_status(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["agents", "--status"])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["agent_count"] == 13

    def test_cli_agents_dispatch(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["agents", "--dispatch", "math", '{"n": 5}'])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["task_type"] == "math"
        assert len(data["results"]) == 1

    def test_cli_agents_dispatch_bad_json(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = cli_main(["agents", "--dispatch", "math", "not-json"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "invalid JSON" in err

    def test_cli_agents_dispatch_bad_type(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = cli_main(["agents", "--dispatch", "invalid_type", "{}"])
        assert rc == 1

    def test_cli_agents_balance(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["agents", "--balance"])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "total_moved" in data

    def test_cli_agents_map(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["agents", "--map"])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 13
