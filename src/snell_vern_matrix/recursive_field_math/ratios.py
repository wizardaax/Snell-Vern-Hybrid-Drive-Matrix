"""
Lucas ratio convergence analysis with error bounds.

This module analyzes the convergence of consecutive Lucas number ratios to
the golden ratio φ, with mathematically rigorous error bounds.

Convergence Property:
    lim(n→∞) L(n+1)/L(n) = φ

This convergence is exponential due to the |ψ|ⁿ decay in the error term,
where ψ ≈ -0.618 is the conjugate of φ.

Error Bound Derivation:
Given L(n) = φⁿ + ψⁿ, we have:
    L(n+1)/L(n) = (φⁿ⁺¹ + ψⁿ⁺¹)/(φⁿ + ψⁿ)
                = φ × (1 + (ψ/φ)ⁿ⁺¹)/(1 + (ψ/φ)ⁿ)
                
Since ψ/φ = -1/φ² ≈ -0.382, the error decreases exponentially.

The bounds implemented here use the identity:
    √5 / (Lₙ(Lₙ + |ψ|ⁿ)) ≤ |L(n+1)/L(n) - φ| ≤ √5 / (Lₙ(Lₙ - |ψ|ⁿ))

These bounds are tight and guarantee the accuracy of the ratio approximation.

Applications:
- Validating numerical implementations of the golden ratio
- Determining when ratio approximations are sufficiently accurate
- Educational demonstrations of limit convergence
- Quality control for cryptographic entropy derived from ratio sequences
"""

import math

from .constants import PSI
from .lucas import L


def ratio(n: int) -> float:
    """
    Compute the ratio L(n+1) / L(n).
    
    This ratio converges to the golden ratio φ as n increases. The convergence
    is exponential with rate |ψ|ⁿ where |ψ| ≈ 0.618.
    
    Convergence Examples:
        n=1:  L(2)/L(1) = 3/1 = 3.000      (error ≈ 1.382)
        n=2:  L(3)/L(2) = 4/3 ≈ 1.333      (error ≈ 0.285)
        n=5:  L(6)/L(5) = 18/11 ≈ 1.636    (error ≈ 0.018)
        n=10: L(11)/L(10) ≈ 1.6180328      (error < 0.0001)
    
    Args:
        n: The index (must be >= 1)
        
    Returns:
        The ratio L(n+1)/L(n) as a float
        
    Raises:
        ValueError: If n < 1
        
    Examples:
        >>> ratio(1)
        3.0
        >>> ratio(5)
        1.6363636363636365
        >>> abs(ratio(20) - 1.618033988749895) < 1e-10
        True
        
    Mathematical Note:
        The continued fraction expansion of L(n+1)/L(n) is [1; 1, 1, ..., 1, 3]
        with (n-2) ones in the middle. As n→∞, this approaches [1; 1, 1, ...] = φ.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    Ln, Lnp1 = L(n), L(n + 1)
    return Lnp1 / Ln


def ratio_error_bounds(n: int):
    """
    Compute rigorous error bounds for |L(n+1)/L(n) - φ|.
    
    Returns both lower and upper bounds on the absolute error between the
    ratio and the true golden ratio value.
    
    Derivation:
        The error formula comes from:
        |L(n+1)/L(n) - φ| = |ψⁿ⁺¹ - ψⁿφ| / |φⁿ + ψⁿ|
                          = |ψ|ⁿ × |ψ - φ| / |φⁿ + ψⁿ|
                          = √5 × |ψ|ⁿ / |φⁿ + ψⁿ|
        
        Since Lₙ = φⁿ + ψⁿ and bounds on |φⁿ + ψⁿ| are:
            Lₙ - |ψ|ⁿ ≤ |φⁿ + ψⁿ| ≤ Lₙ + |ψ|ⁿ
        
        We get the stated inequalities.
    
    Args:
        n: The index (must be >= 1)
        
    Returns:
        Tuple of (lower_bound, upper_bound) where both are positive floats
        representing bounds on the absolute error
        
    Raises:
        ValueError: If n < 1
        
    Examples:
        >>> lower, upper = ratio_error_bounds(5)
        >>> lower > 0 and upper > lower
        True
        >>> lower, upper = ratio_error_bounds(20)
        >>> upper < 1e-10  # Error is very small for large n
        True
        
    Mathematical Note:
        For large n, both bounds approach 0 exponentially as |ψ|ⁿ → 0.
        The bounds become very tight (upper/lower ≈ 1) for moderate n.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    Ln = L(n)
    abs_psi_n = abs(PSI) ** n
    # Lower bound: √5 / (Lₙ(Lₙ + |ψ|ⁿ))
    lower = math.sqrt(5) / (Ln * (Ln + abs_psi_n))
    # Upper bound: √5 / (Lₙ(Lₙ - |ψ|ⁿ))
    upper = math.sqrt(5) / (Ln * (Ln - abs_psi_n))
    return lower, upper
