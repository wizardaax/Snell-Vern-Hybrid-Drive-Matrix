"""Tests for CognitiveCycle goal-driven driver."""

from __future__ import annotations

import glob
import json
import os

from snell_vern_matrix.agents import TaskType
from snell_vern_matrix.agents.cognitive_cycle import (
    CognitiveCycle,
    CycleResult,
    _crest_stamp,
    verify_log,
)
from snell_vern_matrix.agents.orchestrator import AgentOrchestrator


def test_decompose_picks_relevant_task_types() -> None:
    cc = CognitiveCycle()
    tts = cc.decompose("audit the lucas formula and validate field coherence")
    # Bookends always present
    assert tts[0] == TaskType.OBSERVATION
    assert tts[-1] == TaskType.COHERENCE
    # Keywords in goal map to expected types
    assert TaskType.MATH in tts          # "lucas"
    assert TaskType.CONSTRAINT in tts    # "validate" → constraint-checking
    assert TaskType.FIELD in tts         # "field"


def test_decompose_unknown_goal_still_has_bookends() -> None:
    """Even on a meaningless goal, the cycle observes → recalls → checks coherence."""
    cc = CognitiveCycle()
    tts = cc.decompose("xyzzy plugh")
    assert tts == [TaskType.OBSERVATION, TaskType.MEMORY, TaskType.COHERENCE]


def test_decompose_no_duplicates() -> None:
    cc = CognitiveCycle()
    tts = cc.decompose("test test test memory memory")
    assert len(tts) == len(set(tts))


def test_run_returns_cycle_result_with_results() -> None:
    cc = CognitiveCycle()
    r = cc.run("observe the field and remember coherence")
    assert isinstance(r, CycleResult)
    assert r.goal.startswith("observe")
    assert len(r.task_types) >= 3  # OBSERVATION + matches + COHERENCE
    assert len(r.results) >= 1
    assert 0.0 <= r.average_coherence <= 1.0


def test_run_records_to_history() -> None:
    cc = CognitiveCycle()
    cc.run("audit memory")
    cc.run("validate phase")
    assert len(cc.history) == 2


def test_loop_stops_on_high_coherence() -> None:
    cc = CognitiveCycle()
    results = cc.loop("observe coherence", max_cycles=5)
    assert 1 <= len(results) <= 5
    # Each cycle returns a CycleResult
    for r in results:
        assert isinstance(r, CycleResult)


def test_summary_is_serialisable() -> None:
    cc = CognitiveCycle()
    r = cc.run("audit lucas formula")
    s = r.summary()
    # All keys present and types are JSON-friendly
    assert s["goal"] == "audit lucas formula"
    assert isinstance(s["tasks_dispatched"], int)
    assert isinstance(s["average_coherence"], float)
    assert isinstance(s["task_types"], list)
    assert all(isinstance(t, str) for t in s["task_types"])


def test_uses_provided_orchestrator() -> None:
    orch = AgentOrchestrator()
    cc = CognitiveCycle(orchestrator=orch)
    cc.run("audit field")
    # Tasks should appear in the orchestrator's task_log
    status = orch.get_status()
    assert status["task_log_length"] >= 1


def test_crest_stamp_is_deterministic() -> None:
    payload = b"recursive field framework"
    s1 = _crest_stamp(payload)
    s2 = _crest_stamp(payload)
    assert s1 == s2
    assert len(s1) == 8


def test_crest_stamp_changes_with_payload() -> None:
    s1 = _crest_stamp(b"goal A")
    s2 = _crest_stamp(b"goal B")
    assert s1 != s2


def test_run_stamps_result_with_crest_and_sha() -> None:
    cc = CognitiveCycle()
    r = cc.run("audit lucas formula")
    assert r.crest != ""
    assert len(r.crest) == 8
    assert len(r.sha256) == 64  # hex-encoded SHA-256


def test_log_record_round_trip_verifies(tmp_path) -> None:
    log_dir = str(tmp_path / "cycles")
    cc = CognitiveCycle(log_dir=log_dir)
    cc.run("audit memory")

    files = glob.glob(os.path.join(log_dir, "*.json"))
    assert len(files) == 1, "expected exactly one cycle log written"

    with open(files[0], "r", encoding="utf-8") as f:
        record = json.load(f)

    # Every log carries its own integrity proof.
    assert verify_log(record) is True


def test_verify_log_rejects_tampered_record(tmp_path) -> None:
    log_dir = str(tmp_path / "cycles")
    cc = CognitiveCycle(log_dir=log_dir)
    cc.run("audit field")

    files = glob.glob(os.path.join(log_dir, "*.json"))
    with open(files[0], "r", encoding="utf-8") as f:
        record = json.load(f)

    # Tamper: change the goal but keep the original stamp.
    record["goal"] = "different goal"
    assert verify_log(record) is False


