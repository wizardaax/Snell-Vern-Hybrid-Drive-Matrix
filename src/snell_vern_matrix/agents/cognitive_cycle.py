"""
CognitiveCycle: goal-driven driver above the AgentOrchestrator.

Takes a natural-language goal, decomposes it into TaskTypes via keyword
heuristics, dispatches the resulting tasks through the orchestrator,
synthesises the results, and (optionally) iterates.

This is the layer that turns the 13-agent fleet from a slash-command
dispatch system into a self-driving cognitive loop.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from . import TaskType
from .orchestrator import AgentOrchestrator

# Heraldic alphabet for crest stamps. 16 glyphs → one nibble each.
# Chosen so a stamp is human-readable, copy-pasteable, and survives
# ASCII-only transports (no fragile non-BMP codepoints).
_CREST_GLYPHS: str = "△▽◆●◇◯⬢⬡✦✧✪✱☉☽⚙⚛"
assert len(_CREST_GLYPHS) == 16

# Keyword → TaskType map. Order matters only for readability.
_KEYWORD_MAP: dict[str, TaskType] = {
    "test": TaskType.TESTING,
    "regression": TaskType.TESTING,
    # "validat" routes to CONSTRAINT (agent-04 Constraint Guardian) — semantically
    # validation is invariant-checking, not running test suites.
    "validat": TaskType.CONSTRAINT,
    "memory": TaskType.MEMORY,
    "remember": TaskType.MEMORY,
    "recall": TaskType.MEMORY,
    "constrain": TaskType.CONSTRAINT,
    "guard": TaskType.CONSTRAINT,
    "phase": TaskType.PHASE,
    "lucas": TaskType.MATH,
    "fibonacci": TaskType.MATH,
    "math": TaskType.MATH,
    "formula": TaskType.MATH,
    "field": TaskType.FIELD,
    "spiral": TaskType.FIELD,
    "ternary": TaskType.TERNARY,
    "logic": TaskType.TERNARY,
    "observ": TaskType.OBSERVATION,
    "self": TaskType.OBSERVATION,
    "audit": TaskType.OBSERVATION,
    "sync": TaskType.SYNC,
    "repo": TaskType.SYNC,
    "doc": TaskType.DOCUMENTATION,
    "readme": TaskType.DOCUMENTATION,
    "ci": TaskType.CI_HEALTH,
    "build": TaskType.CI_HEALTH,
    "coheren": TaskType.COHERENCE,
}

# Tasks always added: observe before, recall corpus mid-cycle, monitor coherence after.
# MEMORY is included by default so every cycle grounds itself in the corpus —
# you can't reason about something the substrate doesn't know about.
_BOOKEND_PRE: TaskType = TaskType.OBSERVATION
_DEFAULT_RECALL: TaskType = TaskType.MEMORY
_BOOKEND_POST: TaskType = TaskType.COHERENCE


def _crest_stamp(payload: bytes, length: int = 8) -> str:
    """Generate a deterministic heraldic stamp from arbitrary bytes.

    SHA-256 → first ``length*4`` bits → glyphs from ``_CREST_GLYPHS``.
    Two runs over the same payload produce the same stamp. A future
    reader can re-compute the stamp to verify a log entry hasn't drifted.
    """
    digest = hashlib.sha256(payload).digest()
    bits = int.from_bytes(digest[: (length * 4 + 7) // 8 + 1], "big")
    glyphs = []
    for _ in range(length):
        glyphs.append(_CREST_GLYPHS[bits & 0xF])
        bits >>= 4
    return "".join(reversed(glyphs))


@dataclass
class CycleResult:
    """One pass of the cognitive cycle."""

    goal: str
    task_types: list[TaskType]
    results: list[dict[str, Any]] = field(default_factory=list)
    average_coherence: float = 0.0
    gated_count: int = 0
    timestamp: float = field(default_factory=time.time)
    crest: str = ""
    sha256: str = ""

    def summary(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "tasks_dispatched": len(self.task_types),
            "results_returned": len(self.results),
            "average_coherence": self.average_coherence,
            "gated_count": self.gated_count,
            "task_types": [t.value for t in self.task_types],
            "timestamp": self.timestamp,
            "crest": self.crest,
            "sha256": self.sha256,
        }

    def to_log(self) -> dict[str, Any]:
        """Full serialisable record — what gets written to disk."""
        return {
            "goal": self.goal,
            "task_types": [t.value for t in self.task_types],
            "results": self.results,
            "average_coherence": self.average_coherence,
            "gated_count": self.gated_count,
            "timestamp": self.timestamp,
            "timestamp_iso": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.timestamp)
            ),
            "crest": self.crest,
            "sha256": self.sha256,
        }

    def stamp(self) -> None:
        """Compute crest + sha256 from the current contents. Idempotent."""
        # Sign over a stable, ordered subset of fields. Excludes crest/sha256
        # themselves so the stamp is reproducible over the *content*.
        payload = json.dumps(
            {
                "goal": self.goal,
                "task_types": [t.value for t in self.task_types],
                "results": self.results,
                "average_coherence": self.average_coherence,
                "gated_count": self.gated_count,
                "timestamp": self.timestamp,
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
        self.sha256 = hashlib.sha256(payload).hexdigest()
        self.crest = _crest_stamp(payload)


def verify_log(record: dict[str, Any]) -> bool:
    """Recompute the stamp from a log dict and verify it matches.

    Future-proofing: a researcher in 2125 reading a cycle log can verify
    its integrity with stdlib only — no key servers, no external trust roots.
    """
    if not isinstance(record, dict):
        return False
    expected_sha = record.get("sha256")
    expected_crest = record.get("crest")
    if not expected_sha or not expected_crest:
        return False
    payload = json.dumps(
        {
            "goal": record.get("goal"),
            "task_types": record.get("task_types", []),
            "results": record.get("results", []),
            "average_coherence": record.get("average_coherence", 0.0),
            "gated_count": record.get("gated_count", 0),
            "timestamp": record.get("timestamp", 0.0),
        },
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")
    return (
        hashlib.sha256(payload).hexdigest() == expected_sha
        and _crest_stamp(payload) == expected_crest
    )


class CognitiveCycle:
    """Drives the AgentOrchestrator through a goal-pursuit loop.

    When constructed with a ``log_dir``, every cycle is stamped with a
    SHA-256 + heraldic crest and written as JSON to disk. The on-disk
    format depends on stdlib only and can be re-verified with
    :func:`verify_log` at any future date.
    """

    def __init__(
        self,
        orchestrator: Optional[AgentOrchestrator] = None,
        log_dir: Optional[str] = None,
    ) -> None:
        self.orch = orchestrator or AgentOrchestrator()
        self.history: list[CycleResult] = []
        self.log_dir: Optional[str] = log_dir
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

    def _write_log(self, result: CycleResult) -> Optional[str]:
        if not self.log_dir:
            return None
        # Filename: <ISO-timestamp>__<crest>.json
        # The crest in the filename lets you visually scan a directory of
        # cycles for tampered or duplicated entries.
        safe_iso = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(result.timestamp))
        path = os.path.join(self.log_dir, f"{safe_iso}__{result.crest}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.to_log(), f, indent=2, ensure_ascii=False)
        return path

    def _derive_phase(self) -> str:
        """Derive a GlyphPhaseEngine-style phase state from cycle history.

        Mirrors the Xova-side PhaseState enum so the Python cycle and the
        TypeScript runtime agree on what 'phase' means.
        """
        if not self.history:
            return "INITIAL"
        last = self.history[-1]
        # If the most recent cycle had any gated outputs, that's an ERROR phase.
        if last.gated_count > 0:
            return "ERROR"
        avg = last.average_coherence
        if avg >= 0.7:
            return "STABILIZED"
        if avg >= 0.5:
            return "DELTA_ADJUSTMENT"
        return "PROCESSING"

    def decompose(self, goal: str) -> list[TaskType]:
        """Map a goal string to TaskTypes via keyword heuristics.

        Always includes:
          - OBSERVATION first (self-model snapshot)
          - MEMORY mid-cycle (corpus recall — every goal grounds in substrate)
          - COHERENCE last (SCE-88 gate)
        """
        goal_lower = goal.lower()
        matched: list[TaskType] = [_BOOKEND_PRE]
        seen: set[TaskType] = {_BOOKEND_PRE}
        # Memory recall is always included — corpus grounding is non-negotiable.
        matched.append(_DEFAULT_RECALL)
        seen.add(_DEFAULT_RECALL)
        for kw, tt in _KEYWORD_MAP.items():
            if kw in goal_lower and tt not in seen:
                matched.append(tt)
                seen.add(tt)
        if _BOOKEND_POST not in seen:
            matched.append(_BOOKEND_POST)
        return matched

    def run(self, goal: str) -> CycleResult:
        """Run one cognitive cycle: decompose → dispatch → process → synthesise."""
        task_types = self.decompose(goal)
        result = CycleResult(goal=goal, task_types=task_types)

        goal_lower = goal.lower()
        for tt in task_types:
            payload: dict[str, Any] = {"goal": goal, "step": tt.value}
            # MEMORY → corpus-search the substrate using the goal.
            if tt is TaskType.MEMORY:
                payload["action"] = "search"
                payload["query"] = goal
            # MATH → Lucas/Fibonacci analysis. Goal phrasing picks the action.
            elif tt is TaskType.MATH:
                if any(k in goal_lower for k in ("converg", "phi", "golden", "ratio")):
                    payload["action"] = "convergence"
                    payload["n"] = 20
                else:
                    payload["action"] = "sequence"
                    payload["n"] = 12
            # FIELD → r=a√n, θ=nφ phyllotaxis. "analysis" wins if goal mentions
            # angle/radius specifically; otherwise return the spiral points.
            elif tt is TaskType.FIELD:
                if any(k in goal_lower for k in ("angle", "radius", "single", "specific")):
                    payload["action"] = "analysis"
                    payload["n"] = 12
                else:
                    payload["action"] = "field"
                    payload["n"] = 12
            # TESTING → actually run pytest on the target repo. Default repo is
            # the Snell-Vern repo itself (the agent's own home), so the cycle
            # validates its own substrate by default.
            elif tt is TaskType.TESTING:
                payload["action"] = "run"
                # The agent has its own default repo path; cycle doesn't need
                # to inject one unless the user supplies it via goal context.
            # CONSTRAINT → exercise SCE-88 invariants. We feed valid mid-range
            # values so the agent's validators actually run their checks. If
            # the framework's coherence / uncertainty / ternary-balance invariants
            # ever break, this is the agent that surfaces it.
            elif tt is TaskType.CONSTRAINT:
                payload["coherence_score"] = 0.5
                payload["uncertainty"] = 0.5
                payload["ternary_balance"] = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
            # PHASE → derive a phase state from cycle history. Mirrors the
            # GlyphPhaseEngine state machine in Xova (INITIAL → PROCESSING →
            # DELTA_ADJUSTMENT → STABILIZED / ERROR).
            elif tt is TaskType.PHASE:
                payload["phase_state"] = self._derive_phase()
            # OBSERVATION → SelfModel.observe(goal) runs GlyphPhaseEngine +
            # Lucas math + golden-angle field on the goal as input pattern.
            # Returns delta, uncertainty, coherence — real cognitive work.
            elif tt is TaskType.OBSERVATION:
                payload["action"] = "observe"
                payload["pattern"] = goal
            # TERNARY → evaluate stability of the balanced ternary equilibrium
            # (1/3, 1/3, 1/3). Returns STABLE / UNSTABLE / CRITICAL classification
            # via the SCE-88 ternary balance math.
            elif tt is TaskType.TERNARY:
                payload["action"] = "evaluate"
                payload["ternary_balance"] = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
            # SYNC → real `git status --porcelain` across all wizardaax repos.
            # Reports clean/dirty count + ahead/behind origin.
            elif tt is TaskType.SYNC:
                payload["action"] = "status"
            # DOCUMENTATION → audit docstring coverage + README status of the
            # Snell-Vern repo. Real ast-walk, real numbers.
            elif tt is TaskType.DOCUMENTATION:
                payload["action"] = "audit"
            # CI_HEALTH → discover .github/workflows/ across all wizardaax repos.
            # No network — pure on-disk presence audit.
            elif tt is TaskType.CI_HEALTH:
                payload["action"] = "audit"
            # COHERENCE → feed the Coherence Monitor the trend of average
            # coherence from the LAST 12 cycles. Lets it detect long-term drift.
            elif tt is TaskType.COHERENCE:
                payload["action"] = "check"
                payload["agent_scores"] = [
                    float(c.average_coherence) for c in self.history[-12:]
                ]
            try:
                self.orch.route_task(tt, payload)
            except RuntimeError:
                continue

        result.results = self.orch.process_all()
        if result.results:
            scores = [r.get("coherence_score", 0.5) for r in result.results]
            result.average_coherence = sum(scores) / len(scores)
            result.gated_count = sum(1 for r in result.results if r.get("coherence_gated"))

        result.stamp()
        self._write_log(result)
        self.history.append(result)
        return result

    def loop(self, goal: str, max_cycles: int = 3) -> list[CycleResult]:
        """Run multiple cycles until coherence stabilises or max_cycles reached."""
        results: list[CycleResult] = []
        for _ in range(max_cycles):
            r = self.run(goal)
            results.append(r)
            # Stable cycle: coherence above threshold AND no gated outputs
            if r.average_coherence >= 0.7 and r.gated_count == 0:
                break
        return results
