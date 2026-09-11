# ==============================================================================
# KRIYA - Central Subagents Registry
# ==============================================================================
# Registers all specialized industrial subagents, their capabilities, and handles:
# 1. Intent Router Subagent
# 2. Planning & Task Queue Subagent
# 3. Code Sandbox & Self-Repair Subagent
# 4. Deliverable Synthesis Subagent
# 5. P&ID Vision Subagent
# ==============================================================================

from typing import Any, Dict, List, Optional
from backend.subagents.intent_router import classify_intent
from backend.subagents.planning_agent import generate_plan
from backend.subagents.task_queue import (
    create_plan_task,
    get_plan,
    get_active_plan,
    approve_plan,
    reject_plan,
    update_step_status,
    request_action_approval,
    resolve_action_approval,
    list_pending_approvals
)

AGENTS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "intent_router": {
        "name": "Action Router Subagent",
        "description": "Parses incoming requests, selects domain skill, and routes to local reasoning, coding, or vision model.",
        "handler": classify_intent
    },
    "planning_agent": {
        "name": "Industrial Planning Subagent",
        "description": "Constructs structured execution plans, establishes evidence verification gates, and generates task queues.",
        "handler": generate_plan
    },
    "task_queue_engine": {
        "name": "Task Queue & Approval State Engine",
        "description": "Tracks multi-step plan execution, step progression, and human-in-the-loop approvals.",
        "handler": create_plan_task
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
