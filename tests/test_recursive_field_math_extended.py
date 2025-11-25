"""
Comprehensive tests for recursive_field_math modules.

This test suite covers edge cases and error conditions for:
- Generating functions (GF_F, GF_L)
- Continued fractions (lucas_ratio_cfrac)
- Egyptian fractions (egypt_4_7_11)
- Signatures (signature_summary)
"""

import math

import pytest

from snell_vern_matrix.recursive_field_math import (
    GF_F,
    GF_L,
    PHI,
    egypt_4_7_11,
    lucas_ratio_cfrac,
    signature_summary,
)


class TestGeneratingFunctions:
    """Test cases for Fibonacci and Lucas generating functions."""

    def test_gf_f_at_zero(self):
        """Test GF_F(0) = 0."""
        assert GF_F(0) == 0.0

    def test_gf_f_at_small_values(self):
        """Test GF_F at small positive values."""
        # GF_F(0.1) = 0.1 / (1 - 0.1 - 0.01) = 0.1 / 0.89
        result = GF_F(0.1)
        expected = 0.1 / (1 - 0.1 - 0.01)
        assert abs(result - expected) < 1e-10

    def test_gf_f_at_half(self):
        """Test GF_F(1/2) converges to sum of F(n)/2^n."""
        result = GF_F(0.5)
        # GF_F(1/2) = 0.5 / (1 - 0.5 - 0.25) = 0.5 / 0.25 = 2.0
        assert abs(result - 2.0) < 1e-10

    def test_gf_f_negative_value(self):
        """Test GF_F at negative values."""
        result = GF_F(-0.2)
        # Should work for small negative values
        assert isinstance(result, float)

    def test_gf_f_singularity_golden_ratio(self):
        """Test that GF_F raises error at singularity x = 1/phi."""
        with pytest.raises(ZeroDivisionError, match="Singularity"):
            GF_F(1 / PHI)

    def test_gf_f_near_singularity(self):
        """Test GF_F very close to (but not at) singularity."""
        # Just before singularity
        x = 1 / PHI - 0.001
        result = GF_F(x)
        assert isinstance(result, float)
        assert result > 0  # Should be large positive

    def test_gf_l_at_zero(self):
        """Test GF_L(0) = 2."""
        assert GF_L(0) == 2.0

    def test_gf_l_at_small_values(self):
        """Test GF_L at small positive values."""
        result = GF_L(0.1)
        expected = (2 - 0.1) / (1 - 0.1 - 0.01)
        assert abs(result - expected) < 1e-10

    def test_gf_l_singularity(self):
        """Test that GF_L raises error at singularity."""
        with pytest.raises(ZeroDivisionError, match="Singularity"):
            GF_L(1 / PHI)

    def test_gf_relationship(self):
        """Test relationship: GF_L(x) + GF_F(x) = 2/(1 - x - x^2)."""
        x = 0.3
        gf_f = GF_F(x)
        gf_l = GF_L(x)
        expected = 2 / (1 - x - x * x)
        assert abs(gf_f + gf_l - expected) < 1e-10

    def test_gf_f_multiple_values(self):
        """Test GF_F at multiple values for consistency."""
        test_values = [0.1, 0.2, 0.3, 0.4, 0.5]
        for x in test_values:
            result = GF_F(x)
            expected = x / (1 - x - x * x)
            assert abs(result - expected) < 1e-10

    def test_gf_l_multiple_values(self):
        """Test GF_L at multiple values for consistency."""
        test_values = [0.1, 0.2, 0.3, 0.4, 0.5]
        for x in test_values:
            result = GF_L(x)
            expected = (2 - x) / (1 - x - x * x)
            assert abs(result - expected) < 1e-10


class TestContinuedFractions:
    """Test cases for Lucas ratio continued fraction analysis."""

    def test_cfrac_n1(self):
        """Test continued fraction for n=1: L(2)/L(1) = 3/1."""
        num, den, meta = lucas_ratio_cfrac(1)
        assert num == 3
        assert den == 1
        assert meta["head"] == 1
        assert meta["ones"] == 0
        assert meta["tail"] == 3

    def test_cfrac_n2(self):
        """Test continued fraction for n=2: L(3)/L(2) = 4/3 = [1; 3]."""
        num, den, meta = lucas_ratio_cfrac(2)
        assert num == 4
        assert den == 3
        assert meta["ones"] == 0  # [1; 3] has 0 ones

    def test_cfrac_n3(self):
        """Test continued fraction for n=3: L(4)/L(3) = 7/4 = [1; 1, 3]."""
        num, den, meta = lucas_ratio_cfrac(3)
        assert num == 7
        assert den == 4
        assert meta["ones"] == 1  # [1; 1, 3] has 1 one

    def test_cfrac_n5(self):
        """Test continued fraction for n=5: L(6)/L(5) = 18/11."""
        num, den, meta = lucas_ratio_cfrac(5)
        assert num == 18
        assert den == 11
        assert meta["ones"] == 3  # [1; 1, 1, 1, 3] has 3 ones

    def test_cfrac_pattern_consistency(self):
        """Test that the ones count follows pattern max(0, n-2)."""
        for n in range(1, 10):
            _, _, meta = lucas_ratio_cfrac(n)
            expected_ones = max(0, n - 2)
            assert meta["ones"] == expected_ones

    def test_cfrac_ratio_convergence(self):
        """Test that ratios converge to PHI as n increases."""
        ratios = []
        for n in range(1, 15):
            num, den, _ = lucas_ratio_cfrac(n)
            ratios.append(num / den)

        # Later ratios should be closer to PHI
        assert abs(ratios[-1] - PHI) < abs(ratios[0] - PHI)
        assert abs(ratios[-1] - PHI) < 0.001

    def test_cfrac_invalid_n(self):
        """Test that n < 1 raises ValueError."""
        with pytest.raises(ValueError, match="n must be >= 1"):
            lucas_ratio_cfrac(0)

        with pytest.raises(ValueError, match="n must be >= 1"):
            lucas_ratio_cfrac(-1)


