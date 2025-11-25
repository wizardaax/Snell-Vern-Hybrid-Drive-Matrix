import math

from .constants import PSI
from .lucas import L


def ratio(n: int) -> float:
    """Return L_{n+1}/L_n for n>=1."""
    if n < 1:
        raise ValueError("n must be >= 1")
    Ln, Lnp1 = L(n), L(n + 1)
    return Lnp1 / Ln


def ratio_error_bounds(n: int):
    """Return (lower, upper) bounds for |L_{n+1}/L_n - PHI|.

    Uses stated inequalities.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    Ln = L(n)
    abs_psi_n = abs(PSI) ** n
    lower = math.sqrt(5) / (Ln * (Ln + abs_psi_n))
    upper = math.sqrt(5) / (Ln * (Ln - abs_psi_n))
    return lower, upper
