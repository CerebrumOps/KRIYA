# ==============================================================================
# KRIYA Task Queue, Planning & Human Approval REST API
# ==============================================================================
# Exposes endpoints for:
# - Plan generation and task queue inspection
# - Human approval for starting multi-step plan execution
# - Action-level approval gates (web search, terminal actions)
# ==============================================================================

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from backend.subagents.task_queue import (
    create_plan_task,
    get_plan,
    get_active_plan,
    approve_plan,
    reject_plan,
    update_plan_details,
    update_checklist_item_status,
    resolve_action_approval,
    list_pending_approvals,
    request_action_approval
)

router = APIRouter(prefix="/api", tags=["Planning & Task Queue"])


class CreatePlanRequest(BaseModel):
    user_prompt: str
    context: Optional[Dict[str, Any]] = None


class UpdatePlanRequest(BaseModel):
    plan: Optional[str] = None
    check_list: Optional[List[Dict[str, Any]]] = None


class UpdateChecklistItemRequest(BaseModel):
    status: str


class ResolveApprovalRequest(BaseModel):
    approved: bool


@router.post("/plan/create")
async def api_create_plan(req: CreatePlanRequest):
    """Generates a structured execution plan and enqueues tasks."""
    plan = await create_plan_task(req.user_prompt, req.context)
    return {"plan": plan}


@router.get("/plan/active")
async def api_get_active_plan():
    """Returns the currently active task queue in the workbench."""
    plan = get_active_plan()
    if not plan:
        return {"plan": None, "message": "No active plan running."}
    return {"plan": plan}


@router.get("/plan/{plan_id}")
async def api_get_plan(plan_id: str):
    """Returns details and step progress for a specific plan."""
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' not found.")
    return {"plan": plan}


@router.post("/plan/{plan_id}/approve")
async def api_approve_plan(plan_id: str):
    """Human-in-the-Loop gate: Operator approves proposed execution plan."""
    try:
        plan = approve_plan(plan_id)
        return {"success": True, "plan": plan, "message": "Plan approved. Autonomous execution initiated."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/plan/{plan_id}/reject")
async def api_reject_plan(plan_id: str):
    """Human-in-the-Loop gate: Operator rejects or cancels proposed plan."""
    try:
        plan = reject_plan(plan_id)
        return {"success": True, "plan": plan, "message": "Plan rejected."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/plan/{plan_id}/update")
async def api_update_plan(plan_id: str, req: UpdatePlanRequest):
    """Allows human operator to edit the plan markdown or customize the checklist."""
    try:
        plan = update_plan_details(plan_id, plan_markdown=req.plan, check_list=req.check_list)
        return {"success": True, "plan": plan, "message": "Plan updated successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/plan/{plan_id}/checklist/{item_id}")
async def api_update_checklist_item(plan_id: str, item_id: str, req: UpdateChecklistItemRequest):
    """Updates status of a single checklist task item."""
    try:
        plan = update_checklist_item_status(plan_id, item_id, req.status)
        return {"success": True, "plan": plan}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))



@router.get("/approvals/pending")
async def api_list_pending_approvals():
    """Returns all pending human approval requests (e.g. web search permissions)."""
    approvals = list_pending_approvals()
    return {"pendingApprovals": approvals, "count": len(approvals)}


@router.post("/approvals/{approval_id}/resolve")
async def api_resolve_approval(approval_id: str, req: ResolveApprovalRequest):
    """Operator approves or denies a sensitive action request."""
    try:
        res = resolve_action_approval(approval_id, req.approved)
        return {"success": True, "approval": res}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
