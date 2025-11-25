"""Tests for the recursive_field module (phyllotaxis patterns)."""

import math

from snell_vern_matrix.recursive_field import angle, golden_angle, position, radius


class TestGoldenAngle:
    """Tests for golden angle calculations."""

    def test_golden_angle_value(self):
        """Test golden angle is approximately 137.508 degrees."""
        ga = golden_angle()
        assert abs(ga - 137.508) < 0.001

    def test_golden_angle_derivation(self):
        """Test golden angle derivation from golden ratio."""
        ga = golden_angle()
        expected = 180.0 * (3.0 - math.sqrt(5.0))
        assert ga == expected


class TestRadius:
    """Tests for radius calculations."""

    def test_radius_positive_index(self):
        """Test radius calculation for positive indices."""
        assert radius(1) == 3.0
        assert abs(radius(4) - 6.0) < 0.0001  # 3 * sqrt(4) = 6
        assert abs(radius(9) - 9.0) < 0.0001  # 3 * sqrt(9) = 9

    def test_radius_with_scale(self):
        """Test radius calculation with custom scale factor."""
        assert radius(4, a=2.0) == 4.0  # 2 * sqrt(4) = 4
        assert radius(1, a=5.0) == 5.0

    def test_radius_invalid_index(self):
        """Test radius raises error for non-positive indices."""
        import pytest

        with pytest.raises(ValueError, match="positive"):
            radius(0)

        with pytest.raises(ValueError, match="positive"):
            radius(-1)


class TestAngle:
    """Tests for angle calculations."""

    def test_angle_values(self):
        """Test angle calculations return values in [0, 360)."""
        for n in range(1, 100):
            a = angle(n)
            assert 0 <= a < 360

    def test_angle_progression(self):
        """Test angle progresses by golden angle."""
        ga = golden_angle()
        a1 = angle(1)
        a2 = angle(2)
        # Difference should be golden angle (mod 360)
        diff = (a2 - a1) % 360
        assert abs(diff - ga) < 0.0001 or abs(diff - (360 - ga)) < 0.0001


class TestPosition:
    """Tests for Cartesian position calculations."""

    def test_position_returns_tuple(self):
        """Test position returns (x, y) tuple."""
        pos = position(1)
        assert isinstance(pos, tuple)
        assert len(pos) == 2

    def test_position_distance(self):
        """Test position distance matches radius."""
        for n in [1, 5, 10]:
            x, y = position(n)
            r = radius(n)
            calculated_r = math.sqrt(x**2 + y**2)
            assert abs(calculated_r - r) < 0.0001

    def test_position_invalid_index(self):
        """Test position raises error for non-positive indices."""
        import pytest

        with pytest.raises(ValueError):
            position(0)

        with pytest.raises(ValueError):
            position(-1)
