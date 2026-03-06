"""Tests for the GlyphPhaseEngine."""

from glyph_phase_engine import GlyphPhaseEngine, PhaseState


class TestGlyphPhaseEngine:
    """Test cases for GlyphPhaseEngine."""

    def test_initialization(self):
        """Test engine initialization."""
        engine = GlyphPhaseEngine()
        assert engine.current_phase == PhaseState.INITIAL
        assert engine.delta_values == []
        assert engine.symbolic_input is None
        assert engine.metadata == {}

    def test_initialization_with_phase(self):
        """Test engine initialization with custom phase."""
        engine = GlyphPhaseEngine(PhaseState.PROCESSING)
        assert engine.current_phase == PhaseState.PROCESSING

    def test_process_symbolic_input_short(self):
        """Test processing short symbolic input."""
        engine = GlyphPhaseEngine()
        result = engine.process_symbolic_input("test")
        assert result == PhaseState.STABILIZED
        assert engine.symbolic_input == "test"

    def test_process_symbolic_input_long(self):
        """Test processing long symbolic input."""
        engine = GlyphPhaseEngine()
        long_input = "x" * 150  # > 100 characters
        result = engine.process_symbolic_input(long_input)
        assert result == PhaseState.DELTA_ADJUSTMENT
        assert engine.symbolic_input == long_input

    def test_process_symbolic_input_invalid(self):
        """Test processing invalid symbolic input."""
        engine = GlyphPhaseEngine()
        result = engine.process_symbolic_input("")
        assert result == PhaseState.ERROR

        result = engine.process_symbolic_input(None)
        assert result == PhaseState.ERROR

    def test_adjust_phase_delta_small(self):
        """Test delta adjustment with small value."""
        engine = GlyphPhaseEngine(PhaseState.DELTA_ADJUSTMENT)
        result = engine.adjust_phase_delta(0.05)
        assert result == PhaseState.STABILIZED
        assert 0.05 in engine.delta_values

    def test_adjust_phase_delta_large(self):
        """Test delta adjustment with large value."""
        engine = GlyphPhaseEngine(PhaseState.DELTA_ADJUSTMENT)
        result = engine.adjust_phase_delta(1.5)
        assert result == PhaseState.ERROR
        assert 1.5 in engine.delta_values

    def test_adjust_phase_delta_medium(self):
        """Test delta adjustment with medium value."""
        engine = GlyphPhaseEngine(PhaseState.DELTA_ADJUSTMENT)
        result = engine.adjust_phase_delta(0.5)
        assert result == PhaseState.DELTA_ADJUSTMENT
        assert 0.5 in engine.delta_values

    def test_get_phase_info(self):
        """Test getting phase information."""
        engine = GlyphPhaseEngine()
        engine.process_symbolic_input("test")
        engine.adjust_phase_delta(0.3)

        info = engine.get_phase_info()
        assert info["current_phase"] == "stabilized"
        assert info["delta_values"] == [0.3]
        assert info["symbolic_input"] == "test"
        assert isinstance(info["metadata"], dict)

    def test_reset(self):
        """Test engine reset functionality."""
        engine = GlyphPhaseEngine()
        engine.process_symbolic_input("test")
        engine.adjust_phase_delta(0.5)
        engine.metadata["test"] = "value"

        engine.reset()
        assert engine.current_phase == PhaseState.INITIAL
        assert engine.delta_values == []
        assert engine.symbolic_input is None
        assert engine.metadata == {}


class TestPhaseState:
    """Test cases for PhaseState enum."""

    def test_phase_state_values(self):
        """Test phase state enum values."""
        assert PhaseState.INITIAL.value == "initial"
        assert PhaseState.PROCESSING.value == "processing"
        assert PhaseState.DELTA_ADJUSTMENT.value == "delta_adjustment"
        assert PhaseState.STABILIZED.value == "stabilized"
        assert PhaseState.ERROR.value == "error"

    def test_phase_state_iteration(self):
        """Test phase state enum iteration."""
        states = list(PhaseState)
        assert len(states) == 5
        assert PhaseState.INITIAL in states
        assert PhaseState.PROCESSING in states
        assert PhaseState.DELTA_ADJUSTMENT in states
        assert PhaseState.STABILIZED in states
        assert PhaseState.ERROR in states
