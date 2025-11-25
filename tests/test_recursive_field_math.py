"""Tests for the recursive_field_math module."""

from snell_vern_matrix.recursive_field_math import (
    F,
    L,
    egypt_4_7_11,
    r_theta,
    ratio,
    ratio_error_bounds,
    signature_summary,
)


def test_basic_sequences():
    """Test basic Fibonacci and Lucas sequences."""
    assert F(0) == 0
    assert F(1) == 1
    assert L(0) == 2
    assert L(1) == 1
    assert L(2) == 3
    assert L(3) == 4
    assert L(4) == 7
    assert L(5) == 11


def test_field():
    """Test field calculations."""
    r1, th1 = r_theta(1)
    assert r1 == 3.0  # r1 == 3*sqrt(1)


def test_ratio_bounds():
    """Test ratio error bounds."""
    r = ratio(5)
    lo, hi = ratio_error_bounds(5)
    assert lo > 0 and hi > lo
    assert r > 1


def test_egypt_and_signature():
    """Test Egyptian fraction and signature summary."""
    num, den = egypt_4_7_11()
    assert (num, den) == (149, 308)
    sig = signature_summary()
    assert sig["L3"] == 4 and sig["L4"] == 7 and sig["L5"] == 11
