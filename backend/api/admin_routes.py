# ==============================================================================
# KRIYA Administration & Employee Directory REST API
# ==============================================================================
# Endpoints:
#   - GET  /api/admin/employees
#   - POST /api/admin/employees
#   - GET  /api/admin/employees/{employee_id}
#   - POST /api/admin/employees/{employee_id}/toggle-active
#   - POST /api/admin/employees/{employee_id}/reset-registration
#   - GET  /api/admin/stats
# ==============================================================================

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from backend.database.auth_db import (
    get_auth_stats,
    get_employee_by_id,
    list_all_employees,
    reset_employee_registration,
    toggle_employee_active,
    upsert_employee,
)
from backend.database.sync_employees import compute_permissions_for_clearance
from backend.schemas.auth import (
    AdminStatsResponse,
    EnrollEmployeeRequest,
)

router = APIRouter(prefix="/api/admin", tags=["Admin Portal"])


def _format_emp_for_admin(emp: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "employeeId": emp["employee_id"],
        "employeeName": emp["employee_name"],
        "companyEmail": emp["company_email"],
        "designation": emp["designation"],
        "department": emp["department"],
        "operationalSite": emp.get("operational_site", "Refinery Complex Alpha (Sector 4)"),
        "roleCode": emp.get("role_code", "ENG"),
        "clearanceLevel": emp.get("clearance_level", 2),
        "isRegistered": bool(emp.get("is_registered")),
        "isActive": bool(emp.get("is_active")),
        "accessLevel": emp.get("access_level", "process_engineer"),
        "registeredAt": emp.get("updated_at") if emp.get("is_registered") else None
    }


@router.get("/employees")
async def list_employees():
    """Returns list of all employees in the corporate directory."""
    records = await list_all_employees()
    return [_format_emp_for_admin(e) for e in records]


@router.post("/employees")
async def enroll_employee(req: EnrollEmployeeRequest):
    """Enrolls a new employee into the local directory."""
    existing = await get_employee_by_id(req.employeeId.strip())
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee ID '{req.employeeId}' already exists in directory."
        )

    clearance = req.clearanceLevel or 2
    permissions = compute_permissions_for_clearance(clearance)

    emp_data = {
        "employee_id": req.employeeId.strip(),
        "employee_name": req.employeeName.strip(),
        "company_email": req.companyEmail.strip(),
        "designation": req.designation.strip(),
        "department": req.department.strip(),
        "operational_site": req.operationalSite.strip(),
        "role_code": req.roleCode or "ENG",
        "clearance_level": clearance,
        "password_hash": None,
        "is_registered": False,
        "is_active": True,
        "access_level": req.roleCode or "process_engineer",
        "permissions": permissions
    }
    await upsert_employee(emp_data)
    created = await get_employee_by_id(req.employeeId.strip())
    return {"success": True, "employee": _format_emp_for_admin(created)}


@router.get("/employees/{employee_id}")
async def get_employee_detail(employee_id: str):
    """Retrieves full employee record by ID."""
    emp = await get_employee_by_id(employee_id.strip())
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found."
        )
    return _format_emp_for_admin(emp)


@router.post("/employees/{employee_id}/toggle-active")
async def toggle_active(employee_id: str):
    """Toggles employee account active/suspended state."""
    new_status = await toggle_employee_active(employee_id.strip())
    if new_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found."
        )
    return {"success": True, "isActive": new_status}


@router.post("/employees/{employee_id}/reset-registration")
async def reset_registration(employee_id: str):
    """Resets employee registration state, clearing passwords and allowing re-onboarding."""
    success = await reset_employee_registration(employee_id.strip())
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found."
        )
    return {"success": True, "message": "Employee registration state reset successfully."}


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats():
    """Returns directory statistics."""
    stats = await get_auth_stats()
    return AdminStatsResponse(**stats)
