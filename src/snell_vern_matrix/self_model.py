"""
Sentience Seed Module: Self-Model for the Snell-Vern Hybrid Drive Matrix.

Provides a deterministic, thread-safe self-model that observes symbolic input,
tracks internal state via Lucas 4-7-11 math and golden-angle field calculations,
and validates coherence against SCE-88 constraint topology.
"""

from __future__ import annotations

import hashlib
import json
import math
import threading
from enum import Enum
from typing import Any, Optional

from glyph_phase_engine import GlyphPhaseEngine, PhaseState
from recursive_field_math import (
    PHI,
    L,
    egypt_4_7_11,
    ratio,
    signature_summary,
)

from .recursive_field import golden_angle

# ---------------------------------------------------------------------------
# SCE-88 constraint topology
# ---------------------------------------------------------------------------
# REQ-01: coherence_score must remain in [0.0, 1.0]
# REQ-02: phase_state must be a valid PhaseState value
# REQ-03: uncertainty must remain in [0.0, 1.0]
# REQ-04: ternary_balance components must each be in [-1.0, 1.0]
# REQ-05: ternary_balance components must sum to approximately 0 (|sum| <= 1.0)

_SCE88_COHERENCE_BOUNDS = (0.0, 1.0)
_SCE88_UNCERTAINTY_BOUNDS = (0.0, 1.0)
_SCE88_TERNARY_COMPONENT_BOUNDS = (-1.0, 1.0)
_SCE88_TERNARY_SUM_TOLERANCE = 1.0


class ConstraintViolation(Exception):
    """Raised when an SCE-88 constraint is violated."""


