"""
Distributed agent orchestration for the Snell-Vern Hybrid Drive Matrix.

Provides 13 specialized agents coordinated by an AgentOrchestrator,
with SCE-88 coherence gating and Lucas 4-7-11 load balancing.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class AgentRole(Enum):
    """Roles for the 13 specialized agents."""

    ORCHESTRATOR = "orchestrator"
    CI_SENTINEL = "ci_sentinel"
    MEMORY_KEEPER = "memory_keeper"
    CONSTRAINT_GUARDIAN = "constraint_guardian"
    PHASE_TRACKER = "phase_tracker"
    LUCAS_ANALYST = "lucas_analyst"
    FIELD_WEAVER = "field_weaver"
    TERNARY_LOGIC = "ternary_logic"
    SELF_MODEL_OBSERVER = "self_model_observer"
    REPO_SYNC = "repo_sync"
    TEST_VALIDATOR = "test_validator"
    DOC_KEEPER = "doc_keeper"
    COHERENCE_MONITOR = "coherence_monitor"


class TaskType(Enum):
    """Types of tasks the agent system handles."""

    COORDINATION = "coordination"
    CI_HEALTH = "ci_health"
    MEMORY = "memory"
    CONSTRAINT = "constraint"
    PHASE = "phase"
    MATH = "math"
    FIELD = "field"
    TERNARY = "ternary"
    OBSERVATION = "observation"
    SYNC = "sync"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    COHERENCE = "coherence"


class AgentHealth(Enum):
    """Health states for agents."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OVERLOADED = "overloaded"
    OFFLINE = "offline"


class TaskStatus(Enum):
    """Status of a queued task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Mapping from TaskType to the primary AgentRole that handles it
TASK_ROUTING_MAP: dict[TaskType, AgentRole] = {
    TaskType.COORDINATION: AgentRole.ORCHESTRATOR,
    TaskType.CI_HEALTH: AgentRole.CI_SENTINEL,
    TaskType.MEMORY: AgentRole.MEMORY_KEEPER,
    TaskType.CONSTRAINT: AgentRole.CONSTRAINT_GUARDIAN,
    TaskType.PHASE: AgentRole.PHASE_TRACKER,
    TaskType.MATH: AgentRole.LUCAS_ANALYST,
    TaskType.FIELD: AgentRole.FIELD_WEAVER,
    TaskType.TERNARY: AgentRole.TERNARY_LOGIC,
    TaskType.OBSERVATION: AgentRole.SELF_MODEL_OBSERVER,
    TaskType.SYNC: AgentRole.REPO_SYNC,
    TaskType.TESTING: AgentRole.TEST_VALIDATOR,
    TaskType.DOCUMENTATION: AgentRole.DOC_KEEPER,
    TaskType.COHERENCE: AgentRole.COHERENCE_MONITOR,
}

# Maximum workload queue length before an agent is considered overloaded
MAX_QUEUE_LENGTH = 10

# Coherence threshold for SCE-88 gating
COHERENCE_THRESHOLD = 0.3


@dataclass
class Task:
    """A task to be processed by an agent."""

    task_id: str
    task_type: TaskType
    payload: dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[dict[str, Any]] = None
    assigned_agent: Optional[str] = None
    created_at: float = field(default_factory=time.monotonic)

    @staticmethod
    def generate_id(task_type: str, payload: str) -> str:
        """Generate a deterministic task ID from type and payload."""
        raw = f"{task_type}:{payload}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass
class AgentState:
    """Persistent state for a single agent."""

    agent_id: str
    role: AgentRole
    capability_set: frozenset[TaskType]
    health: AgentHealth = AgentHealth.HEALTHY
    coherence_score: float = 0.5
    tasks_completed: int = 0
    tasks_failed: int = 0
    workload_queue: list[Task] = field(default_factory=list)

    @property
    def queue_length(self) -> int:
        return len(self.workload_queue)

    @property
    def is_available(self) -> bool:
        return (
            self.health in (AgentHealth.HEALTHY, AgentHealth.DEGRADED)
            and self.queue_length < MAX_QUEUE_LENGTH
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialise agent state to a JSON-compatible dict."""
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "health": self.health.value,
            "coherence_score": self.coherence_score,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "queue_length": self.queue_length,
            "capabilities": sorted(t.value for t in self.capability_set),
        }


class BaseAgent:
    """
    Base class for all 13 specialized agents.

    Each agent has a role, a set of task types it can handle,
    and processes tasks through its ``execute`` method.
    """

    role: AgentRole = AgentRole.ORCHESTRATOR
    capabilities: frozenset[TaskType] = frozenset()

    def __init__(self, agent_id: str) -> None:
        self.state = AgentState(
            agent_id=agent_id,
            role=self.role,
            capability_set=self.capabilities,
        )

    @property
    def agent_id(self) -> str:
        return self.state.agent_id

    def can_handle(self, task_type: TaskType) -> bool:
        """Return True if this agent can process the given task type."""
        return task_type in self.capabilities

    def execute(self, task: Task) -> dict[str, Any]:
        """
        Execute a task and return the result.

        Subclasses should override this to provide specialised logic.
        """
        return {"status": "completed", "agent": self.agent_id, "task": task.task_id}

    def enqueue(self, task: Task) -> bool:
        """Add a task to this agent's workload queue. Returns False if full."""
        if not self.state.is_available:
            return False
        task.assigned_agent = self.agent_id
        self.state.workload_queue.append(task)
        return True

    def process_next(self) -> Optional[dict[str, Any]]:
        """Process the next task in the queue."""
        if not self.state.workload_queue:
            return None
        task = self.state.workload_queue.pop(0)
        task.status = TaskStatus.RUNNING
        try:
            result = self.execute(task)
            task.status = TaskStatus.COMPLETED
            task.result = result
            self.state.tasks_completed += 1
            return result
        except Exception:
            task.status = TaskStatus.FAILED
            self.state.tasks_failed += 1
            return {"status": "failed", "agent": self.agent_id, "task": task.task_id}

    def update_health(self) -> AgentHealth:
        """Re-evaluate agent health based on queue and coherence."""
        q = self.state.queue_length
        if q >= MAX_QUEUE_LENGTH:
            self.state.health = AgentHealth.OVERLOADED
        elif q >= MAX_QUEUE_LENGTH // 2 or self.state.coherence_score < 0.3:
            self.state.health = AgentHealth.DEGRADED
        else:
            self.state.health = AgentHealth.HEALTHY
        return self.state.health


__all__ = [
    "AgentHealth",
    "AgentRole",
    "AgentState",
    "BaseAgent",
    "COHERENCE_THRESHOLD",
    "MAX_QUEUE_LENGTH",
    "TASK_ROUTING_MAP",
    "Task",
    "TaskStatus",
    "TaskType",
]
