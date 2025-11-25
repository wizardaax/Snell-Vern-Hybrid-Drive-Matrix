"""
Core engine module for glyph phase processing.
"""

from enum import Enum
from typing import Any


class PhaseState(Enum):
    """Enumeration of possible phase states."""
    INITIAL = "initial"
    PROCESSING = "processing"
    DELTA_ADJUSTMENT = "delta_adjustment"
    STABILIZED = "stabilized"
    ERROR = "error"


class GlyphPhaseEngine:
    """
    A Python engine that processes symbolic input and adjusts operational phase
    based on dynamic delta values.
    """

    def __init__(self, initial_phase: PhaseState = PhaseState.INITIAL):
        """Initialize the engine with an initial phase state."""
        self.current_phase = initial_phase
        self.delta_values: list[float] = []
        self.symbolic_input: str | None = None
        self.metadata: dict[str, Any] = {}

    def process_symbolic_input(self, symbolic_input: str) -> PhaseState:
        """
        Process symbolic input and potentially change phase state.
        
        Args:
            symbolic_input: The symbolic input to process
            
        Returns:
            The new phase state after processing
        """
        self.symbolic_input = symbolic_input
        self.current_phase = PhaseState.PROCESSING

        try:
            # Basic symbolic processing simulation
            if not symbolic_input or not isinstance(symbolic_input, str):
                self.current_phase = PhaseState.ERROR
                return self.current_phase

            # Simulate processing based on input characteristics
            if len(symbolic_input) > 100:
                self.current_phase = PhaseState.DELTA_ADJUSTMENT
            else:
                self.current_phase = PhaseState.STABILIZED

        except Exception:
            self.current_phase = PhaseState.ERROR

        return self.current_phase

    def adjust_phase_delta(self, delta_value: float) -> PhaseState:
        """
        Adjust the operational phase based on a delta value.
        
        Args:
            delta_value: The delta value to apply
            
        Returns:
            The new phase state after delta adjustment
        """
        self.delta_values.append(delta_value)

        if self.current_phase == PhaseState.DELTA_ADJUSTMENT:
            # Apply delta logic
            if abs(delta_value) < 0.1:
                self.current_phase = PhaseState.STABILIZED
            elif abs(delta_value) > 1.0:
                self.current_phase = PhaseState.ERROR
            # Otherwise stay in delta adjustment

        return self.current_phase

    def get_phase_info(self) -> dict[str, Any]:
        """
        Get current phase information.
        
        Returns:
            Dictionary containing phase state and related information
        """
        return {
            "current_phase": self.current_phase.value,
            "delta_values": self.delta_values.copy(),
            "symbolic_input": self.symbolic_input,
            "metadata": self.metadata.copy()
        }

    def reset(self) -> None:
        """Reset the engine to initial state."""
        self.current_phase = PhaseState.INITIAL
        self.delta_values.clear()
        self.symbolic_input = None
        self.metadata.clear()