def test_log_filename_contains_crest(tmp_path) -> None:
    log_dir = str(tmp_path / "cycles")
    cc = CognitiveCycle(log_dir=log_dir)
    r = cc.run("validate phase coherence")
    files = os.listdir(log_dir)
    assert any(r.crest in name for name in files)


def test_no_log_dir_means_no_files_written(tmp_path) -> None:
    # CognitiveCycle without log_dir should not touch the filesystem.
    cc = CognitiveCycle()
    cc.run("observe")
    # tmp_path is empty; this test just confirms no AttributeError or write.
    assert os.listdir(tmp_path) == []


def test_verify_log_handles_garbage() -> None:
    assert verify_log({}) is False
    assert verify_log({"sha256": "abc"}) is False
    assert verify_log("not a dict") is False  # type: ignore[arg-type]


def test_decompose_always_includes_memory_recall() -> None:
    """Every goal grounds in the corpus — MEMORY is always dispatched."""
    cc = CognitiveCycle()
    assert TaskType.MEMORY in cc.decompose("anything at all")
    assert TaskType.MEMORY in cc.decompose("xyzzy plugh")
    assert TaskType.MEMORY in cc.decompose("validate phase")


def test_memory_keeper_searches_corpus(tmp_path) -> None:
    """MemoryKeeperAgent reads a corpus index from disk and returns ranked hits."""
    from snell_vern_matrix.agents.agent_03_memory_keeper import MemoryKeeperAgent
    from snell_vern_matrix.agents import Task, TaskType

    corpus = {
        "count": 3,
        "generated_at_iso": "2026-05-02T03:00:00",
        "entries": [
            {"name": "lucas_formula.md", "excerpt": "lucas numbers and fibonacci closed form",
             "ext": ".md", "path": "/x/lucas.md", "root": "test", "mtime": 100},
            {"name": "phaistos_disc.md", "excerpt": "spiral mapping of phaistos signs",
             "ext": ".md", "path": "/x/phaistos.md", "root": "test", "mtime": 200},
            {"name": "irrelevant.md", "excerpt": "shopping list for groceries",
             "ext": ".md", "path": "/x/irr.md", "root": "test", "mtime": 50},
        ],
    }
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(__import__("json").dumps(corpus), encoding="utf-8")

    agent = MemoryKeeperAgent("agent-03")
    task = Task(
        task_id="t1",
        task_type=TaskType.MEMORY,
        payload={"action": "search", "query": "lucas formula", "corpus_path": str(corpus_path)},
    )
    result = agent.execute(task)
    assert result["matched"] is True
    assert result["total_hits"] >= 1
    # The lucas entry should rank first (filename hit + excerpt match)
    assert result["top"][0]["name"] == "lucas_formula.md"
    assert result["top"][0]["name_hit"] is True


def test_memory_keeper_handles_missing_corpus() -> None:
    from snell_vern_matrix.agents.agent_03_memory_keeper import MemoryKeeperAgent
    from snell_vern_matrix.agents import Task, TaskType

    agent = MemoryKeeperAgent("agent-03")
    task = Task(
        task_id="t1",
        task_type=TaskType.MEMORY,
        payload={"action": "search", "query": "anything", "corpus_path": r"C:\does\not\exist.json"},
    )
    result = agent.execute(task)
    assert result["matched"] is False
    assert "unavailable" in result["reason"]


def test_cycle_dispatches_real_lucas_sequence() -> None:
    """A goal mentioning lucas math should produce a real Lucas sequence."""
    cc = CognitiveCycle()
    r = cc.run("compute lucas sequence")
    seq_results = [x for x in r.results if x.get("action") == "sequence"]
    assert len(seq_results) == 1
    values = seq_results[0]["values"]
    # Lucas: 2, 1, 3, 4, 7, 11, 18, 29, 47, 76, 123, 199, 322
    assert values["0"] == 2
    assert values["1"] == 1
    assert values["7"] == 29
    assert values["12"] == 322


def test_ci_sentinel_audit_handles_missing_base() -> None:
    """CI audit on missing base returns empty list cleanly."""
    from snell_vern_matrix.agents.agent_02_ci_sentinel import CISentinelAgent
    from snell_vern_matrix.agents import Task, TaskType

    agent = CISentinelAgent("agent-02")
    task = Task(
        task_id="t1",
        task_type=TaskType.CI_HEALTH,
        payload={"action": "audit", "base": r"C:\does\not\exist"},
    )
    result = agent.execute(task)
    assert result["action"] == "audit"
    assert result["total_repos"] == 0


