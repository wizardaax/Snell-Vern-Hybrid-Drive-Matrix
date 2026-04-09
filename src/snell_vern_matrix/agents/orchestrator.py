"""
AgentOrchestrator: Central coordinator for the 13-agent distributed system.

Manages task routing, load balancing, coherence gating (SCE-88),
and state persistence across all specialized agents.
"""

from __future__ import annotations

from typing import Any, Optional

from ..self_model import _lucas_coherence, _validate_coherence
from . import (
    COHERENCE_THRESHOLD,
    MAX_QUEUE_LENGTH,
    TASK_ROUTING_MAP,
    AgentHealth,
    AgentRole,
    BaseAgent,
    Task,
    TaskType,
)
from .agent_01_orchestrator import OrchestratorAgent
from .agent_02_ci_sentinel import CISentinelAgent
from .agent_03_memory_keeper import MemoryKeeperAgent
from .agent_04_constraint_guardian import ConstraintGuardianAgent
from .agent_05_phase_tracker import PhaseTrackerAgent
from .agent_06_lucas_analyst import LucasAnalystAgent
from .agent_07_field_weaver import FieldWeaverAgent
from .agent_08_ternary_logic import TernaryLogicAgent
from .agent_09_self_model_observer import SelfModelObserverAgent
from .agent_10_repo_sync import RepoSyncAgent
from .agent_11_test_validator import TestValidatorAgent
from .agent_12_doc_keeper import DocKeeperAgent
from .agent_13_coherence_monitor import CoherenceMonitorAgent

# Agent registry: ordered list matching the 13-agent spec
_AGENT_CLASSES: list[type[BaseAgent]] = [
    OrchestratorAgent,
    CISentinelAgent,
    MemoryKeeperAgent,
    ConstraintGuardianAgent,
    PhaseTrackerAgent,
    LucasAnalystAgent,
    FieldWeaverAgent,
    TernaryLogicAgent,
    SelfModelObserverAgent,
    RepoSyncAgent,
    TestValidatorAgent,
    DocKeeperAgent,
    CoherenceMonitorAgent,
]


