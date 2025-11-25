from .constants import PHI, PSI


def L(n: int) -> int:
    """Lucas number via closed form."""
    if n < 0:
        raise ValueError("n must be >= 0")
    return int(round(PHI**n + PSI**n))
