"""
Lucas number computation using closed-form formula.

The Lucas sequence is a companion to the Fibonacci sequence, defined as:
    L(0) = 2, L(1) = 1
    L(n) = L(n-1) + L(n-2) for n ≥ 2

Sequence: 2, 1, 3, 4, 7, 11, 18, 29, 47, 76, 123, ...

The closed-form formula is:
    L(n) = φⁿ + ψⁿ

where φ and ψ are the golden ratio and its conjugate (roots of x² - x - 1 = 0).

Unlike Fibonacci, the Lucas formula involves a sum rather than a difference,
and notably does not require division by √5. The ψⁿ term alternates in sign
and decreases exponentially, so L(n) ≈ φⁿ for large n.

Key Properties:
- L(n)² - 5F(n)² = 4(-1)ⁿ (Cassini-like identity)
- L(n+1)/L(n) → φ as n → ∞ (ratio convergence)
- The triplet (L(3), L(4), L(5)) = (4, 7, 11) has special Diophantine properties

Applications in this framework:
- Ratio convergence analysis with provable error bounds
- Egyptian fraction decompositions (1/4 + 1/7 + 1/11)
- Field spacing in cryptographic entropy generation
- Frobenius number calculations for coin problems
"""

from .constants import PHI, PSI


def L(n: int) -> int:
    """
    Compute the nth Lucas number using the closed-form formula.
    
    Uses: L(n) = round(φⁿ + ψⁿ)
    
    The formula is exact due to the identity φⁿ + ψⁿ being an integer for all n ≥ 0.
    This is because both φ and ψ are algebraic integers (roots of monic polynomial
    with integer coefficients).
    
    Args:
        n: The index (must be non-negative)
        
    Returns:
        The nth Lucas number
        
    Raises:
        ValueError: If n is negative
        
    Examples:
        >>> L(0)
        2
        >>> L(1)
        1
        >>> L(3)
        4
        >>> L(4)
        7
        >>> L(5)
        11
        >>> L(10)
        123
        
    Mathematical Note:
        L(n) ≈ φⁿ for large n (since |ψⁿ| < 1)
        L(n) = F(n-1) + F(n+1) (relationship to Fibonacci)
        L(2n) = L(n)² - 2(-1)ⁿ (doubling formula)
    """
    if n < 0:
        raise ValueError("n must be >= 0")
    return int(round(PHI**n + PSI**n))