class AgentOrchestrator:
    """
    Central orchestrator managing 13 specialized agents.

    Provides:
    - Task routing based on type → capability mapping
    - Load balancing across agents (prevents overload)
    - SCE-88 coherence gating on agent outputs
    - State persistence for agent health, task completion, and uncertainty
    """

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}
        self._role_map: dict[AgentRole, BaseAgent] = {}
        self._task_log: list[Task] = []
        self._coherence_history: list[float] = []

        # Instantiate all 13 agents
        for idx, cls in enumerate(_AGENT_CLASSES, start=1):
            agent_id = f"agent-{idx:02d}"
            agent = cls(agent_id)
            self._agents[agent_id] = agent
            self._role_map[agent.role] = agent

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def agent_count(self) -> int:
        return len(self._agents)

    @property
    def agents(self) -> dict[str, BaseAgent]:
        return dict(self._agents)

    # ------------------------------------------------------------------
    # Task routing
    # ------------------------------------------------------------------

    def route_task(self, task_type: TaskType, payload: dict[str, Any]) -> Task:
        """
        Create and route a task to the appropriate agent.

        Falls back to load-balanced selection if the primary agent is
        unavailable.

        Raises:
            RuntimeError: If no agent can handle the task.
        """
        task_id = Task.generate_id(task_type.value, str(payload))
        task = Task(task_id=task_id, task_type=task_type, payload=payload)

        # Primary agent for this task type
        primary_role = TASK_ROUTING_MAP.get(task_type)
        if primary_role and primary_role in self._role_map:
            primary = self._role_map[primary_role]
            if primary.state.is_available and primary.can_handle(task_type):
                primary.enqueue(task)
                self._task_log.append(task)
                return task

        # Fallback: find any available agent with matching capability
        for agent in self._agents.values():
            if agent.can_handle(task_type) and agent.state.is_available:
                agent.enqueue(task)
                self._task_log.append(task)
                return task

        raise RuntimeError(f"No available agent for task type {task_type.value}")

    def dispatch(self, task_type_str: str, payload: dict[str, Any]) -> Task:
        """
        Dispatch a task by string type name.

        Convenience wrapper around ``route_task`` that accepts a string
        task type for CLI integration.
        """
        task_type = TaskType(task_type_str)
        return self.route_task(task_type, payload)

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def process_all(self) -> list[dict[str, Any]]:
        """Process all queued tasks across all agents, with coherence gating."""
        results: list[dict[str, Any]] = []
        for agent in self._agents.values():
            while agent.state.workload_queue:
                result = agent.process_next()
                if result is not None:
                    gated = self._coherence_gate(agent, result)
                    results.append(gated)
        return results

    def process_agent(self, agent_id: str) -> Optional[dict[str, Any]]:
        """Process the next task for a specific agent."""
        agent = self._agents.get(agent_id)
        if agent is None:
            return None
        result = agent.process_next()
        if result is not None:
            return self._coherence_gate(agent, result)
        return None

    # ------------------------------------------------------------------
    # Coherence gating (SCE-88)
    # ------------------------------------------------------------------

    def _coherence_gate(
        self, agent: BaseAgent, result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Apply SCE-88 coherence gating to an agent's output.

        Updates the agent's coherence_score and flags outputs that fall
        below the coherence threshold.
        """
        # Compute coherence from the agent's task history
        completed = agent.state.tasks_completed
        failed = agent.state.tasks_failed
        total = completed + failed
        if total > 0:
            raw_score = completed / total
        else:
            raw_score = 0.5

        # Blend with Lucas coherence from the orchestrator's history
        self._coherence_history.append(raw_score)
        lucas_score = _lucas_coherence(self._coherence_history)
        blended = (raw_score + lucas_score) / 2.0

        # Clamp and validate
        blended = max(0.0, min(1.0, blended))
        try:
            _validate_coherence(blended)
        except Exception:
            blended = 0.5

        agent.state.coherence_score = blended

        result["coherence_score"] = blended
        result["coherence_gated"] = blended < COHERENCE_THRESHOLD
        return result

    # ------------------------------------------------------------------
    # Load balancing
    # ------------------------------------------------------------------

    def balance_load(self) -> dict[str, Any]:
        """
        Rebalance workloads across agents.

        Moves tasks from overloaded agents to underloaded peers
        with matching capabilities. Returns a summary of actions taken.
        """
        moves: list[dict[str, str]] = []

        # Update all agent health states
        for agent in self._agents.values():
            agent.update_health()

        overloaded = [
            a for a in self._agents.values() if a.state.health == AgentHealth.OVERLOADED
        ]
        available = [
            a for a in self._agents.values() if a.state.health == AgentHealth.HEALTHY
        ]

        for src in overloaded:
            while (
                src.state.queue_length > MAX_QUEUE_LENGTH // 2
                and src.state.workload_queue
            ):
                task = src.state.workload_queue[-1]
                moved = False
                for dst in available:
                    if dst.can_handle(task.task_type) and dst.state.is_available:
                        src.state.workload_queue.pop()
                        dst.enqueue(task)
                        moves.append(
                            {
                                "task": task.task_id,
                                "from": src.agent_id,
                                "to": dst.agent_id,
                            }
                        )
                        moved = True
                        break
                if not moved:
                    break

        return {"moves": moves, "total_moved": len(moves)}

    # ------------------------------------------------------------------
    # Status & state
    # ------------------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """Return comprehensive orchestrator status."""
        agent_statuses = {}
        for aid, agent in self._agents.items():
            agent.update_health()
            agent_statuses[aid] = agent.state.to_dict()

        total_queued = sum(a.state.queue_length for a in self._agents.values())
        total_completed = sum(a.state.tasks_completed for a in self._agents.values())
        total_failed = sum(a.state.tasks_failed for a in self._agents.values())

        scores = [a.state.coherence_score for a in self._agents.values()]
        avg_coherence = sum(scores) / len(scores) if scores else 0.5

        return {
            "agent_count": self.agent_count,
            "agents": agent_statuses,
            "total_queued": total_queued,
            "total_completed": total_completed,
            "total_failed": total_failed,
            "average_coherence": avg_coherence,
            "task_log_length": len(self._task_log),
        }

    def get_agent_map(self) -> list[dict[str, Any]]:
        """Return a compact map of all agents and their roles."""
        return [
            {
                "id": aid,
                "role": agent.role.value,
                "capabilities": sorted(t.value for t in agent.capabilities),
                "health": agent.state.health.value,
                "queue": agent.state.queue_length,
            }
            for aid, agent in self._agents.items()
        ]
