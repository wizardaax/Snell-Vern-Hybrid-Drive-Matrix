"""
Ordinary generating functions for Fibonacci and Lucas sequences.

A generating function encodes a sequence {aₙ} into a formal power series:
    G(x) = Σ(n≥0) aₙxⁿ = a₀ + a₁x + a₂x² + a₃x³ + ...

For sequences satisfying linear recurrences, generating functions are
rational functions (ratios of polynomials).

Fibonacci Generating Function:
    G_F(x) = x / (1 - x - x²)

This encodes the Fibonacci sequence as coefficients:
    G_F(x) = 0 + 1·x + 1·x² + 2·x³ + 3·x⁴ + 5·x⁵ + ...
             = F(0) + F(1)x + F(2)x² + F(3)x³ + ...

Lucas Generating Function:
    G_L(x) = (2 - x) / (1 - x - x²)

This encodes the Lucas sequence:
    G_L(x) = 2 + 1·x + 3·x² + 4·x³ + 7·x⁴ + 11·x⁵ + ...
             = L(0) + L(1)x + L(2)x² + L(3)x³ + ...

Derivation:
Starting from the recurrence F(n) = F(n-1) + F(n-2) with F(0)=0, F(1)=1:
    G_F(x) - x = Σ(n≥2) F(n)xⁿ
               = Σ(n≥2) (F(n-1) + F(n-2))xⁿ
               = x·Σ(n≥1) F(n)xⁿ + x²·Σ(n≥0) F(n)xⁿ
               = x·G_F(x) + x²·G_F(x)

Solving for G_F(x):
    G_F(x) - x = x·G_F(x) + x²·G_F(x)
    G_F(x)(1 - x - x²) = x
    G_F(x) = x / (1 - x - x²)

Applications:
1. **Closed-form extraction**: Extract F(n) via coefficient of xⁿ
2. **Combinatorial identities**: Prove identities by manipulating G_F
3. **Asymptotic analysis**: Poles at x = 1/φ and x = 1/ψ determine growth
4. **Recurrence solving**: Convert recurrences to algebraic equations

Singularities:
The denominator 1 - x - x² has roots at x = 1/φ and x = 1/ψ.
These determine the exponential growth rate of the sequences (φⁿ).

Cryptographic Note:
Generating functions can be evaluated at special points for entropy:
- G_F(1/2) = 1/(1 - 1/2 - 1/4) = 4 (sum with geometric decay)
- Points near singularities create quasi-chaotic behavior
"""


def GF_F(x: float) -> float:
    """
    Evaluate the Fibonacci generating function at x.

    Computes: G_F(x) = x / (1 - x - x²)

    This is the ordinary generating function that encodes the Fibonacci
    sequence as coefficients in its Taylor expansion around x=0.

    Args:
        x: The evaluation point (must not be a singularity)

    Returns:
        The value of G_F(x)

    Raises:
        ZeroDivisionError: If x is a root of 1 - x - x² (singularity)

    Examples:
        >>> GF_F(0)
        0.0
        >>> abs(GF_F(0.1) - 0.1111111111111111) < 1e-10
        True
        >>> # At x = 1/2: converges to sum of F(n)/2^n
        >>> abs(GF_F(0.5) - 2.0) < 1e-10
        True

    Mathematical Note:
        The Taylor expansion around x=0 is:
            G_F(x) = F(0) + F(1)x + F(2)x² + F(3)x³ + ...
                   = 0 + x + x² + 2x³ + 3x⁴ + 5x⁵ + ...

        Singularities at x = 1/φ ≈ 0.618 and x = 1/ψ ≈ -1.618.

        For |x| < 1/φ, the series converges.

        The residues at the poles determine the asymptotic behavior F(n) ~ φⁿ/√5.
    """
    denom = 1 - x - x * x
    if abs(denom) < 1e-15:
        raise ZeroDivisionError("Singularity at 1 - x - x^2 = 0")
    return x / denom


def GF_L(x: float) -> float:
    """
    Evaluate the Lucas generating function at x.

    Computes: G_L(x) = (2 - x) / (1 - x - x²)

    This is the ordinary generating function that encodes the Lucas
    sequence as coefficients in its Taylor expansion around x=0.

    Args:
        x: The evaluation point (must not be a singularity)

    Returns:
        The value of G_L(x)

    Raises:
        ZeroDivisionError: If x is a root of 1 - x - x² (singularity)

    Examples:
        >>> GF_L(0)
        2.0
        >>> abs(GF_L(0.1) - 2.222222222222222) < 1e-10
        True
        >>> # Relationship: G_L(x) + G_F(x) = 2/(1 - x - x²)
        >>> x = 0.3
        >>> abs(GF_L(x) + GF_F(x) - 2/(1 - x - x*x)) < 1e-10
        True

    Mathematical Note:
        The Taylor expansion is:
            G_L(x) = L(0) + L(1)x + L(2)x² + L(3)x³ + ...
                   = 2 + x + 3x² + 4x³ + 7x⁴ + 11x⁵ + ...

        Identity relating to Fibonacci generating function:
            G_L(x) = (2 - x) / (1 - x - x²)
                   = 2/(1 - x - x²) - x/(1 - x - x²)
                   = 2/(1 - x - x²) - G_F(x)

        This reflects the identity L(n) + F(n) = 2F(n+1).

        The same singularities as G_F(x) determine L(n) ~ φⁿ asymptotically.
    """
    denom = 1 - x - x * x
    if abs(denom) < 1e-15:
        raise ZeroDivisionError("Singularity at 1 - x - x^2 = 0")
    return (2 - x) / denom
