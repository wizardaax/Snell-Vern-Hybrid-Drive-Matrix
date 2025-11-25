"""
Recursive Field: Mathematical formulas for phyllotaxis patterns.

This module implements the mathematical relationships described in the
"Recursive Field" scientific math song, including radius growth and
angular progression based on the golden angle.
"""

import math


def golden_angle() -> float:
    """
    Return the golden angle in degrees.

    The golden angle is approximately 137.508 degrees and is derived from
    the golden ratio.

    Returns:
        float: The golden angle in degrees
    """
    return 180.0 * (3.0 - math.sqrt(5.0))


def radius(n: int, a: float = 3.0) -> float:
    """
    Calculate the radius for a given index.

    Args:
        n: The index (must be positive)
        a: Scale factor (default: 3.0)

    Returns:
        float: The radius value r_n = a * sqrt(n)

    Raises:
        ValueError: If n is not positive
    """
    if n <= 0:
        raise ValueError("Index n must be positive")
    return a * math.sqrt(n)


def angle(n: int) -> float:
    """
    Calculate the angle for a given index.

    Args:
        n: The index

    Returns:
        float: The angle in degrees, θ_n = n * φ (mod 360)
    """
    phi = golden_angle()
    return (n * phi) % 360.0


def position(n: int, a: float = 3.0) -> tuple[float, float]:
    """
    Calculate the Cartesian position for a given index.

    Args:
        n: The index (must be positive)
        a: Scale factor (default: 3.0)

    Returns:
        tuple: (x, y) coordinates in Cartesian space

    Raises:
        ValueError: If n is not positive
    """
    r = radius(n, a)
    theta_deg = angle(n)
    theta_rad = math.radians(theta_deg)
    x = r * math.cos(theta_rad)
    y = r * math.sin(theta_rad)
    return (x, y)