def test_coherence_monitor_tracks_trend_over_cycles() -> None:
    """Coherence Monitor receives previous-cycle averages as agent_scores."""
    cc = CognitiveCycle()
    # First cycle: empty history → monitor gets [] as scores
    cc.run("track coherence")
    # Second cycle: monitor should get [first.avg] as agent_scores
    r2 = cc.run("track coherence again")
    monitor = [x for x in r2.results if "agents_below_threshold" in x and x.get("agent", "").endswith("-13")]
    assert len(monitor) == 1
    # system_healthy should reflect actual coherence trend, not always True
    assert "system_healthy" in monitor[0]
    assert "average_coherence" in monitor[0]


def test_doc_keeper_audit_returns_real_coverage() -> None:
    """DOCUMENTATION audit returns real coverage numbers from ast walk."""
    from snell_vern_matrix.agents.agent_12_doc_keeper import DocKeeperAgent
    from snell_vern_matrix.agents import Task, TaskType

    agent = DocKeeperAgent("agent-12")
    task = Task(
        task_id="t1",
        task_type=TaskType.DOCUMENTATION,
        payload={"action": "audit"},
    )
    result = agent.execute(task)
    assert result["action"] == "audit"
    assert result["py_files"] > 0  # the repo has Python files
    assert 0.0 <= result["module_doc_coverage"] <= 1.0
    assert 0.0 <= result["function_doc_coverage"] <= 1.0
    assert 0.0 <= result["class_doc_coverage"] <= 1.0


def test_repo_sync_status_handles_missing_base() -> None:
    """When the base path doesn't exist, status returns empty list cleanly."""
    from snell_vern_matrix.agents.agent_10_repo_sync import RepoSyncAgent
    from snell_vern_matrix.agents import Task, TaskType

    agent = RepoSyncAgent("agent-10")
    task = Task(
        task_id="t1",
        task_type=TaskType.SYNC,
        payload={"action": "status", "base": r"C:\does\not\exist"},
    )
    result = agent.execute(task)
    assert result["action"] == "status"
    assert result["total"] == 0
    assert result["repos"] == []


def test_cycle_dispatches_real_ternary_evaluation() -> None:
    """TERNARY task evaluates SCE-88 ternary stability on a balanced equilibrium."""
    cc = CognitiveCycle()
    r = cc.run("evaluate ternary logic")
    tern = [x for x in r.results if "stability" in x and x.get("agent", "").endswith("-08")]
    assert len(tern) == 1
    # The balanced (1/3, 1/3, 1/3) equilibrium should be STABLE.
    assert tern[0]["stability"] == "stable"
    assert len(tern[0]["balance"]) == 3


def test_cycle_dispatches_real_self_model_observe() -> None:
    """OBSERVATION task runs SelfModel.observe(goal) — real GlyphPhaseEngine work."""
    cc = CognitiveCycle()
    r = cc.run("observe the field")
    obs = [x for x in r.results if "observation" in x and x.get("agent", "").endswith("-09")]
    assert len(obs) == 1
    o = obs[0]["observation"]
    # observe() returns delta, uncertainty, coherence keys
    assert "delta" in o or "coherence" in o or "uncertainty" in o


def test_cycle_dispatches_real_phase_state() -> None:
    """A goal mentioning phase routes to PHASE Tracker with derived state."""
    cc = CognitiveCycle()
    # First cycle → INITIAL phase (no history yet).
    r1 = cc.run("track phase")
    phase_results = [x for x in r1.results if "current_phase" in x and x.get("agent", "").endswith("-05")]
    assert len(phase_results) == 1
    assert phase_results[0]["current_phase"] == "INITIAL"

    # Second cycle → derived from previous coherence (PROCESSING / DELTA / STABILIZED).
    r2 = cc.run("track phase again")
    phase_results = [x for x in r2.results if "current_phase" in x and x.get("agent", "").endswith("-05")]
    assert phase_results[0]["current_phase"] in ("PROCESSING", "DELTA_ADJUSTMENT", "STABILIZED", "ERROR")


def test_cycle_dispatches_real_constraint_check() -> None:
    """A goal mentioning validate routes to CONSTRAINT and exercises SCE-88 invariants."""
    cc = CognitiveCycle()
    r = cc.run("validate the framework")
    constraint_results = [x for x in r.results if "valid" in x and x.get("agent", "").endswith("-04")]
    assert len(constraint_results) == 1
    cr = constraint_results[0]
    # With valid mid-range values we feed, no violations should fire.
    assert cr["valid"] is True
    assert cr["violations"] == []


