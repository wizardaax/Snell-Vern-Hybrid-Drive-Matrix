"""
Snell-Vern Drive Matrix: Unified Engine for Recursive Field Computations

This module provides the DriveMatrix class that integrates all components:
- GlyphPhaseEngine for phase-state tracking
- Recursive Field Math for Lucas/Fibonacci sequences
- Recursive Field for phyllotaxis patterns
"""

from enum import Enum
from typing import Any

from .glyph_phase_engine import GlyphPhaseEngine, PhaseState
from .recursive_field import angle as rf_angle
from .recursive_field import golden_angle, position, radius
from .recursive_field_math import (
    PHI,
    PSI,
    F,
    L,
    egypt_4_7_11,
    r_theta,
    ratio,
    ratio_error_bounds,
    signature_summary,
)


class MatrixState(Enum):
    """Enumeration of drive matrix operational states."""
    IDLE = "idle"
    COMPUTING = "computing"
    FIELD_ANALYSIS = "field_analysis"
    PHASE_SYNC = "phase_sync"
    COMPLETE = "complete"
    ERROR = "error"


class DriveMatrix:
    """
    Unified Drive Matrix Engine that combines all recursive field computations.

    This engine orchestrates:
    - Symbolic input processing via GlyphPhaseEngine
    - Lucas and Fibonacci sequence calculations
    - Phyllotaxis field pattern analysis
    - Phase-state synchronization
    """

    def __init__(self):
        """Initialize the Drive Matrix with all component engines."""
        self.state = MatrixState.IDLE
        self.phase_engine = GlyphPhaseEngine()
        self.computation_results: dict[str, Any] = {}
        self.field_data: list[tuple[float, float]] = []
        self.sequence_cache: dict[str, dict[int, int]] = {
            "fibonacci": {},
            "lucas": {}
        }

    def process_input(self, symbolic_input: str) -> MatrixState:
        """
        Process symbolic input through the phase engine.

        Args:
            symbolic_input: The symbolic input to process

        Returns:
            The resulting matrix state
        """
        self.state = MatrixState.COMPUTING
        phase_result = self.phase_engine.process_symbolic_input(symbolic_input)

        if phase_result == PhaseState.ERROR:
            self.state = MatrixState.ERROR
        elif phase_result == PhaseState.STABILIZED:
            self.state = MatrixState.COMPLETE
        else:
            self.state = MatrixState.PHASE_SYNC

        return self.state

    def compute_field(self, start: int, end: int) -> list[tuple[float, float]]:
        """
        Compute phyllotaxis field positions for a range of indices.

        Args:
            start: Starting index (must be positive)
            end: Ending index

        Returns:
            List of (x, y) positions for each index
        """
        self.state = MatrixState.FIELD_ANALYSIS
        self.field_data = []

        for n in range(start, end + 1):
            pos = position(n)
            self.field_data.append(pos)

        self.state = MatrixState.COMPLETE
        return self.field_data

    def compute_r_theta_field(
        self, start: int, end: int
    ) -> dict[int, tuple[float, float]]:
        """
        Compute radial/angular field values for a range of indices.

        Args:
            start: Starting index (must be >= 1)
            end: Ending index

        Returns:
            Dictionary mapping index to (radius, theta) pairs
        """
        self.state = MatrixState.FIELD_ANALYSIS
        result = {}

        for n in range(start, end + 1):
            result[n] = r_theta(n)

        self.computation_results["r_theta_field"] = result
        self.state = MatrixState.COMPLETE
        return result

    def compute_sequences(self, max_n: int) -> dict[str, dict[int, int]]:
        """
        Compute Fibonacci and Lucas sequences up to max_n.

        Args:
            max_n: Maximum index to compute

        Returns:
            Dictionary with 'fibonacci' and 'lucas' sequences
        """
        self.state = MatrixState.COMPUTING

        for n in range(max_n + 1):
            if n not in self.sequence_cache["fibonacci"]:
                self.sequence_cache["fibonacci"][n] = F(n)
            if n not in self.sequence_cache["lucas"]:
                self.sequence_cache["lucas"][n] = L(n)

        fib_items = self.sequence_cache["fibonacci"].items()
        lucas_items = self.sequence_cache["lucas"].items()
        self.computation_results["sequences"] = {
            "fibonacci": dict(list(fib_items)[: max_n + 1]),
            "lucas": dict(list(lucas_items)[: max_n + 1]),
        }
        self.state = MatrixState.COMPLETE
        return self.computation_results["sequences"]

    def analyze_lucas_ratios(self, max_n: int) -> dict[str, Any]:
        """
        Analyze Lucas number ratios and their convergence to PHI.

        Args:
            max_n: Maximum index for analysis

        Returns:
            Analysis results including ratios and error bounds
        """
        self.state = MatrixState.FIELD_ANALYSIS
        ratios = {}
        bounds = {}

        for n in range(1, max_n + 1):
            ratios[n] = ratio(n)
            bounds[n] = ratio_error_bounds(n)

        result = {
            "phi": PHI,
            "psi": PSI,
            "ratios": ratios,
            "error_bounds": bounds,
            "signature": signature_summary(),
            "egyptian_fraction": egypt_4_7_11()
        }

        self.computation_results["lucas_analysis"] = result
        self.state = MatrixState.COMPLETE
        return result

    def get_golden_field_analysis(self) -> dict[str, Any]:
        """
        Get comprehensive golden angle field analysis.

        Returns:
            Dictionary with golden angle data and field characteristics
        """
        ga = golden_angle()
        return {
            "golden_angle_degrees": ga,
            "phi": PHI,
            "psi": PSI,
            "field_samples": [
                {"n": n, "radius": radius(n), "angle": rf_angle(n)}
                for n in range(1, 11)
            ]
        }

    def get_status(self) -> dict[str, Any]:
        """
        Get current drive matrix status.

        Returns:
            Dictionary with current state and computation info
        """
        return {
            "matrix_state": self.state.value,
            "phase_info": self.phase_engine.get_phase_info(),
            "field_data_count": len(self.field_data),
            "cached_fibonacci": len(self.sequence_cache["fibonacci"]),
            "cached_lucas": len(self.sequence_cache["lucas"]),
            "computation_results_keys": list(self.computation_results.keys())
        }

    def reset(self) -> None:
        """Reset the drive matrix to initial state."""
        self.state = MatrixState.IDLE
        self.phase_engine.reset()
        self.computation_results.clear()
        self.field_data.clear()
        # Keep sequence cache for efficiency