class TestEgyptianFraction:
    """Test cases for Egyptian fraction 1/4 + 1/7 + 1/11."""

    def test_egypt_basic(self):
        """Test basic Egyptian fraction calculation."""
        num, den = egypt_4_7_11()
        assert num == 149
        assert den == 308

    def test_egypt_decimal_value(self):
        """Test decimal value of Egyptian fraction."""
        num, den = egypt_4_7_11()
        decimal = num / den
        # Verify against direct calculation
        expected = 1 / 4 + 1 / 7 + 1 / 11
        assert abs(decimal - expected) < 1e-10

    def test_egypt_irreducible(self):
        """Test that 149/308 is in lowest terms."""
        num, den = egypt_4_7_11()
        from math import gcd

        assert gcd(num, den) == 1

    def test_egypt_prime_numerator(self):
        """Test that 149 is prime."""
        num, _ = egypt_4_7_11()
        assert num == 149

        # Verify 149 is prime
        def is_prime(n):
            if n < 2:
                return False
            for i in range(2, int(n**0.5) + 1):
                if n % i == 0:
                    return False
            return True

        assert is_prime(149)

    def test_egypt_denominator(self):
        """Test that denominator is 4 × 7 × 11 = 308."""
        _, den = egypt_4_7_11()
        assert den == 4 * 7 * 11
        assert den == 308

    def test_egypt_near_half(self):
        """Test that 149/308 is close to but not equal to 1/2."""
        num, den = egypt_4_7_11()
        value = num / den
        half = 0.5
        assert abs(value - half) > 0  # Not exactly 1/2
        assert abs(value - half) < 0.02  # But close to 1/2


class TestSignatures:
    """Test cases for Lucas 4-7-11 signature analysis."""

    def test_signature_values(self):
        """Test basic signature values."""
        sig = signature_summary()
        assert sig["L3"] == 4
        assert sig["L4"] == 7
        assert sig["L5"] == 11

    def test_signature_product(self):
        """Test signature product: 4 × 7 × 11 = 308."""
        sig = signature_summary()
        assert sig["product"] == 308
        assert sig["product"] == sig["L3"] * sig["L4"] * sig["L5"]

    def test_signature_pair_sum(self):
        """Test pair sum: (4×7) + (4×11) + (7×11) = 149."""
        sig = signature_summary()
        assert sig["pair_sum"] == 149
        expected = (4 * 7) + (4 * 11) + (7 * 11)
        assert sig["pair_sum"] == expected

    def test_signature_egypt_connection(self):
        """Test connection to Egyptian fraction."""
        sig = signature_summary()
        num, den = egypt_4_7_11()
        # Numerator equals pair sum
        assert sig["pair_sum"] == num
        # Denominator equals product
        assert sig["product"] == den

    def test_signature_frobenius(self):
        """Test Frobenius number F(4,7) = 17."""
        sig = signature_summary()
        assert sig["frobenius_4_7"] == 17
        assert sig["frobenius_4_7"] == 4 * 7 - 4 - 7

    def test_signature_additive_chain(self):
        """Test additive chain property: 4 + 7 = 11."""
        sig = signature_summary()
        assert sig["additive_chain"] is True
        assert sig["L3"] + sig["L4"] == sig["L5"]

    def test_signature_all_keys(self):
        """Test that signature contains all expected keys."""
        sig = signature_summary()
        expected_keys = {
            "L3",
            "L4",
            "L5",
            "product",
            "pair_sum",
            "frobenius_4_7",
            "additive_chain",
        }
        assert set(sig.keys()) == expected_keys


class TestEdgeCases:
    """Edge case tests for various mathematical functions."""

    def test_gf_boundary_values(self):
        """Test generating functions at boundary values."""
        # Very small x
        assert abs(GF_F(1e-10) - 1e-10) < 1e-15
        assert abs(GF_L(1e-10) - 2.0) < 1e-8  # Relaxed tolerance for floating-point

        # Negative small x
        gf_f_neg = GF_F(-0.01)
        gf_l_neg = GF_L(-0.01)
        assert isinstance(gf_f_neg, float)
        assert isinstance(gf_l_neg, float)

    def test_cfrac_large_n(self):
        """Test continued fractions for large n."""
        num, den, meta = lucas_ratio_cfrac(20)
        # Should still compute correctly
        assert num > den  # Ratio > 1
        assert abs(num / den - PHI) < 1e-8  # Very close to PHI
        assert meta["ones"] == 18  # max(0, 20-2) = 18

    def test_multiple_egypt_calls(self):
        """Test that multiple calls to egypt_4_7_11 are consistent."""
        results = [egypt_4_7_11() for _ in range(5)]
        # All results should be identical
        assert all(r == (149, 308) for r in results)

    def test_signature_idempotent(self):
        """Test that signature_summary is idempotent."""
        sig1 = signature_summary()
        sig2 = signature_summary()
        assert sig1 == sig2
