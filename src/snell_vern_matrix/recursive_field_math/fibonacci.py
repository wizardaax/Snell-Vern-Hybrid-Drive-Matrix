"""
Fibonacci number computation using Binet's formula.

The Fibonacci sequence is defined recursively as:
    F(0) = 0, F(1) = 1
    F(n) = F(n-1) + F(n-2) for n ≥ 2

This module uses Binet's closed-form formula for direct computation:
    F(n) = (φⁿ - ψⁿ) / √5

where φ = (1+√5)/2 is the golden ratio and ψ = (1-√5)/2 is its conjugate.

The formula works because φ and ψ are roots of x² - x - 1 = 0, and the
recurrence relation can be solved using characteristic equation methods.

Note: For very large n (> 70), floating-point precision may introduce errors.
For cryptographic applications requiring exact values, use modular arithmetic
or integer-only recursive methods.
"""

import math

from .constants import PHI, PSI


def F(n: int) -> int:
    """
    Compute the nth Fibonacci number using Binet's formula.

    Uses the closed-form expression: F(n) = round((φⁿ - ψⁿ) / √5)

    This is exact for moderate n (< 70) due to |ψ| < 1, which makes the
    ψⁿ term negligible. The rounding eliminates floating-point errors.

    Args:
        n: The index (must be non-negative)

    Returns:
        The nth Fibonacci number

    Raises:
        ValueError: If n is negative

    Examples:
        >>> F(0)
        0
        >>> F(1)
        1
        >>> F(10)
        55
        >>> F(20)
        6765

    Mathematical Note:
        The growth rate of F(n) is φⁿ/√5, so F(n) ≈ φⁿ/√5 for large n.
        This exponential growth means F(100) has 21 digits.
    """
    if n < 0:
        raise ValueError("n must be >= 0")
    return int(round((PHI**n - PSI**n) / math.sqrt(5)))