class TernaryStability(Enum):
    """Ternary balance stability classification."""

    STABLE = "stable"
    UNSTABLE = "unstable"
    CRITICAL = "critical"


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _input_hash(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _validate_coherence(score: float) -> None:
    lo, hi = _SCE88_COHERENCE_BOUNDS
    if not (lo <= score <= hi):
        raise ConstraintViolation(
            f"SCE-88 REQ-01: coherence_score {score} out of bounds [{lo}, {hi}]"
        )


def _validate_phase_state(phase: PhaseState) -> None:
    if not isinstance(phase, PhaseState):
        raise ConstraintViolation(
            f"SCE-88 REQ-02: phase_state must be PhaseState, got {type(phase)}"
        )


def _validate_uncertainty(uncertainty: float) -> None:
    lo, hi = _SCE88_UNCERTAINTY_BOUNDS
    if not (lo <= uncertainty <= hi):
        raise ConstraintViolation(
            f"SCE-88 REQ-03: uncertainty {uncertainty} out of bounds [{lo}, {hi}]"
        )


def _validate_ternary_balance(balance: tuple[float, float, float]) -> None:
    lo, hi = _SCE88_TERNARY_COMPONENT_BOUNDS
    for i, comp in enumerate(balance):
        if not (lo <= comp <= hi):
            raise ConstraintViolation(
                f"SCE-88 REQ-04: ternary_balance[{i}] = {comp} "
                f"out of bounds [{lo}, {hi}]"
            )
    total = sum(balance)
    if abs(total) > _SCE88_TERNARY_SUM_TOLERANCE:
        raise ConstraintViolation(
            f"SCE-88 REQ-05: ternary_balance sum {total} "
            f"exceeds tolerance {_SCE88_TERNARY_SUM_TOLERANCE}"
        )


def _validate_state(state: dict[str, Any]) -> None:
    """Run all SCE-88 constraint checks against a state dict."""
    _validate_phase_state(state["phase_state"])
    _validate_coherence(state["coherence_score"])
    _validate_uncertainty(state["uncertainty"])
    _validate_ternary_balance(state["ternary_balance"])


# ---------------------------------------------------------------------------
# Lucas 4-7-11 math helpers
# ---------------------------------------------------------------------------

_L3 = L(3)  # 4
_L4 = L(4)  # 7
_L5 = L(5)  # 11
_GOLDEN_ANGLE = golden_angle()  # ≈137.508°
_EGYPT_NUM: int
_EGYPT_DEN: int
_EGYPT_NUM, _EGYPT_DEN = egypt_4_7_11()  # (149, 308)


def _lucas_coherence(delta_values: list[float]) -> float:
    """Compute coherence score from delta history using Lucas ratio convergence."""
    if not delta_values:
        return 0.5
    # Use ratio of successive deltas mapped through Lucas convergence
    n = len(delta_values)
    # Convergence quality from Lucas ratio at depth n (capped at 20)
    depth = min(n, 20)
    rat = ratio(max(depth, 1))
    # Distance from PHI indicates convergence quality
    convergence_error = abs(rat - PHI)
    # Map through golden angle normalisation
    score = 1.0 / (1.0 + convergence_error * _L5)
    # Incorporate recent delta magnitude
    recent_mag = abs(delta_values[-1]) if delta_values else 0.0
    score *= 1.0 / (1.0 + recent_mag)
    return _clamp(score, 0.0, 1.0)


def _compute_phase_delta(input_pattern: str) -> float:
    """Derive a deterministic phase delta from input using golden-angle field."""
    h = _input_hash(input_pattern)
    # Extract numeric seed from hash (first 8 hex chars)
    seed = int(h[:8], 16)
    # Normalise into golden-angle fraction range
    raw = (seed % _EGYPT_DEN) / _EGYPT_DEN
    # Scale by Egyptian fraction ratio for 4-7-11 alignment
    delta = raw * (_EGYPT_NUM / _EGYPT_DEN)
    # Centre around zero for balanced adjustment
    return delta - (_EGYPT_NUM / (2 * _EGYPT_DEN))


def _update_ternary_balance(
    current: tuple[float, float, float],
    delta: float,
) -> tuple[float, float, float]:
    """Rotate ternary balance using golden-angle–weighted update."""
    angle_rad = math.radians(_GOLDEN_ANGLE)
    # Project delta onto three ternary axes offset by 120°
    t0 = current[0] + delta * math.cos(0.0)
    t1 = current[1] + delta * math.cos(angle_rad)
    t2 = current[2] + delta * math.cos(2 * angle_rad)
    # Normalise so components stay bounded and sum ≈ 0
    mean = (t0 + t1 + t2) / 3.0
    t0 -= mean
    t1 -= mean
    t2 -= mean
    # Clamp individual components
    lo, hi = _SCE88_TERNARY_COMPONENT_BOUNDS
    t0 = _clamp(t0, lo, hi)
    t1 = _clamp(t1, lo, hi)
    t2 = _clamp(t2, lo, hi)
    return (t0, t1, t2)


def _ternary_stability(balance: tuple[float, float, float]) -> TernaryStability:
    """Classify ternary balance stability."""
    spread = max(balance) - min(balance)
    if spread < 0.3:
        return TernaryStability.STABLE
    elif spread < 0.7:
        return TernaryStability.UNSTABLE
    else:
        return TernaryStability.CRITICAL


# ---------------------------------------------------------------------------
# SelfModel
# ---------------------------------------------------------------------------


class SelfModel:
    """
    Self-model for the Snell-Vern Hybrid Drive Matrix.

    Wraps SCE-88 constraint topology and provides three core operations:
    - observe(input_pattern): process symbolic input, update internal state
    - ask(): introspect whether more data is needed
    - integrate(new_data): incorporate validated data into state

    Thread-safe and deterministic.  Zero new runtime dependencies.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._engine = GlyphPhaseEngine()
        self._state: dict[str, Any] = {
            "phase_state": PhaseState.INITIAL,
            "coherence_score": 0.5,
            "uncertainty": 0.5,
            "last_input_hash": "",
            "ternary_balance": (0.0, 0.0, 0.0),
        }
        self._delta_history: list[float] = []
        self._observation_count: int = 0

    # -- public read-only access ------------------------------------------

    @property
    def state(self) -> dict[str, Any]:
        """Return a snapshot of current internal state."""
        with self._lock:
            return dict(self._state)

    @property
    def phase_state(self) -> PhaseState:
        with self._lock:
            result: PhaseState = self._state["phase_state"]
            return result

    @property
    def coherence_score(self) -> float:
        with self._lock:
            result: float = self._state["coherence_score"]
            return result

    @property
    def uncertainty(self) -> float:
        with self._lock:
            result: float = self._state["uncertainty"]
            return result

    @property
    def ternary_balance(self) -> tuple[float, float, float]:
        with self._lock:
            result: tuple[float, float, float] = self._state["ternary_balance"]
            return result

    # -- core operations ---------------------------------------------------

    def observe(self, input_pattern: str) -> dict[str, Any]:
        """
        Process symbolic input and update internal state.

        Uses GlyphPhaseEngine for symbolic processing, Lucas 4-7-11 math
        for coherence tracking, and golden-angle field for delta calculation.

        Args:
            input_pattern: Symbolic input string to observe.

        Returns:
            Dictionary with ``delta``, ``uncertainty``, and ``coherence``
            after observation.

        Raises:
            ValueError: If *input_pattern* is empty or ``None``.
        """
        if not input_pattern:
            raise ValueError("input_pattern must be a non-empty string")

        with self._lock:
            # 1. Process symbolic input via GlyphPhaseEngine
            phase_result = self._engine.process_symbolic_input(input_pattern)
            self._state["phase_state"] = phase_result

            # 2. Compute deterministic phase delta
            delta = _compute_phase_delta(input_pattern)
            self._delta_history.append(delta)
            self._observation_count += 1

            # 3. Apply delta through GlyphPhaseEngine
            self._engine.adjust_phase_delta(delta)

            # 4. Update ternary balance
            self._state["ternary_balance"] = _update_ternary_balance(
                self._state["ternary_balance"], delta
            )

            # 5. Compute coherence via Lucas convergence
            coherence = _lucas_coherence(self._delta_history)
            self._state["coherence_score"] = coherence

            # 6. Update uncertainty — decays as observations accumulate
            obs = self._observation_count
            prev_unc = self._state["uncertainty"]
            decay_factor = _L3 / (_L3 + obs * (_L3 / _L5))
            self._state["uncertainty"] = _clamp(prev_unc * decay_factor, 0.0, 1.0)

            # 7. Record input hash
            self._state["last_input_hash"] = _input_hash(input_pattern)

            # 8. Validate against SCE-88 constraints
            _validate_state(self._state)

            return {
                "delta": delta,
                "uncertainty": self._state["uncertainty"],
                "coherence": coherence,
            }

    def ask(self) -> Optional[dict[str, Any]]:
        """
        Introspect whether the model needs more data.

        Returns a JSON-serialisable query dict when uncertainty > 0.3 or
        ternary balance is unstable; otherwise returns ``None``.
        """
        with self._lock:
            uncertainty = self._state["uncertainty"]
            stability = _ternary_stability(self._state["ternary_balance"])
            needs_data = uncertainty > 0.3 or stability != TernaryStability.STABLE

            if not needs_data:
                return None

            # Determine query type based on dominant source of need
            if stability == TernaryStability.CRITICAL:
                query_type = "field_coherence"
            elif stability == TernaryStability.UNSTABLE:
                query_type = "phase_delta"
            else:
                query_type = "lucas_convergence"

            sig = signature_summary()
            return {
                "type": query_type,
                "context": {
                    "uncertainty": uncertainty,
                    "ternary_stability": stability.value,
                    "coherence_score": self._state["coherence_score"],
                    "observation_count": self._observation_count,
                    "lucas_signature": {
                        "L3": sig["L3"],
                        "L4": sig["L4"],
                        "L5": sig["L5"],
                    },
                },
            }

    def integrate(self, new_data: dict[str, Any]) -> dict[str, Any]:
        """
        Integrate validated data into the model's state.

        Validates against SCE-88 constraint topology, updates phase state
        via GlyphPhaseEngine, and reduces uncertainty on success.

        Args:
            new_data: Dictionary with optional keys ``phase_delta`` (float),
                ``coherence_hint`` (float in [0, 1]), and
                ``ternary_adjustment`` (3-tuple of floats).

        Returns:
            Updated state snapshot.

        Raises:
            ConstraintViolation: If the resulting state violates SCE-88.
            ValueError: If *new_data* is not a dict.
        """
        if not isinstance(new_data, dict):
            raise ValueError("new_data must be a dictionary")

        with self._lock:
            # Snapshot for rollback on constraint failure
            prev_state = dict(self._state)
            prev_deltas = list(self._delta_history)

            try:
                # 1. Apply phase_delta if provided
                phase_delta = new_data.get("phase_delta")
                if phase_delta is not None:
                    pd = float(phase_delta)
                    self._engine.adjust_phase_delta(pd)
                    self._delta_history.append(pd)
                    self._state["phase_state"] = self._engine.current_phase
                    self._state["ternary_balance"] = _update_ternary_balance(
                        self._state["ternary_balance"], pd
                    )

                # 2. Apply coherence hint if provided (saved for blending
                # after lucas recomputation in step 4)
                coherence_hint = new_data.get("coherence_hint")

                # 3. Apply ternary adjustment if provided
                ternary_adj = new_data.get("ternary_adjustment")
                if ternary_adj is not None:
                    adj = tuple(float(x) for x in ternary_adj)
                    if len(adj) != 3:
                        raise ValueError(
                            "ternary_adjustment must have exactly 3 elements"
                        )
                    cur = self._state["ternary_balance"]
                    self._state["ternary_balance"] = _update_ternary_balance(
                        cur, sum(adj) / 3.0
                    )

                # 4. Recompute coherence from full delta history
                self._state["coherence_score"] = _lucas_coherence(self._delta_history)

                # 4b. Blend coherence hint after recomputation
                if coherence_hint is not None:
                    ch = float(coherence_hint)
                    old_c = self._state["coherence_score"]
                    self._state["coherence_score"] = _clamp(
                        (old_c + ch) / 2.0, 0.0, 1.0
                    )

                # 5. Reduce uncertainty on valid integration
                cur_unc = self._state["uncertainty"]
                reduction = (_EGYPT_NUM / _EGYPT_DEN) * 0.1
                self._state["uncertainty"] = _clamp(cur_unc - reduction, 0.0, 1.0)

                # 6. Validate final state
                _validate_state(self._state)

                return dict(self._state)

            except ConstraintViolation:
                # Rollback on violation
                self._state = prev_state
                self._delta_history = prev_deltas
                # Increase uncertainty on constraint violation
                self._state["uncertainty"] = _clamp(
                    self._state["uncertainty"] + 0.1, 0.0, 1.0
                )
                raise

    def to_json(self) -> str:
        """Serialise current state to a deterministic JSON string."""
        with self._lock:
            serialisable = {
                "phase_state": self._state["phase_state"].value,
                "coherence_score": self._state["coherence_score"],
                "uncertainty": self._state["uncertainty"],
                "last_input_hash": self._state["last_input_hash"],
                "ternary_balance": list(self._state["ternary_balance"]),
                "observation_count": self._observation_count,
                "delta_history_length": len(self._delta_history),
            }
            return json.dumps(serialisable, sort_keys=True)

    def reset(self) -> None:
        """Reset to initial state."""
        with self._lock:
            self._engine.reset()
            self._state = {
                "phase_state": PhaseState.INITIAL,
                "coherence_score": 0.5,
                "uncertainty": 0.5,
                "last_input_hash": "",
                "ternary_balance": (0.0, 0.0, 0.0),
            }
            self._delta_history = []
            self._observation_count = 0
