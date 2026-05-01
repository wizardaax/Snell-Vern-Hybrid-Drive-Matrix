"""Agent 3: Memory_Keeper — associative memory + corpus search.

Stores in-memory key/value associations AND searches an on-disk
corpus_index.json (Xova's body-of-work index) using a deterministic
token-overlap engine.

Stdlib only — no external search libraries. The same engine ships in the
Xova UI so results match exactly.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from . import AgentRole, BaseAgent, Task, TaskType

# Default corpus location — overridable per-task via payload["corpus_path"].
_DEFAULT_CORPUS = r"C:\Xova\memory\corpus_index.json"

# Stopwords filtered before token matching. Mirrors Xova's /corpus engine.
_STOP: frozenset[str] = frozenset({
    "the", "and", "but", "with", "this", "that", "what", "when", "where",
    "how", "why", "you", "are", "for", "not", "can", "get", "let", "its",
    "was", "has", "have", "had", "does", "did", "into", "from", "over",
    "under", "about", "than", "then", "also", "like", "just", "your",
    "mine", "ours", "they", "them", "there", "here", "some", "much",
    "more", "most", "very", "such", "each", "every", "these", "those",
    "being", "been", "were",
})

_TOKEN_RE = re.compile(r"\b[a-z0-9][a-z0-9]{2,}\b")


class MemoryKeeperAgent(BaseAgent):
    """Associative memory + on-disk corpus search."""

    role = AgentRole.MEMORY_KEEPER
    capabilities = frozenset({TaskType.MEMORY})

    def __init__(self, agent_id: str) -> None:
        super().__init__(agent_id)
        self._store: dict[str, Any] = {}
        # Lazily-loaded corpus cache so repeated searches don't re-read 5MB.
        self._corpus_cache: Optional[dict[str, Any]] = None
        self._corpus_path_cached: Optional[str] = None

    # ------------------------------------------------------------------
    # Corpus loader
    # ------------------------------------------------------------------

    def _load_corpus(self, path: str) -> Optional[dict[str, Any]]:
        if self._corpus_cache is not None and self._corpus_path_cached == path:
            return self._corpus_cache
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return None
        if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
            return None
        self._corpus_cache = data
        self._corpus_path_cached = path
        return data

    # ------------------------------------------------------------------
    # Search engine — same token-overlap as Xova's /corpus
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(query: str) -> list[str]:
        seen: list[str] = []
        for tok in _TOKEN_RE.findall(query.lower()):
            if tok in _STOP or tok in seen:
                continue
            seen.append(tok)
        return seen

    def _search(self, query: str, corpus_path: str, limit: int = 12) -> dict[str, Any]:
        corpus = self._load_corpus(corpus_path)
        if corpus is None:
            return {
                "matched": False,
                "reason": "corpus index unavailable",
                "path": corpus_path,
            }
        tokens = self._tokenize(query)
        if not tokens:
            return {"matched": False, "reason": "empty query after stopword filter"}
        threshold = 2 if len(tokens) >= 2 else 1
        scored: list[tuple[int, bool, dict[str, Any]]] = []
        for entry in corpus["entries"]:
            haystack = (entry.get("name", "") + " " + entry.get("excerpt", "")).lower()
            score = sum(1 for t in tokens if t in haystack)
            name_lower = entry.get("name", "").lower()
            name_hit = any(t in name_lower for t in tokens)
            if name_hit:
                score += 2
            if score >= threshold:
                scored.append((score, name_hit, entry))
        scored.sort(key=lambda x: (-x[0], -x[2].get("mtime", 0)))
        top = scored[:limit]
        return {
            "matched": True,
            "query": query,
            "tokens": tokens,
            "total_hits": len(scored),
            "top": [
                {
                    "name": e.get("name"),
                    "path": e.get("path"),
                    "ext": e.get("ext"),
                    "root": e.get("root"),
                    "mtime": e.get("mtime"),
                    "score": s,
                    "name_hit": nh,
                    "excerpt": e.get("excerpt", "")[:200],
                }
                for s, nh, e in top
            ],
        }

    # ------------------------------------------------------------------
    # Public execute
    # ------------------------------------------------------------------

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload
        action = payload.get("action", "get")

        if action == "search":
            query = payload.get("query") or payload.get("goal") or ""
            corpus_path = payload.get("corpus_path", _DEFAULT_CORPUS)
            result = self._search(query, corpus_path, limit=int(payload.get("limit", 12)))
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "searched",
                **result,
            }

        if action == "store":
            self._store[payload.get("key", "")] = payload.get("value")
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "stored",
                "key": payload.get("key", ""),
            }

        if action == "get":
            key = payload.get("key", "")
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "retrieved",
                "key": key,
                "value": self._store.get(key),
            }

        if action == "list":
            return {
                "status": "completed",
                "agent": self.agent_id,
                "task": task.task_id,
                "action": "listed",
                "keys": sorted(self._store.keys()),
            }

        return {
            "status": "completed",
            "agent": self.agent_id,
            "task": task.task_id,
            "action": "noop",
        }
