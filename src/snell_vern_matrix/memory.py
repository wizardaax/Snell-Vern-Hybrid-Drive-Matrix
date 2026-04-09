"""
Deterministic Associative Memory Module for Snell-Vern Hybrid Drive Matrix.

Provides a ``FieldMemory`` class that stores, recalls, decays, prunes, and
persists associative records using Lucas-phi hashing, golden-angle proximity
scoring, ternary logic gating, and SCE-88 constraint validation.

Thread-safe, deterministic, zero new runtime dependencies.
"""

from __future__ import annotations

import json
import math
import threading
import time
from typing import Any, Optional

from recursive_field_math import L

from .recursive_field import golden_angle

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PRIME = 104_729  # Large prime for Lucas-phi modular mapping
_GOLDEN_ANGLE_DEG = golden_angle()  # ≈ 137.508°
_GOLDEN_ANGLE_RAD = math.radians(_GOLDEN_ANGLE_DEG)

# SCE-88 constraints (reuse definitions from self_model)
_SCE88_COHERENCE_BOUNDS = (0.0, 1.0)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# Lucas-phi deterministic hashing
# ---------------------------------------------------------------------------


def lucas_phi_hash(key: str) -> int:
    """Deterministic hash using Lucas-phi function.

    Maps *key* to a non-negative integer via the Lucas sequence modulo
    a large prime.  The mapping is:

    1. Convert each character to its ordinal value.
    2. Accumulate a Lucas-number index ``n`` from the ordinals.
    3. Return ``L(n mod 30) mod _PRIME``.

    The index is capped at 30 so that L(n) remains fast and bounded.
    """
    n = 0
    for i, ch in enumerate(key):
        n += ord(ch) * (i + 1)
    # Cap the Lucas index at 30 to keep values deterministic and bounded
    idx = n % 30
    return int(L(idx)) % _PRIME


# ---------------------------------------------------------------------------
# SCE-88 data validation
# ---------------------------------------------------------------------------


def validate_sce88(data: dict[str, Any]) -> bool:
    """Validate a data dict against SCE-88 constraint topology.

    Rules applied:
    - Must be a non-empty ``dict``.
    - No value may be ``None``.
    - Numeric values must be finite.

    Returns ``True`` when valid, ``False`` otherwise.
    """
    if not isinstance(data, dict) or not data:
        return False
    for v in data.values():
        if v is None:
            return False
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return False
    return True


# ---------------------------------------------------------------------------
# Golden-angle proximity scoring
# ---------------------------------------------------------------------------


def _proximity_score(hash_a: int, hash_b: int) -> float:
    """Compute proximity between two Lucas-phi hashes.

    Uses golden-angle spacing projected through a ternary-logic gate
    (three angular phases offset by 120°) to yield a score in [0, 1].
    """
    diff = abs(hash_a - hash_b)
    # Normalise difference into [0, 1) via prime modulus
    norm = (diff % _PRIME) / _PRIME
    # Golden-angle angular mapping
    theta = norm * 2.0 * math.pi
    # Ternary-logic gate: average of three angular projections
    t0 = math.cos(theta)
    t1 = math.cos(theta + _GOLDEN_ANGLE_RAD)
    t2 = math.cos(theta + 2.0 * _GOLDEN_ANGLE_RAD)
    raw = (t0 + t1 + t2) / 3.0
    # Map from [-1, 1] → [0, 1]
    return _clamp((raw + 1.0) / 2.0, 0.0, 1.0)


# ---------------------------------------------------------------------------
# FieldMemory
# ---------------------------------------------------------------------------


