"""
Radial/angular field calculations for phyllotaxis-style patterns.

This module implements the polar coordinate system used in the recursive field,
where positions are defined by:
    r(n) = ROOT_SCALE × √n  (radius grows as square root of index)
    θ(n) = n × φ            (angle in radians, φ being the golden ratio)

The r-theta representation is fundamental to the field structure and differs
from the golden-angle phyllotaxis in the recursive_field.core module.

Key Difference from core.py:
- This module uses θ = n × φ (in radians), where φ ≈ 1.618 radians ≈ 92.7°
- The core module uses θ = n × golden_angle, where golden_angle ≈ 137.5°

Both approaches create spiral patterns, but with different angular spacings.
This module's approach ties the angular progression directly to the golden
ratio value itself, creating a mathematical connection between the field
structure and the underlying φ constant.

Applications:
- Entropy field generation for cryptographic purposes
- Mathematical pattern analysis distinct from botanical phyllotaxis
- Golden ratio-based indexing systems
"""

import math

from .constants import PHI, ROOT_SCALE


def r_theta(n: int) -> tuple[float, float]:
    """
    Compute radial and angular coordinates for field index n.
    
    The field uses a polar coordinate system where:
        r(n) = ROOT_SCALE × √n  (default: 3√n)
        θ(n) = n × φ (in radians)
    
    This creates a spiral pattern where:
    - Radius increases as the square root (spacing increases outward)
    - Angle increments by φ ≈ 1.618 radians ≈ 92.7° per step
    
    Args:
        n: The field index (must be >= 1)
        
    Returns:
        Tuple of (radius, theta) where:
            - radius: float, the radial distance from origin
            - theta: float, the angle in radians (not modulo 2π)
            
    Raises:
        ValueError: If n < 1
        
    Examples:
        >>> r, theta = r_theta(1)
        >>> r
        3.0
        >>> r, theta = r_theta(4)
        >>> r
        6.0
        >>> r, theta = r_theta(9)
        >>> r
        9.0
        
    Mathematical Note:
        The √n radius growth ensures constant density in the radial direction
        when combined with the angular progression. This is because the area
        of an annulus grows linearly with n, and we want constant points per
        unit area.
        
        The use of φ (instead of golden angle) creates approximately 360°/92.7° ≈ 3.88
        spirals, which is close to but distinct from the Fibonacci spiral patterns.
    """
    if n <= 0:
        raise ValueError("n must be >= 1")
    # Radius: square root growth for constant density
    r = ROOT_SCALE * math.sqrt(n)
    # Angle: golden ratio progression (in radians, not degrees)
    theta = n * PHI
    return r, theta
