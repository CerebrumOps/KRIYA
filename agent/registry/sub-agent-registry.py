# ==============================================================================
# KRIYA - Central Subagents Registry
# ==============================================================================
# Registers specialized industrial subagents callable as tools:
# - Sovereign Memory Intelligence Subagent (Retrieval + Summarization)
# ==============================================================================

from typing import Any, Dict, List, Optional
from agent.subagents.memory_agent import search_and_summarize_memories, store_agent_memory

AGENTS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "memory_subagent": {
        "name": "Sovereign Memory & Context Subagent",
        "description": "2-agent pipeline (Retrieval + Summarizer) for recalling historical plant insights, calculations, and operator preferences.",
        "handler": search_and_summarize_memories
    }
}


def get_subagent(name: str) -> Optional[Dict[str, Any]]:
    """Returns subagent definition by name."""
    return AGENTS_REGISTRY.get(name)


def list_registered_subagents() -> List[Dict[str, Any]]:
    """Returns a list of all registered subagents with descriptions."""
    return [
        {"id": k, "name": v["name"], "description": v["description"]}
        for k, v in AGENTS_REGISTRY.items()
    ]
