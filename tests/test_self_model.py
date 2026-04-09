"""
Tests for the sentience seed self-model module.

Covers:
- State persistence across sequential observe/integrate calls
- Uncertainty decay on valid integration, increase on constraint violation
- SCE-88 constraint validation (REQ-01 through REQ-05)
- CLI subcommand end-to-end
- Ternary logic balance tracking across phase transitions
- 55 tests covering core paths
"""

from __future__ import annotations

import json

import pytest
from glyph_phase_engine import PhaseState

from snell_vern_matrix.cli import main as cli_main
from snell_vern_matrix.self_model import (
    ConstraintViolation,
    SelfModel,
    TernaryStability,
    _compute_phase_delta,
    _input_hash,
    _lucas_coherence,
    _ternary_stability,
    _update_ternary_balance,
    _validate_coherence,
    _validate_phase_state,
    _validate_ternary_balance,
    _validate_uncertainty,
)

# =========================================================================
# SelfModel — initialisation
# =========================================================================


class TestSelfModelInit:
    def test_initial_phase_state(self) -> None:
        m = SelfModel()
        assert m.phase_state == PhaseState.INITIAL

    def test_initial_coherence(self) -> None:
        m = SelfModel()
        assert m.coherence_score == 0.5

    def test_initial_uncertainty(self) -> None:
        m = SelfModel()
        assert m.uncertainty == 0.5

    def test_initial_ternary_balance(self) -> None:
        m = SelfModel()
        assert m.ternary_balance == (0.0, 0.0, 0.0)

    def test_initial_last_input_hash_empty(self) -> None:
        m = SelfModel()
        assert m.state["last_input_hash"] == ""


# =========================================================================
# SelfModel.observe
# =========================================================================


class TestObserve:
    def test_observe_returns_delta(self) -> None:
        m = SelfModel()
        result = m.observe("hello")
        assert "delta" in result
        assert isinstance(result["delta"], float)

    def test_observe_returns_uncertainty(self) -> None:
        m = SelfModel()
        result = m.observe("hello")
        assert "uncertainty" in result
        assert 0.0 <= result["uncertainty"] <= 1.0

    def test_observe_returns_coherence(self) -> None:
        m = SelfModel()
        result = m.observe("hello")
        assert "coherence" in result
        assert 0.0 <= result["coherence"] <= 1.0

    def test_observe_updates_phase_state(self) -> None:
        m = SelfModel()
        m.observe("hello")
        assert m.phase_state != PhaseState.INITIAL

    def test_observe_updates_input_hash(self) -> None:
        m = SelfModel()
        m.observe("hello")
        assert m.state["last_input_hash"] == _input_hash("hello")

    def test_observe_empty_raises(self) -> None:
        m = SelfModel()
        with pytest.raises(ValueError, match="non-empty"):
            m.observe("")

    def test_observe_none_raises(self) -> None:
        m = SelfModel()
        with pytest.raises((ValueError, TypeError)):
            m.observe(None)  # type: ignore[arg-type]

    def test_observe_deterministic(self) -> None:
        m1 = SelfModel()
        m2 = SelfModel()
        r1 = m1.observe("same_input")
        r2 = m2.observe("same_input")
        assert r1 == r2

    def test_observe_different_inputs_differ(self) -> None:
        m1 = SelfModel()
        m2 = SelfModel()
        r1 = m1.observe("input_a")
        r2 = m2.observe("input_b")
        assert r1["delta"] != r2["delta"]


# =========================================================================
# State persistence across sequential calls
# =========================================================================


class TestStatePersistence:
    def test_state_persists_across_observations(self) -> None:
        m = SelfModel()
        m.observe("first")
        s1 = m.state.copy()
        m.observe("second")
        s2 = m.state
        # State should have changed
        assert s1["last_input_hash"] != s2["last_input_hash"]
        assert s1["uncertainty"] != s2["uncertainty"]

    def test_state_persists_across_integrate(self) -> None:
        m = SelfModel()
        m.observe("seed")
        s_before = m.state.copy()
        m.integrate({"phase_delta": 0.01})
        s_after = m.state
        # Uncertainty should have decreased
        assert s_after["uncertainty"] < s_before["uncertainty"]


# =========================================================================
# Uncertainty behaviour
# =========================================================================


