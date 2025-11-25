"""
Mathematical constants for recursive field computations.

This module defines fundamental constants used throughout the recursive field
mathematics framework, particularly the golden ratio and its conjugate.
"""

import math

# The golden ratio φ (phi): the positive root of x² - x - 1 = 0
# φ = (1 + √5) / 2 ≈ 1.618033988749895
# This is the most irrational number in the sense that its continued fraction
# representation [1; 1, 1, 1, ...] has all coefficients equal to 1, making it
# the hardest to approximate with rationals (slowest convergence).
PHI = (1 + math.sqrt(5)) / 2

# The conjugate of the golden ratio: ψ = 1 - φ = (1 - √5) / 2 ≈ -0.618...
# Properties: φ + ψ = 1, φ × ψ = -1, |ψ| < 1 (ensures convergence in Binet formulas)
# Used in closed-form expressions for Fibonacci and Lucas numbers
PSI = 1 - PHI

# Scaling factor for phyllotaxis radius: r_n = ROOT_SCALE × √n
# The value 3.0 provides visually pleasing spiral spacing in botanical models
ROOT_SCALE = 3.0
