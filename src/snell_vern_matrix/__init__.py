"""
Snell-Vern Hybrid Drive Matrix

A unified engine that combines multiple mathematical and symbolic processing
components for recursive field computations and phase-state tracking.

Components:
- glyph_phase_engine: Symbolic input processing and phase adjustment
- recursive_field_math: Lucas sequences, Fibonacci, and field calculations
- recursive_field: Phyllotaxis pattern mathematics
"""

__version__ = "0.1.0"
__author__ = "wizardaax"

from .drive_matrix import DriveMatrix, MatrixState
from .glyph_phase_engine import GlyphPhaseEngine, PhaseState
from .recursive_field import angle, golden_angle, position, radius
from .recursive_field_math import (
    F,
    GF_F,
    GF_L,
    L,
    PHI,
    PSI,
    ROOT_SCALE,
    egypt_4_7_11,
    lucas_ratio_cfrac,
    r_theta,
    ratio,
    ratio_error_bounds,
    signature_summary,
)

__all__ = [
    # Drive Matrix
    "DriveMatrix",
    "MatrixState",
    # Glyph Phase Engine
    "GlyphPhaseEngine",
    "PhaseState",
    # Recursive Field Math
    "PHI",
    "PSI",
    "ROOT_SCALE",
    "F",
    "L",
    "r_theta",
    "ratio",
    "ratio_error_bounds",
    "lucas_ratio_cfrac",
    "GF_F",
    "GF_L",
    "egypt_4_7_11",
    "signature_summary",
    # Recursive Field
    "golden_angle",
    "radius",
    "angle",
    "position",
    "__version__",
]
