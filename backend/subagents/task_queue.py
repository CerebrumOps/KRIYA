# ==============================================================================
# KRIYA Task Queue & Human Approval Engine
# ==============================================================================
# Manages execution lifecycle for multi-step industrial plans and human-in-the-loop approvals:
# - Plan state transitions: PENDING_APPROVAL -> APPROVED -> EXECUTING -> COMPLETED / REJECTED
# - Granular step progress tracking (pending, running, completed, failed)
# - Gatekeeper for sensitive actions (web search, destructive commands, plan kickoff)
# ==============================================================================

import secrets
import time
from typing import Any, Dict, List, Optional

from backend.subagents.intent_router import classify_intent
from backend.subagents.planning_agent import generate_plan, generate_plan_async

# In-memory plan and approval stores
_PLANS: Dict[str, Dict[str, Any]] = {}
_PENDING_APPROVALS: Dict[str, Dict[str, Any]] = {}
_ACTIVE_PLAN_ID: Optional[str] = None


async def create_plan_task(user_prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Classifies intent and generates a new execution plan task using LLM/heuristics.
    Registers plan in the queue.
    """
    global _ACTIVE_PLAN_ID
    intent = classify_intent(user_prompt)
    plan = await generate_plan_async(user_prompt, intent, context)
    plan_id = plan["plan_id"]
    _PLANS[plan_id] = plan
    _ACTIVE_PLAN_ID = plan_id
    return plan


def get_plan(plan_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves plan by ID."""
    return _PLANS.get(plan_id)


def get_active_plan() -> Optional[Dict[str, Any]]:
    """Returns the currently active plan in the workbench if not rejected or completed."""
    global _ACTIVE_PLAN_ID
    if _ACTIVE_PLAN_ID and _ACTIVE_PLAN_ID in _PLANS:
        plan = _PLANS[_ACTIVE_PLAN_ID]
        if plan.get("status") in ["REJECTED", "CANCELLED"]:
            _ACTIVE_PLAN_ID = None
            return None
        return plan
    return None


def approve_plan(plan_id: str) -> Dict[str, Any]:
    """Approves plan for execution."""
    if plan_id not in _PLANS:
        raise ValueError(f"Plan '{plan_id}' not found.")
    _PLANS[plan_id]["status"] = "APPROVED"
    _PLANS[plan_id]["approved_at"] = time.time()
    return _PLANS[plan_id]


def reject_plan(plan_id: str) -> Dict[str, Any]:
    """Rejects or cancels a proposed plan, discarding it from active queue."""
    global _ACTIVE_PLAN_ID
    if plan_id not in _PLANS:
        raise ValueError(f"Plan '{plan_id}' not found.")
    _PLANS[plan_id]["status"] = "REJECTED"
    if _ACTIVE_PLAN_ID == plan_id:
        _ACTIVE_PLAN_ID = None
    return _PLANS[plan_id]


def update_plan_details(
    plan_id: str,
    plan_markdown: Optional[str] = None,
    check_list: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Allows operator to edit plan markdown or add/edit checklist items."""
    if plan_id not in _PLANS:
        raise ValueError(f"Plan '{plan_id}' not found.")
    plan = _PLANS[plan_id]
    if plan_markdown is not None:
        plan["plan"] = plan_markdown
    if check_list is not None:
        plan["check_list"] = check_list
        plan["steps"] = [
            {
                "step_id": i + 1,
                "title": it.get("task", f"Task {i+1}"),
                "tool": it.get("tool", "custom_tool"),
                "status": "completed" if it.get("status") == "success" else it.get("status", "pending")
            }
            for i, it in enumerate(check_list)
        ]
        plan["total_steps"] = len(check_list)
    return plan


def update_checklist_item_status(plan_id: str, item_id: str, status: str) -> Dict[str, Any]:
    """Updates status of a specific checklist item."""
    if plan_id not in _PLANS:
        raise ValueError(f"Plan '{plan_id}' not found.")
    plan = _PLANS[plan_id]
    for it in plan.get("check_list", []):
        if it.get("id") == item_id:
            it["status"] = status
            break
    # sync with steps
    for step in plan.get("steps", []):
        if step.get("step_id") == item_id or f"step_{step.get('step_id')}" == item_id:
            step["status"] = "completed" if status == "success" else status
            break
    return plan


def update_checklist_by_tool(tool_name: str, status: str = "success") -> Optional[Dict[str, Any]]:
    """
    Finds active plan and marks the first pending/in_progress checklist item
    whose associated tool matches tool_name as completed/success.
    """
    global _ACTIVE_PLAN_ID
    if not _ACTIVE_PLAN_ID or _ACTIVE_PLAN_ID not in _PLANS:
        return None

    plan = _PLANS[_ACTIVE_PLAN_ID]
    norm_tool = tool_name.strip().lower()

    # Update first matching item in check_list
    for it in plan.get("check_list", []):
        if it.get("status") in ("pending", "in_progress"):
            cand = (it.get("tool") or "").strip().lower()
            if cand == norm_tool or norm_tool in cand or cand in norm_tool:
                it["status"] = status
                break

    # Sync steps
    for step in plan.get("steps", []):
        if step.get("status") in ("pending", "running"):
            cand = (step.get("tool") or "").strip().lower()
            if cand == norm_tool or norm_tool in cand or cand in norm_tool:
                step["status"] = "completed" if status == "success" else status
                break

    # Check overall plan completion
    items = plan.get("check_list", [])
    if items and all(it.get("status") == "success" for it in items):
        plan["status"] = "COMPLETED"

    return plan


def update_step_status(
    plan_id: str,
    step_id: int,
    status: str,
    result: Optional[str] = None
) -> Dict[str, Any]:
    """Updates the status and output of a specific plan step."""
    if plan_id not in _PLANS:
        raise ValueError(f"Plan '{plan_id}' not found.")

    plan = _PLANS[plan_id]
    for step in plan["steps"]:
        if step["step_id"] == step_id:
            step["status"] = status
            if result:
                step["actual_output"] = result
            break

    # Also update check_list
    check_list = plan.get("check_list", [])
    if 0 <= step_id - 1 < len(check_list):
        check_list[step_id - 1]["status"] = "success" if status == "completed" else status

    # If all steps completed, mark plan COMPLETED
    if all(s.get("status") == "completed" for s in plan["steps"]):
        plan["status"] = "COMPLETED"
    elif any(s.get("status") == "failed" for s in plan["steps"]):
        plan["status"] = "FAILED"
    elif any(s.get("status") == "running" for s in plan["steps"]):
        plan["status"] = "EXECUTING"

    return plan


# ==============================================================================
# ACTION-LEVEL HUMAN-IN-THE-LOOP APPROVALS
# ==============================================================================

def request_action_approval(
    action_type: str,
    details: Dict[str, Any]
) -> str:
    """
    Registers a sensitive action (e.g. web search, file deletion, network call)
    that requires explicit operator confirmation before execution.
    Returns: approval_id
    """
    approval_id = f"appr_{secrets.token_hex(4)}"
    _PENDING_APPROVALS[approval_id] = {
        "approval_id": approval_id,
        "action_type": action_type,
        "details": details,
        "status": "PENDING",
        "created_at": time.time()
    }
    return approval_id


def resolve_action_approval(approval_id: str, approved: bool) -> Dict[str, Any]:
    """Resolves a pending human approval decision."""
    if approval_id not in _PENDING_APPROVALS:
        raise ValueError(f"Approval request '{approval_id}' not found.")

    req = _PENDING_APPROVALS[approval_id]
    req["status"] = "APPROVED" if approved else "DENIED"
    req["resolved_at"] = time.time()
    return req


def list_pending_approvals() -> List[Dict[str, Any]]:
    """Returns all pending human approval requests."""
    return [a for a in _PENDING_APPROVALS.values() if a["status"] == "PENDING"]
