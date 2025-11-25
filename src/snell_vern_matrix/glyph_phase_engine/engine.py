"""
Core engine module for glyph phase processing.

The Glyph Phase Engine implements a symbolic state machine that processes
abstract "glyphs" (symbolic inputs) and manages computational phases.

Phase State Model:
The engine operates in distinct phases, forming a state machine:

    INITIAL → PROCESSING → DELTA_ADJUSTMENT → STABILIZED
                ↓                ↓
              ERROR ← ─────────────

States:
- INITIAL: Starting state, no input processed
- PROCESSING: Actively analyzing symbolic input
- DELTA_ADJUSTMENT: Refining computation based on delta values
- STABILIZED: Computation has converged/completed
- ERROR: Invalid input or computational failure

Symbolic Processing:
"Glyphs" are abstract symbolic entities that represent mathematical or
logical operations. The engine doesn't interpret the semantic meaning,
but rather tracks the computational state as symbols are processed.

Applications:
1. **Ternary Logic**: Three primary states (Initial, Delta, Stabilized)
   model balanced ternary or three-valued logic systems
2. **Adaptive Computation**: Delta adjustments allow self-regulating flows
3. **Symbolic Algebra**: Framework for building computer algebra systems
4. **Cryptographic State Machines**: Phase tracking for protocol states

Delta Adjustment Mechanism:
The delta parameter controls phase convergence:
- Small delta (|Δ| < 0.1): Indicates near-convergence → Stabilized
- Large delta (|Δ| > 1.0): Indicates divergence → Error
- Medium delta: Continues adjustment cycles

This creates a feedback loop where the system adapts based on how much
the computation is changing between iterations.

Security Note:
The phase engine itself doesn't handle sensitive data. It's a pure state
machine for controlling computational flow. Any cryptographic applications
should ensure that glyph content doesn't leak information through timing
or phase transition patterns.
"""

from enum import Enum
from typing import Any


class PhaseState(Enum):
    """
    Enumeration of possible phase states in the glyph processing engine.

    The phase states form a directed graph of possible transitions:
    - INITIAL can transition to PROCESSING
    - PROCESSING can transition to DELTA_ADJUSTMENT, STABILIZED, or ERROR
    - DELTA_ADJUSTMENT can transition to STABILIZED or ERROR
    - STABILIZED is a terminal success state
    - ERROR is a terminal failure state
    """

    INITIAL = "initial"
    PROCESSING = "processing"
    DELTA_ADJUSTMENT = "delta_adjustment"
    STABILIZED = "stabilized"
    ERROR = "error"