class TestUncertainty:
    def test_uncertainty_decays_on_observe(self) -> None:
        m = SelfModel()
        initial = m.uncertainty
        m.observe("data1")
        assert m.uncertainty < initial

    def test_uncertainty_continues_to_decay(self) -> None:
        m = SelfModel()
        prev = m.uncertainty
        for i in range(5):
            m.observe(f"data_{i}")
            current = m.uncertainty
            assert current < prev
            prev = current

    def test_uncertainty_decays_on_valid_integration(self) -> None:
        m = SelfModel()
        m.observe("seed")
        unc_before = m.uncertainty
        m.integrate({"phase_delta": 0.01})
        assert m.uncertainty < unc_before

    def test_uncertainty_increases_on_constraint_violation(self) -> None:
        m = SelfModel()
        m.observe("seed")
        unc_before = m.uncertainty
        # Manually corrupt internal state to force a constraint violation
        # during integrate.  We set coherence out-of-bounds so that
        # _validate_state raises ConstraintViolation after integration.
        with m._lock:
            m._state["coherence_score"] = 0.99
        # Now integrate: the lucas recomputation will overwrite, but the
        # coherence_hint blending with 5.0 pushes it above 1.0 → REQ-01 fail.
        # Actually, _clamp prevents that.  Instead, we temporarily patch
        # _validate_state to always reject:
        import snell_vern_matrix.self_model as sm_mod

        original = sm_mod._validate_state

        def _strict_validate(state: dict) -> None:  # type: ignore[type-arg]
            original(state)
            # Reject any integration attempt for this test
            raise ConstraintViolation("forced violation for test")

        sm_mod._validate_state = _strict_validate  # type: ignore[assignment]
        try:
            with pytest.raises(ConstraintViolation):
                m.integrate({"phase_delta": 0.01})
            assert m.uncertainty >= unc_before
        finally:
            sm_mod._validate_state = original  # type: ignore[assignment]


# =========================================================================
# SCE-88 constraint validation
# =========================================================================


class TestSCE88Constraints:
    def test_req01_coherence_out_of_bounds_low(self) -> None:
        with pytest.raises(ConstraintViolation, match="REQ-01"):
            _validate_coherence(-0.1)

    def test_req01_coherence_out_of_bounds_high(self) -> None:
        with pytest.raises(ConstraintViolation, match="REQ-01"):
            _validate_coherence(1.1)

    def test_req02_invalid_phase_state(self) -> None:
        with pytest.raises(ConstraintViolation, match="REQ-02"):
            _validate_phase_state("not_a_phase")  # type: ignore[arg-type]

    def test_req03_uncertainty_out_of_bounds(self) -> None:
        with pytest.raises(ConstraintViolation, match="REQ-03"):
            _validate_uncertainty(-0.5)

    def test_req04_ternary_component_out_of_bounds(self) -> None:
        with pytest.raises(ConstraintViolation, match="REQ-04"):
            _validate_ternary_balance((2.0, 0.0, 0.0))

    def test_req05_ternary_sum_exceeds_tolerance(self) -> None:
        with pytest.raises(ConstraintViolation, match="REQ-05"):
            _validate_ternary_balance((0.9, 0.9, 0.9))

    def test_valid_state_passes_all_constraints(self) -> None:
        # Should not raise
        _validate_coherence(0.5)
        _validate_phase_state(PhaseState.INITIAL)
        _validate_uncertainty(0.5)
        _validate_ternary_balance((0.0, 0.0, 0.0))


# =========================================================================
# Ternary balance tracking
# =========================================================================


class TestTernaryBalance:
    def test_ternary_balance_updates_on_observe(self) -> None:
        m = SelfModel()
        m.observe("ternary_test")
        tb = m.ternary_balance
        assert tb != (0.0, 0.0, 0.0)

    def test_ternary_components_bounded(self) -> None:
        m = SelfModel()
        for i in range(20):
            m.observe(f"stress_test_{i}")
        for comp in m.ternary_balance:
            assert -1.0 <= comp <= 1.0

    def test_ternary_sum_near_zero(self) -> None:
        m = SelfModel()
        for i in range(10):
            m.observe(f"balance_{i}")
        total = sum(m.ternary_balance)
        assert abs(total) <= 1.0

    def test_ternary_stability_classification(self) -> None:
        assert _ternary_stability((0.0, 0.0, 0.0)) == TernaryStability.STABLE
        assert _ternary_stability((0.5, -0.5, 0.0)) == TernaryStability.CRITICAL
        assert _ternary_stability((0.2, -0.1, 0.0)) == TernaryStability.UNSTABLE

    def test_ternary_balance_across_phase_transitions(self) -> None:
        m = SelfModel()
        balances: list[tuple[float, float, float]] = []
        # Short input → STABILIZED transition
        m.observe("short")
        balances.append(m.ternary_balance)
        # Long input → DELTA_ADJUSTMENT transition
        m.observe("x" * 200)
        balances.append(m.ternary_balance)
        # Another short → back to STABILIZED
        m.observe("tiny")
        balances.append(m.ternary_balance)
        # All should differ
        assert len(set(balances)) == len(balances)


# =========================================================================
# SelfModel.ask
# =========================================================================


