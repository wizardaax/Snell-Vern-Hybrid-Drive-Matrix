import math

from .constants import PHI, ROOT_SCALE


def r_theta(n: int) -> tuple[float, float]:
    """Radial/Angular pair for index n.
    r_n = 3 * sqrt(n)
    theta_n = n * PHI (radians)
    """
    if n <= 0:
        raise ValueError("n must be >= 1")
    r = ROOT_SCALE * math.sqrt(n)
    theta = n * PHI
    return r, theta