class GlyphPhaseEngine:
    """
    A symbolic processing engine with phase-state tracking.

    The GlyphPhaseEngine processes symbolic input (glyphs) through a series
    of computational phases, tracking state transitions and delta adjustments.

    Architecture:
    - **State Machine**: Maintains current phase from PhaseState enum
    - **Delta Tracking**: Records adjustment values for convergence analysis
    - **Symbolic Input**: Stores the most recent symbolic input string
    - **Metadata**: Extensible dictionary for custom state information

    Typical Workflow:
    1. Initialize engine with INITIAL or custom phase
    2. Process symbolic input → transitions to PROCESSING
    3. If needed, apply delta adjustments → DELTA_ADJUSTMENT phase
    4. Converge to STABILIZED or ERROR based on convergence criteria

    Example:
        >>> engine = GlyphPhaseEngine()
        >>> state = engine.process_symbolic_input("analyze field")
        >>> state == PhaseState.STABILIZED
        True
        >>> engine.adjust_phase_delta(0.05)  # Small delta
        >>> engine.current_phase == PhaseState.STABILIZED
        True

    The engine is designed to be extended for specific symbolic processing
    applications. The basic implementation uses simple heuristics (input length,
    delta magnitude), but subclasses can implement sophisticated analysis.

    Attributes:
        current_phase: Current PhaseState of the engine
        delta_values: List of all delta adjustments applied
        symbolic_input: Most recent symbolic input string
        metadata: Dictionary for storing custom state information
    """

    def __init__(self, initial_phase: PhaseState = PhaseState.INITIAL):
        """
        Initialize the glyph phase engine.

        Args:
            initial_phase: Starting phase state (default: PhaseState.INITIAL)
        """
        self.current_phase = initial_phase
        self.delta_values: list[float] = []
        self.symbolic_input: str | None = None
        self.metadata: dict[str, Any] = {}

    def process_symbolic_input(self, symbolic_input: str) -> PhaseState:
        """
        Process symbolic input and determine resulting phase state.

        This is the primary entry point for symbolic computation. The engine
        analyzes the input and transitions through phase states accordingly.

        Current Implementation:
        - Validates input (non-empty string)
        - Long input (>100 chars) → DELTA_ADJUSTMENT phase
        - Normal input → STABILIZED phase
        - Invalid input → ERROR phase

        Subclasses can override this to implement sophisticated symbolic
        analysis, pattern matching, or computational logic.

        Args:
            symbolic_input: The symbolic input string to process

        Returns:
            The new phase state after processing

        Examples:
            >>> engine = GlyphPhaseEngine()
            >>> engine.process_symbolic_input("compute")
            <PhaseState.STABILIZED: 'stabilized'>
            >>> engine.process_symbolic_input("x" * 150)
            <PhaseState.DELTA_ADJUSTMENT: 'delta_adjustment'>
            >>> engine.process_symbolic_input("")
            <PhaseState.ERROR: 'error'>

        Note:
            The simple length-based heuristic is a placeholder. Real applications
            should implement meaningful symbolic analysis based on glyph semantics.
        """
        self.symbolic_input = symbolic_input
        self.current_phase = PhaseState.PROCESSING

        try:
            # Basic symbolic processing simulation
            if not symbolic_input or not isinstance(symbolic_input, str):
                self.current_phase = PhaseState.ERROR
                return self.current_phase

            # Simulate processing based on input characteristics
            # Long input requires delta adjustment (iterative refinement)
            if len(symbolic_input) > 100:
                self.current_phase = PhaseState.DELTA_ADJUSTMENT
            else:
                # Short input stabilizes immediately
                self.current_phase = PhaseState.STABILIZED

        except Exception:
            # Any exception during processing leads to error state
            self.current_phase = PhaseState.ERROR

        return self.current_phase

    def adjust_phase_delta(self, delta_value: float) -> PhaseState:
        """
        Apply a delta adjustment to refine the computational phase.

        Delta adjustments represent iterative refinements in the computation.
        The magnitude of the delta indicates how much the computation is
        changing, which determines convergence.

        Convergence Criteria:
        - |delta| < 0.1: Small change → Converged to STABILIZED
        - |delta| > 1.0: Large change → Diverging to ERROR
        - 0.1 ≤ |delta| ≤ 1.0: Moderate → Continue DELTA_ADJUSTMENT

        This implements a simple form of convergence testing similar to
        iterative numerical methods (gradient descent, Newton-Raphson, etc.)

        Args:
            delta_value: The delta adjustment value (can be positive or negative)

        Returns:
            The new phase state after delta adjustment

        Examples:
            >>> engine = GlyphPhaseEngine(PhaseState.DELTA_ADJUSTMENT)
            >>> engine.adjust_phase_delta(0.05)
            <PhaseState.STABILIZED: 'stabilized'>
            >>> engine = GlyphPhaseEngine(PhaseState.DELTA_ADJUSTMENT)
            >>> engine.adjust_phase_delta(1.5)
            <PhaseState.ERROR: 'error'>

        Note:
            Delta values are accumulated in self.delta_values for analysis.
            Large accumulated deltas could indicate oscillation or divergence.
        """
        # Record the delta for tracking and analysis
        self.delta_values.append(delta_value)

        # Only process delta adjustments when in DELTA_ADJUSTMENT phase
        if self.current_phase == PhaseState.DELTA_ADJUSTMENT:
            # Apply convergence logic based on delta magnitude
            if abs(delta_value) < 0.1:
                # Small delta indicates convergence
                self.current_phase = PhaseState.STABILIZED
            elif abs(delta_value) > 1.0:
                # Large delta indicates divergence or error
                self.current_phase = PhaseState.ERROR
            # Otherwise stay in DELTA_ADJUSTMENT (medium delta)

        return self.current_phase

    def get_phase_info(self) -> dict[str, Any]:
        """
        Get comprehensive information about current phase state.

        Returns a dictionary containing all engine state information,
        useful for debugging, monitoring, or serialization.

        Returns:
            Dictionary with keys:
                - current_phase: String value of current PhaseState
                - delta_values: Copy of all delta adjustments
                - symbolic_input: Most recent input (or None)
                - metadata: Copy of metadata dictionary

        Examples:
            >>> engine = GlyphPhaseEngine()
            >>> engine.process_symbolic_input("test")
            >>> info = engine.get_phase_info()
            >>> info['current_phase']
            'stabilized'
            >>> 'delta_values' in info
            True
        """
        return {
            "current_phase": self.current_phase.value,
            "delta_values": self.delta_values.copy(),
            "symbolic_input": self.symbolic_input,
            "metadata": self.metadata.copy(),
        }

    def reset(self) -> None:
        """
        Reset the engine to initial state.

        Clears all state including:
        - Phase returns to INITIAL
        - Delta values cleared
        - Symbolic input cleared
        - Metadata cleared

        Use this to reuse the engine for a new computation without
        creating a new instance.

        Examples:
            >>> engine = GlyphPhaseEngine()
            >>> engine.process_symbolic_input("test")
            >>> engine.reset()
            >>> engine.current_phase == PhaseState.INITIAL
            True
            >>> len(engine.delta_values)
            0
        """
        self.current_phase = PhaseState.INITIAL
        self.delta_values.clear()
        self.symbolic_input = None
        self.metadata.clear()
