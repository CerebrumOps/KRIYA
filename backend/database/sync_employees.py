# ==============================================================================
# KRIYA Employee Synchronizer & Directory Mapper
# ==============================================================================
# Queries the remote company database on Raspberry Pi 5 (READ-ONLY)
# and synchronizes/maps employee designations and clearance levels (1 to 4)
# into the local SQLite database at backend/data/kriya_auth.db.
# ==============================================================================

import asyncio
import json
import logging
from typing import Any, Dict, List

import asyncpg

from backend.config import COMPANY_DB_URL
from backend.database.auth_db import (
    get_employee_by_id,
    hash_password,
    init_auth_db,
    upsert_employee,
)

logger = logging.getLogger("kriya.sync")

# Pre-registered demo accounts for immediate testing
PRE_REGISTERED_DEMO_ACCOUNTS = {
    "EMP-1008",  # Arun V. Rao - Level 2 (Inspector hero persona)
    "EMP-1002",  # K. V. Ramanathan - Level 4 (General Manager hero persona)
    "EMP-1001",  # Dr. Arvind Swaminathan - Level 4 (Director)
    "EMP-1005",  # Rajesh K. Sharma - Level 3 (AGM Maintenance)
    "EMP-1025",  # Mahesh G. Prabhu - Level 1 (Technician)
}
DEFAULT_DEMO_PASSWORD = "Kriya@2026"


def compute_permissions_for_clearance(clearance_level: int) -> List[str]:
    """
    Computes domain permissions matching the RBAC matrix in MCP_DOCUMENTATION.md.
    """
    perms = ["units", "telemetry", "standards", "sops_level_1"]
    if clearance_level >= 2:
        perms.extend([
            "equipment_design_specs",
            "thickness_cml",
            "inspection_reports",
            "work_orders",
            "line_list",
            "ptw",
            "documents_lvl_2",
            "vendors"
        ])
    if clearance_level >= 3:
        perms.extend([
            "budgets",
            "rate_contracts",
            "incidents",
            "moc_records",
            "doa_matrix",
            "documents_lvl_3"
        ])
    if clearance_level >= 4:
        perms.extend([
            "commercial_bids",
            "capex_proposals",
            "executive_correspondence",
            "documents_lvl_4"
        ])
    return perms


async def sync_employees_from_company_db() -> int:
    """
    Reads active employees from corp.employees in the company database (PostgreSQL 17)
    and maps them to local SQLite records.
    Never alters or writes to the company database.
    """
    await init_auth_db()

    conn = None
    try:
        logger.info(f"Connecting to company database at {COMPANY_DB_URL}...")
        conn = await asyncpg.connect(COMPANY_DB_URL, timeout=10)

        query = """
            SELECT e.emp_id, e.emp_code, e.name, e.email, e.status, e.clearance_level,
                   r.role_code, r.role_name, d.dept_code, d.dept_name
            FROM corp.employees e
            LEFT JOIN corp.roles r ON e.role_id = r.role_id
            LEFT JOIN corp.departments d ON e.dept_id = d.dept_id
            ORDER BY e.emp_id;
        """
        rows = await conn.fetch(query)
        logger.info(f"Fetched {len(rows)} employee records from company database.")

        count = 0
        demo_hash = hash_password(DEFAULT_DEMO_PASSWORD)

        for r in rows:
            emp_code = r["emp_code"]
            existing = await get_employee_by_id(emp_code)

            clearance = r["clearance_level"] or 1
            permissions = compute_permissions_for_clearance(clearance)

            # Determine registration status & password
            if existing and existing.get("is_registered"):
                is_registered = True
                pwd_hash = existing.get("password_hash")
            elif emp_code in PRE_REGISTERED_DEMO_ACCOUNTS:
                is_registered = True
                pwd_hash = demo_hash
            else:
                is_registered = False
                pwd_hash = None

            emp_data = {
                "employee_id": emp_code,
                "employee_name": r["name"],
                "company_email": r["email"],
                "designation": r["role_name"] or "Plant Engineer",
                "department": r["dept_name"] or "Operations",
                "operational_site": f"Refinery Complex Alpha ({r['dept_code'] or 'Plant'})",
                "role_code": r["role_code"] or "ENG",
                "clearance_level": clearance,
                "password_hash": pwd_hash,
                "is_registered": is_registered,
                "is_active": (r["status"] == "Active"),
                "access_level": r["role_code"] or "process_engineer",
                "permissions": permissions
            }

            await upsert_employee(emp_data)
            count += 1

        logger.info(f"Successfully mapped {count} employees into local SQLite database.")
        return count

    except Exception as e:
        logger.warning(
            f"Could not reach remote company database for sync: {e}. "
            f"Local cached SQLite employees will be utilized."
        )
        return 0
    finally:
        if conn:
            await conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(sync_employees_from_company_db())
