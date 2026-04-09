"""
Cross-repo federation mesh for the Snell-Vern Hybrid Drive Matrix.

Wires the 13-agent orchestration system together across the wizardaax org,
providing task routing, coherence tracking, and load balancing across
repository boundaries.
"""

from .adapters import RepoAdapter, RFMProAdapter, SnellVernAdapter
from .mesh import FederationMesh

__all__ = [
    "FederationMesh",
    "RepoAdapter",
    "RFMProAdapter",
    "SnellVernAdapter",
]