class FieldMemory:
    """Deterministic associative memory backed by Lucas-phi addressing.

    Parameters
    ----------
    capacity:
        Maximum number of records (default 1024).
    decay_rate:
        Exponential decay constant applied per :meth:`decay` tick
        (default 0.05).
    coherence_threshold:
        Minimum coherence for a record to survive :meth:`prune`
        (default 0.1).
    """

    def __init__(
        self,
        capacity: int = 1024,
        decay_rate: float = 0.05,
        coherence_threshold: float = 0.1,
    ) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        if not (0.0 <= decay_rate <= 1.0):
            raise ValueError("decay_rate must be in [0.0, 1.0]")
        if not (0.0 <= coherence_threshold <= 1.0):
            raise ValueError("coherence_threshold must be in [0.0, 1.0]")

        self._lock = threading.Lock()
        self._records: dict[str, dict[str, Any]] = {}
        self.capacity = capacity
        self.decay_rate = decay_rate
        self.coherence_threshold = coherence_threshold
        self.last_tick: float = time.monotonic()

    # -- core operations ---------------------------------------------------

    def store(self, key: str, data: dict[str, Any], coherence: float) -> bool:
        """Store a record in memory.

        Parameters
        ----------
        key:
            Unique string identifier for the record.
        data:
            Payload dictionary.  Must pass SCE-88 validation.
        coherence:
            Initial coherence score in [0.0, 1.0].

        Returns
        -------
        bool
            ``True`` if stored successfully, ``False`` otherwise.
        """
        if not key or not isinstance(key, str):
            return False
        lo, hi = _SCE88_COHERENCE_BOUNDS
        if not (lo <= coherence <= hi):
            return False
        if not validate_sce88(data):
            return False

        h = lucas_phi_hash(key)
        now = time.monotonic()

        with self._lock:
            # If at capacity and key is new, prune first
            if key not in self._records and len(self._records) >= self.capacity:
                self._prune_unlocked()
                # If still at capacity, cannot store
                if len(self._records) >= self.capacity:
                    return False

            self._records[key] = {
                "hash": h,
                "data": dict(data),
                "coherence_score": coherence,
                "timestamp": now,
                "usage_count": 0,
            }
            return True

    def recall(self, query: str, threshold: float = 0.5) -> list[dict[str, Any]]:
        """Recall records matching *query*.

        Uses golden-angle spacing and ternary logic to compute proximity
        scores.  Results are sorted by ``coherence × proximity`` and
        filtered by *threshold*.

        Parameters
        ----------
        query:
            Query string.
        threshold:
            Minimum ``coherence × proximity`` for inclusion (default 0.5).

        Returns
        -------
        list[dict]
            Matching records with ``key``, ``data``, ``score``, and
            ``coherence_score`` fields.
        """
        q_hash = lucas_phi_hash(query)
        results: list[dict[str, Any]] = []

        with self._lock:
            for key, rec in self._records.items():
                prox = _proximity_score(q_hash, rec["hash"])
                combined = rec["coherence_score"] * prox
                if combined >= threshold:
                    rec["usage_count"] += 1
                    results.append(
                        {
                            "key": key,
                            "data": dict(rec["data"]),
                            "score": combined,
                            "coherence_score": rec["coherence_score"],
                        }
                    )

        results.sort(key=lambda r: r["score"], reverse=True)
        return results

    def decay(self) -> int:
        """Apply exponential decay to idle records.

        Records with higher ``usage_count`` decay more slowly.
        Returns the number of records whose coherence dropped.
        """
        now = time.monotonic()
        with self._lock:
            dt = now - self.last_tick
            self.last_tick = now
            count = 0
            for rec in self._records.values():
                # Dampen decay by usage count
                effective_rate = self.decay_rate / (1.0 + rec["usage_count"])
                factor = math.exp(-effective_rate * dt)
                old = rec["coherence_score"]
                rec["coherence_score"] = _clamp(old * factor, 0.0, 1.0)
                if rec["coherence_score"] < old:
                    count += 1
            return count

    def prune(self) -> int:
        """Remove records below coherence threshold or beyond capacity.

        Uses LRU + coherence-weighted eviction.  Returns the number of
        records removed.
        """
        with self._lock:
            return self._prune_unlocked()

    def _prune_unlocked(self) -> int:
        """Internal prune without acquiring the lock."""
        removed = 0
        # Phase 1: remove records below coherence threshold
        below = [
            k
            for k, rec in self._records.items()
            if rec["coherence_score"] < self.coherence_threshold
        ]
        for k in below:
            del self._records[k]
            removed += 1

        # Phase 2: if still over capacity, evict lowest-scoring records
        if len(self._records) > self.capacity:
            # Sort by (coherence * (1 + usage_count)), ascending → evict lowest
            ranked = sorted(
                self._records.items(),
                key=lambda kv: kv[1]["coherence_score"] * (1 + kv[1]["usage_count"]),
            )
            while len(self._records) > self.capacity and ranked:
                k, _ = ranked.pop(0)
                del self._records[k]
                removed += 1

        return removed

    # -- persistence -------------------------------------------------------

    def persist(self, path: str) -> None:
        """Write memory state to *path* as deterministic JSON."""
        with self._lock:
            payload = {
                "capacity": self.capacity,
                "decay_rate": self.decay_rate,
                "coherence_threshold": self.coherence_threshold,
                "records": {
                    k: {
                        "hash": rec["hash"],
                        "data": rec["data"],
                        "coherence_score": rec["coherence_score"],
                        "timestamp": rec["timestamp"],
                        "usage_count": rec["usage_count"],
                    }
                    for k, rec in sorted(self._records.items())
                },
            }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, sort_keys=True, indent=2)

    def load(self, path: str) -> None:
        """Load memory state from a JSON file at *path*."""
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)

        with self._lock:
            self.capacity = int(payload["capacity"])
            self.decay_rate = float(payload["decay_rate"])
            self.coherence_threshold = float(payload["coherence_threshold"])
            self._records = {}
            for k, rec in payload.get("records", {}).items():
                self._records[k] = {
                    "hash": int(rec["hash"]),
                    "data": dict(rec["data"]),
                    "coherence_score": float(rec["coherence_score"]),
                    "timestamp": float(rec["timestamp"]),
                    "usage_count": int(rec["usage_count"]),
                }

    # -- introspection -----------------------------------------------------

    @property
    def size(self) -> int:
        """Number of records currently stored."""
        with self._lock:
            return len(self._records)

    def keys(self) -> list[str]:
        """Return a sorted list of record keys."""
        with self._lock:
            return sorted(self._records.keys())

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._records

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """Get a single record by exact key, or ``None``."""
        with self._lock:
            rec = self._records.get(key)
            if rec is None:
                return None
            return {
                "key": key,
                "data": dict(rec["data"]),
                "coherence_score": rec["coherence_score"],
                "usage_count": rec["usage_count"],
            }
