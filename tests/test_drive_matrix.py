"""Tests for the DriveMatrix unified engine."""

from snell_vern_matrix import DriveMatrix, MatrixState, PhaseState


class TestDriveMatrix:
    """Test cases for the unified DriveMatrix."""

    def test_initialization(self):
        """Test DriveMatrix initialization."""
        matrix = DriveMatrix()
        assert matrix.state == MatrixState.IDLE
        assert matrix.field_data == []
        assert matrix.computation_results == {}

    def test_process_input_short(self):
        """Test processing short input."""
        matrix = DriveMatrix()
        result = matrix.process_input("test")
        assert result == MatrixState.COMPLETE
        assert matrix.phase_engine.current_phase == PhaseState.STABILIZED

    def test_process_input_long(self):
        """Test processing long input."""
        matrix = DriveMatrix()
        result = matrix.process_input("x" * 150)
        assert result == MatrixState.PHASE_SYNC

    def test_process_input_invalid(self):
        """Test processing invalid input."""
        matrix = DriveMatrix()
        result = matrix.process_input("")
        assert result == MatrixState.ERROR

    def test_compute_field(self):
        """Test field computation."""
        matrix = DriveMatrix()
        field = matrix.compute_field(1, 5)
        assert len(field) == 5
        assert all(isinstance(pos, tuple) and len(pos) == 2 for pos in field)
        assert matrix.state == MatrixState.COMPLETE

    def test_compute_r_theta_field(self):
        """Test r_theta field computation."""
        matrix = DriveMatrix()
        result = matrix.compute_r_theta_field(1, 5)
        assert len(result) == 5
        assert 1 in result and 5 in result
        assert all(isinstance(v, tuple) and len(v) == 2 for v in result.values())

    def test_compute_sequences(self):
        """Test Fibonacci and Lucas sequence computation."""
        matrix = DriveMatrix()
        result = matrix.compute_sequences(10)
        assert "fibonacci" in result
        assert "lucas" in result
        assert result["fibonacci"][0] == 0
        assert result["fibonacci"][1] == 1
        assert result["lucas"][0] == 2
        assert result["lucas"][4] == 7
        assert result["lucas"][5] == 11

    def test_analyze_lucas_ratios(self):
        """Test Lucas ratio analysis."""
        matrix = DriveMatrix()
        result = matrix.analyze_lucas_ratios(5)
        assert "phi" in result
        assert "ratios" in result
        assert "error_bounds" in result
        assert "signature" in result
        assert "egyptian_fraction" in result
        assert result["egyptian_fraction"] == (149, 308)

    def test_get_golden_field_analysis(self):
        """Test golden field analysis."""
        matrix = DriveMatrix()
        result = matrix.get_golden_field_analysis()
        assert "golden_angle_degrees" in result
        assert "phi" in result
        assert "field_samples" in result
        assert len(result["field_samples"]) == 10

    def test_get_status(self):
        """Test status retrieval."""
        matrix = DriveMatrix()
        status = matrix.get_status()
        assert "matrix_state" in status
        assert "phase_info" in status
        assert status["matrix_state"] == "idle"

    def test_reset(self):
        """Test matrix reset."""
        matrix = DriveMatrix()
        matrix.process_input("test")
        matrix.compute_field(1, 5)
        matrix.reset()
        assert matrix.state == MatrixState.IDLE
        assert matrix.field_data == []
        assert matrix.computation_results == {}


class TestMatrixState:
    """Test cases for MatrixState enum."""

    def test_matrix_state_values(self):
        """Test matrix state enum values."""
        assert MatrixState.IDLE.value == "idle"
        assert MatrixState.COMPUTING.value == "computing"
        assert MatrixState.FIELD_ANALYSIS.value == "field_analysis"
        assert MatrixState.PHASE_SYNC.value == "phase_sync"
        assert MatrixState.COMPLETE.value == "complete"
        assert MatrixState.ERROR.value == "error"
