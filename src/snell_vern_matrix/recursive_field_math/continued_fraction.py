"""
Continued fraction analysis for Lucas ratios.

A continued fraction represents a number as:
    a₀ + 1/(a₁ + 1/(a₂ + 1/(a₃ + ...)))
    
Often written in compact notation as [a₀; a₁, a₂, a₃, ...].

The golden ratio φ has the simplest continued fraction:
    φ = [1; 1, 1, 1, 1, ...] (all coefficients are 1)
    
This makes φ the "most irrational" number - the hardest to approximate with
rational numbers, as rational approximations converge slowest.

Lucas Ratio Continued Fractions:
The ratio L(n+1)/L(n) has the pattern:
    L(2)/L(1) = 3/1 = [3]
    L(3)/L(2) = 4/3 = [1; 3]
    L(4)/L(3) = 7/4 = [1; 1, 3]
    L(5)/L(4) = 11/7 = [1; 1, 1, 3]
    L(n+1)/L(n) = [1; 1, 1, ..., 1, 3] with (n-2) ones for n ≥ 2

As n → ∞, this approaches [1; 1, 1, 1, ...] = φ.

The pattern shows that Lucas ratios are "almost" the golden ratio but
terminate with a 3 instead of continuing infinitely. This creates a
sequence of rational approximations to φ that improve with each n.

Applications:
- Understanding convergence quality of rational approximations
- Diophantine approximation theory
- Cryptographic entropy based on quasi-periodic sequences
- Educational demonstrations of continued fractions

Mathematical Note:
The convergents of φ's continued fraction [1; 1, 1, 1, ...] are exactly
the ratios F(n+1)/F(n) of consecutive Fibonacci numbers. Lucas ratios
provide an alternative sequence converging to the same limit.
"""

from .lucas import L


def lucas_ratio_cfrac(n: int):
    """
    Return continued fraction metadata for L(n+1)/L(n).
    
    The ratio L(n+1)/L(n) has a continued fraction expansion:
        [1; 1, 1, ..., 1, 3]
        
    where there are (n-2) ones in the middle (for n ≥ 2).
    
    For n = 1: L(2)/L(1) = 3/1 = [3] (special case)
    For n ≥ 2: L(n+1)/L(n) = [1; ones..., 3]
    
    Args:
        n: The index (must be >= 1)
        
    Returns:
        Tuple of (numerator, denominator, metadata) where:
            - numerator: int, L(n+1)
            - denominator: int, L(n)
            - metadata: dict with structure:
                {
                    "head": 1,           # First term of continued fraction
                    "ones": n-2,         # Number of ones in the middle
                    "tail": 3            # Final term
                }
                
    Raises:
        ValueError: If n < 1
        
    Examples:
        >>> num, den, meta = lucas_ratio_cfrac(3)
        >>> num, den
        (4, 3)
        >>> meta
        {'head': 1, 'ones': 1, 'tail': 3}
        
        >>> num, den, meta = lucas_ratio_cfrac(5)
        >>> num, den
        (18, 11)
        >>> meta
        {'head': 1, 'ones': 3, 'tail': 3}
        
    Mathematical Note:
        The continued fraction pattern can be verified by computing:
            [1; 1, ..., 1, 3] = 1 + 1/([1, ..., 1, 3])
                              
        For example, [1; 1, 3] = 1 + 1/(1 + 1/3) = 1 + 1/(4/3) = 1 + 3/4 = 7/4.
        
        This matches L(4)/L(3) = 7/4 ✓
        
        The pattern emerges from the recurrence relation and the limiting
        behavior L(n+1)/L(n) → φ = [1; 1, 1, ...].
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    num, den = L(n + 1), L(n)
    # Number of ones in the continued fraction expansion
    # For n=1: [3] has 0 ones
    # For n=2: [1; 3] has 0 ones  
    # For n=3: [1; 1, 3] has 1 one
    # General formula: max(0, n-2) ones
    ones = max(0, n - 2)
    return (num, den, {"head": 1, "ones": ones, "tail": 3})