class TestAsk:
    def test_ask_returns_query_when_uncertain(self) -> None:
        m = SelfModel()
        # Initial uncertainty is 0.5 > 0.3
        query = m.ask()
        assert query is not None
        assert "type" in query
        assert "context" in query

    def test_ask_query_type_valid(self) -> None:
        m = SelfModel()
        query = m.ask()
        assert query is not None
        assert query["type"] in {
            "phase_delta",
            "lucas_convergence",
            "field_coherence",
        }

    def test_ask_returns_none_when_stable_and_certain(self) -> None:
        m = SelfModel()
        # Drive uncertainty below 0.3 and ternary to stable
        for i in range(10):
            m.observe(f"data_{i}")
        # If ternary is still unstable, ask may still return a query
        # but if both conditions met, should be None
        if m.uncertainty <= 0.3:
            stability = _ternary_stability(m.ternary_balance)
            if stability == TernaryStability.STABLE:
                assert m.ask() is None

    def test_ask_query_has_lucas_signature(self) -> None:
        m = SelfModel()
        query = m.ask()
        assert query is not None
        sig = query["context"]["lucas_signature"]
        assert sig["L3"] == 4
        assert sig["L4"] == 7
        assert sig["L5"] == 11


# =========================================================================
# SelfModel.integrate
# =========================================================================


class TestIntegrate:
    def test_integrate_with_phase_delta(self) -> None:
        m = SelfModel()
        result = m.integrate({"phase_delta": 0.05})
        assert "coherence_score" in result

    def test_integrate_with_coherence_hint(self) -> None:
        m = SelfModel()
        # First observe to populate delta_history, shifting coherence away
        # from the default 0.5
        m.observe("seed")
        baseline = m.coherence_score
        m.integrate({"coherence_hint": 0.9})
        # Blended coherence should differ from pre-integration value
        assert m.coherence_score != baseline

    def test_integrate_with_ternary_adjustment(self) -> None:
        m = SelfModel()
        m.integrate({"ternary_adjustment": [0.1, -0.05, 0.02]})
        assert m.ternary_balance != (0.0, 0.0, 0.0)

    def test_integrate_rejects_non_dict(self) -> None:
        m = SelfModel()
        with pytest.raises(ValueError, match="must be a dictionary"):
            m.integrate("not a dict")  # type: ignore[arg-type]

    def test_integrate_bad_ternary_length(self) -> None:
        m = SelfModel()
        with pytest.raises(ValueError, match="exactly 3"):
            m.integrate({"ternary_adjustment": [0.1, 0.2]})


# =========================================================================
# SelfModel.to_json and reset
# =========================================================================


class TestSerialisation:
    def test_to_json_valid(self) -> None:
        m = SelfModel()
        m.observe("test")
        j = m.to_json()
        data = json.loads(j)
        assert "phase_state" in data
        assert "coherence_score" in data
        assert "uncertainty" in data
        assert "ternary_balance" in data
        assert "observation_count" in data

    def test_reset_restores_initial(self) -> None:
        m = SelfModel()
        m.observe("data")
        m.integrate({"phase_delta": 0.1})
        m.reset()
        assert m.phase_state == PhaseState.INITIAL
        assert m.uncertainty == 0.5
        assert m.coherence_score == 0.5
        assert m.ternary_balance == (0.0, 0.0, 0.0)


# =========================================================================
# Helper functions
# =========================================================================


class TestHelpers:
    def test_input_hash_deterministic(self) -> None:
        assert _input_hash("abc") == _input_hash("abc")

    def test_input_hash_differs(self) -> None:
        assert _input_hash("abc") != _input_hash("def")

    def test_compute_phase_delta_deterministic(self) -> None:
        assert _compute_phase_delta("x") == _compute_phase_delta("x")

    def test_lucas_coherence_empty(self) -> None:
        assert _lucas_coherence([]) == 0.5

    def test_lucas_coherence_bounded(self) -> None:
        score = _lucas_coherence([0.1, 0.2, 0.3])
        assert 0.0 <= score <= 1.0

    def test_update_ternary_balance_sums_near_zero(self) -> None:
        result = _update_ternary_balance((0.0, 0.0, 0.0), 0.5)
        assert abs(sum(result)) < 1e-10


# =========================================================================
# CLI end-to-end
# =========================================================================


class TestCLI:
    def test_cli_observe(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["self-model", "--observe", "test_input"])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "delta" in data
        assert "uncertainty" in data

    def test_cli_ask(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["self-model", "--ask"])
        assert rc == 0
        out = capsys.readouterr().out.strip()
        # Should be valid JSON (either null or query object)
        if out == "null":
            pass
        else:
            data = json.loads(out)
            assert "type" in data

    def test_cli_integrate(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["self-model", "--integrate", '{"phase_delta": 0.02}'])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "phase_state" in data

    def test_cli_state(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["self-model", "--state"])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["phase_state"] == "initial"

    def test_cli_integrate_bad_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main(["self-model", "--integrate", "not-json"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "invalid JSON" in err

    def test_cli_no_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = cli_main([])
        assert rc == 0
