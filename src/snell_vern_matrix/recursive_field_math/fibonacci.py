import math

from .constants import PHI, PSI


def F(n: int) -> int:
    """Binet formula rounded to nearest integer (safe for moderate n)."""
    if n < 0:
        raise ValueError("n must be >= 0")
    return int(round((PHI**n - PSI**n) / math.sqrt(5)))