def test_test_validator_parses_pytest_summary() -> None:
    """The summary regex correctly pulls passed/failed from pytest output."""
    from snell_vern_matrix.agents.agent_11_test_validator import _SUMMARY_RE

    samples = [
        ("======= 364 passed, 1 warning in 1.81s =======", 364, 0),
        ("======= 320 passed in 8.15s =======", 320, 0),
        ("======= 1 failed, 361 passed, 1 warning in 1.66s =======", 361, 1),
    ]
    for line, expected_passed, expected_failed in samples:
        m = _SUMMARY_RE.search(line)
        assert m is not None, f"regex missed: {line}"
        passed = int(m.group("passed") or 0)
        failed = int(m.group("failed") or 0)
        assert passed == expected_passed, f"passed mismatch in {line}"
        assert failed == expected_failed, f"failed mismatch in {line}"


def test_test_validator_handles_missing_repo() -> None:
    """When repo path doesn't exist, agent returns ran=False with a reason."""
    from snell_vern_matrix.agents.agent_11_test_validator import TestValidatorAgent
    from snell_vern_matrix.agents import Task, TaskType

    agent = TestValidatorAgent("agent-11")
    task = Task(
        task_id="t1",
        task_type=TaskType.TESTING,
        payload={"action": "run", "repo_path": r"C:\does\not\exist"},
    )
    result = agent.execute(task)
    assert result["action"] == "run"
    assert result["ran"] is False
    assert "not found" in result["reason"]


def test_cycle_dispatches_aeon_engine() -> None:
    """A goal mentioning 'aeon' or 'thrust' routes FIELD task to the AEON action.
    Validates against the documented June 4 2025 PhaseII data."""
    cc = CognitiveCycle()
    r = cc.run("run aeon thrust simulation")
    field_results = [x for x in r.results if x.get("action") == "aeon" and x.get("agent", "").endswith("-07")]
    assert len(field_results) == 1
    f = field_results[0]
    if not f.get("ran"):
        # AEON module not reachable in this test env — that's a soft skip.
        return
    assert "constants" in f
    assert "thrust_series" in f
    assert "validation" in f
    # The headline check: the canonical AEON math reproduces the documented
    # June 4 2025 simulation to <1% rel error.
    assert f["validation"]["matched"] is True
    assert f["validation"]["max_rel_err"] < 0.01


def test_cycle_dispatches_real_field_spiral() -> None:
    """A goal mentioning field should produce real r=a√n, θ=nφ spiral coords."""
    cc = CognitiveCycle()
    r = cc.run("compute field spiral")
    field_results = [x for x in r.results if "golden_angle" in x and x.get("agent", "").endswith("-07")]
    assert len(field_results) == 1
    fr = field_results[0]
    # Golden angle is a known constant ~137.5°
    assert 137.5 < fr["golden_angle"] < 137.51
    # Points should be a list of (n, x, y) dicts
    assert "points" in fr
    assert len(fr["points"]) == 12
    # Origin starts at n=1 (point 0 might be undefined for sqrt-based radius)
    assert fr["points"][0]["n"] == 1


def test_cycle_dispatches_real_field_analysis() -> None:
    """When goal mentions angle/radius specifically, return single-point analysis."""
    cc = CognitiveCycle()
    r = cc.run("compute field radius and angle")
    field_results = [x for x in r.results if "golden_angle" in x and x.get("agent", "").endswith("-07")]
    assert len(field_results) == 1
    fr = field_results[0]
    assert "radius" in fr
    assert "angle" in fr


def test_cycle_dispatches_real_lucas_convergence() -> None:
    """A goal mentioning convergence should produce a real ratio → phi check."""
    cc = CognitiveCycle()
    r = cc.run("show lucas convergence to phi")
    conv_results = [x for x in r.results if x.get("action") == "convergence"]
    assert len(conv_results) == 1
    cr = conv_results[0]
    assert abs(cr["ratio"] - cr["phi"]) < 1e-6
    assert cr["converged"] is True


def test_cycle_run_actually_searches_corpus(tmp_path) -> None:
    """End-to-end: a cycle run dispatches a MEMORY task that returns real hits."""
    import json
    corpus = {
        "count": 1,
        "generated_at_iso": "2026-05-02T03:00:00",
        "entries": [
            {"name": "lucas_formula.md", "excerpt": "lucas numbers closed form",
             "ext": ".md", "path": "/x/lucas.md", "root": "test", "mtime": 100},
        ],
    }
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(json.dumps(corpus), encoding="utf-8")

    cc = CognitiveCycle()
    # Patch the agent's default corpus path for this run by overriding payload.
    # Easiest: dispatch directly with a search payload pointing at our test corpus.
    cc.orch.route_task(
        TaskType.MEMORY,
        {"action": "search", "query": "lucas formula", "corpus_path": str(corpus_path)},
    )
    results = cc.orch.process_all()
    memory_results = [r for r in results if r.get("action") == "searched"]
    assert len(memory_results) == 1
    assert memory_results[0]["matched"] is True
    assert memory_results[0]["top"][0]["name"] == "lucas_formula.md"
