"""
Glyph Phase Engine

A Python engine that processes symbolic input and adjusts operational phase
based on dynamic delta values. Used for phase-state tracking in recursive models.
"""

__version__ = "0.1.0"
__author__ = "wizardaax"

from .engine import GlyphPhaseEngine, PhaseState

__all__ = ["GlyphPhaseEngine", "PhaseState", "__version__"]
