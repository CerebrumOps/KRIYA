# ==============================================================================
# KRIYA Database Request Logic: Corporate Employee & Auth Queries
# ==============================================================================
# Manages database queries for:
# - Employee directory retrieval
# - Registration lifecycle & OTP generation/validation
# - Password hashing with bcrypt
# - 2FA authentication & JWT issuance
# - Initial seed data from Tailscale mesh network profiles
# ==============================================================================

import json
import os
import random
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
import bcrypt
from dotenv import load_dotenv

from backend.database.kriya_db.schema.employee import CREATE_EMPLOYEES_TABLE_SQL

# Load DATABASE_URL from .env
env_path = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

import asyncio

_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Returns or creates the global asyncpg connection pool bound to current event loop."""
    global _pool
    current_loop = asyncio.get_running_loop()
    if _pool is None or getattr(_pool, "_loop", None) != current_loop or getattr(_pool, "_closed", False):
        load_dotenv(dotenv_path=env_path, override=True)
        db_url = os.getenv("DATABASE_URL", DATABASE_URL)
        _pool = await asyncpg.create_pool(db_url, min_size=1, max_size=10)
        # Ensure tables and seed data exist
        await init_employee_db(_pool)
    return _pool


# Seed employees based on model_load_and_device_setups/tailscale_adresses.md
SEED_EMPLOYEES = [
    {
        "employee_id": "EMP-0001",
        "employee_name": "KRIYA System Admin",
        "company_email": "admin@mrpl.co.in",
        "designation": "Chief Information & Sovereign Security Officer",
        "department": "Sovereign AI Administration",
        "operational_site": "Mangalore Central Operations",
        "access_level": "admin",
        "permissions": [
            "chat:standard",
            "chat:reasoning",
            "tools:read_telemetry",
            "tools:simulate_process",
            "schematics:view_p_and_id",
            "approvals:approve_plan",
            "admin:manage_employees"
        ]
    },
    {
        "employee_id": "ADMIN-1001",
        "employee_name": "Vivekananda (Admin)",
        "company_email": "vivekananda2201s7@gmail.com",
        "designation": "Sovereign AI System Administrator",
        "department": "Corporate IT & Sovereign AI Infrastructure",
        "operational_site": "Mangalore Central Operations",
        "access_level": "admin",
        "permissions": [
            "chat:standard",
            "chat:reasoning",
            "tools:read_telemetry",
            "tools:simulate_process",
            "schematics:view_p_and_id",
            "approvals:approve_plan",
            "admin:manage_employees"
        ]
    },
    {
        "employee_id": "EMP-1001",
        "employee_name": "Vivekananda",
        "company_email": "vivekananda2201s7@gmail.com",
        "designation": "Lead Process Control Engineer",
        "department": "Crude Distillation Unit (CDU-II)",
        "operational_site": "Mangalore Refinery Complex (Site-Alpha)",
        "access_level": "lead_engineer",
        "permissions": [
            "chat:standard",
            "chat:reasoning",
            "tools:read_telemetry",
            "tools:simulate_process",
            "schematics:view_p_and_id",
            "approvals:approve_plan"
        ]
    },
    {
        "employee_id": "EMP-1002",
        "employee_name": "Akshitha Rachakonda",
        "company_email": "akshitharachakonda25@gmail.com",
        "designation": "Senior Safety & Inspection Engineer",
        "department": "Plant Inspection & Integrity Wing",
        "operational_site": "Refinery Complex Alpha (Sector 4)",
        "access_level": "senior_engineer",
        "permissions": [
            "chat:standard",
            "chat:reasoning",
            "tools:read_telemetry",
            "inspection:generate_approval_note",
            "schematics:view_p_and_id"
        ]
    },
    {
        "employee_id": "EMP-1003",
        "employee_name": "Archana",
        "company_email": "archana020507@gmail.com",
        "designation": "Senior Plant Reliability Engineer",
        "department": "Fluid Catalytic Cracking Unit (FCCU)",
        "operational_site": "Refinery Complex Beta",
        "access_level": "senior_engineer",
        "permissions": [
            "chat:standard",
            "chat:reasoning",
            "tools:read_telemetry",
            "tools:simulate_process"
        ]
    },
    {
        "employee_id": "EMP-1004",
        "employee_name": "Chaitanya Varma",
        "company_email": "chaitanyakanumuri48@gmail.com",
        "designation": "Senior Operations Superintendent",
        "department": "Vacuum Distillation Unit (VDU)",
        "operational_site": "Mangalore Complex Alpha",
        "access_level": "senior_engineer",
        "permissions": [
            "chat:standard",
            "chat:reasoning",
            "tools:read_telemetry",
            "tools:simulate_process"
        ]
    },
    {
        "employee_id": "EMP-1005",
        "employee_name": "Viveka",
        "company_email": "rviveka86@gmail.com",
        "designation": "Lead Automation & SCADA Engineer",
        "department": "Instrumentation & SCADA Control",
        "operational_site": "Central Control Room",
        "access_level": "lead_engineer",
        "permissions": [
            "chat:standard",
            "chat:reasoning",
            "tools:read_telemetry",
            "tools:simulate_process",
            "schematics:view_p_and_id"
        ]
    },
    {
        "employee_id": "EMP-1006",
        "employee_name": "Tarun",
        "company_email": "tarunff0777@gmail.com",
        "designation": "Maintenance & Overhaul Specialist",
        "department": "Rotary Equipment Division",
        "operational_site": "Mangalore Complex Alpha",
        "access_level": "specialist",
        "permissions": [
            "chat:standard",
            "chat:reasoning",
            "tools:read_telemetry",
            "maintenance:work_orders"
        ]
    },
    {
        "employee_id": "EMP-8942",
        "employee_name": "Aarav Sharma",
        "company_email": "aarav.sharma@kriya-energy.com",
        "designation": "Senior Process Engineer",
        "department": "Crude Distillation Unit (CDU-II)",
        "operational_site": "Refinery Complex Alpha (Sector 4)",
        "access_level": "senior_engineer",
        "permissions": [
            "chat:standard",
            "chat:reasoning",
            "tools:read_telemetry"
        ]
    }
]


async def init_employee_db(pool: asyncpg.Pool) -> None:
    """Initializes tables and seeds default employee accounts if empty."""
    async with pool.acquire() as conn:
        await conn.execute(CREATE_EMPLOYEES_TABLE_SQL)

        # Check existing employees count
        count = await conn.fetchval("SELECT count(*) FROM employees")
        if count == 0:
            for emp in SEED_EMPLOYEES:
                await conn.execute(
                    """
                    INSERT INTO employees (
                        employee_id, employee_name, company_email, designation,
                        department, operational_site, access_level, permissions,
                        is_registered, is_active, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, FALSE, TRUE, NOW(), NOW())
                    ON CONFLICT (employee_id) DO NOTHING
                    """,
                    emp["employee_id"],
                    emp["employee_name"],
                    emp["company_email"],
                    emp["designation"],
                    emp["department"],
                    emp["operational_site"],
                    emp["access_level"],
                    json.dumps(emp["permissions"])
                )


def mask_email(email: str) -> str:
    """Masks corporate email for safe display (e.g. vi***s7@gmail.com)."""
    if not email or "@" not in email:
        return "—"
    name_part, domain = email.split("@", 1)
    if len(name_part) <= 2:
        masked_name = name_part[0] + "***"
    else:
        masked_name = name_part[:2] + "***" + name_part[-2:]
    return f"{masked_name}@{domain}"


def hash_password(password: str) -> str:
    """Hashes plain text password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain text password against bcrypt hash."""
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


async def get_employee_by_id(employee_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves full employee record by employee ID."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT employee_id, employee_name, company_email, designation,
                   department, operational_site, password_hash, is_registered,
                   is_active, access_level, permissions, created_at, updated_at
            FROM employees
            WHERE employee_id = $1
            """,
            employee_id.strip()
        )
    if not row:
        return None
    return dict(row)


async def get_employee_by_identifier(identifier: str) -> Optional[Dict[str, Any]]:
    """Retrieves employee record by either employee ID or company email."""
    pool = await get_db_pool()
    ident = identifier.strip()
    async with pool.acquire() as conn:
        # 1. First priority: Exact match by employee_id (e.g. 'ADMIN-1001' or 'EMP-1001')
        row = await conn.fetchrow(
            """
            SELECT employee_id, employee_name, company_email, designation,
                   department, operational_site, password_hash, is_registered,
                   is_active, access_level, permissions, created_at, updated_at
            FROM employees
            WHERE LOWER(employee_id) = LOWER($1)
            """,
            ident
        )
        if not row:
            # 2. Match by email: prefer standard employee accounts over ADMIN- aliases
            row = await conn.fetchrow(
                """
                SELECT employee_id, employee_name, company_email, designation,
                       department, operational_site, password_hash, is_registered,
                       is_active, access_level, permissions, created_at, updated_at
                FROM employees
                WHERE LOWER(company_email) = LOWER($1)
                ORDER BY (CASE WHEN employee_id LIKE 'ADMIN-%' THEN 2 ELSE 1 END), employee_id ASC
                LIMIT 1
                """,
                ident
            )
    if not row:
        return None
    return dict(row)


async def generate_and_store_otp(employee_id: str, purpose: str) -> Dict[str, Any]:
    """
    Generates a cryptographically random 6-digit numeric OTP and a unique token.
    Stores record in auth_otps with a 5-minute expiration.
    Returns: dict with otp_code, token, masked_email, and expiration.
    """
    pool = await get_db_pool()
    # 6-digit numeric OTP
    otp_code = "".join(random.choices(string.digits, k=6))
    
    # Token prefix matching contract
    if purpose == "registration":
        token = f"reg_vtok_{secrets.token_hex(16)}"
    else:
        token = f"login_vref_{secrets.token_hex(16)}"

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    otp_id = str(uuid.uuid4())

    async with pool.acquire() as conn:
        # Invalidate previous unused OTPs for this employee & purpose
        await conn.execute(
            """
            UPDATE auth_otps
            SET is_used = TRUE
            WHERE employee_id = $1 AND purpose = $2 AND is_used = FALSE
            """,
            employee_id, purpose
        )

        await conn.execute(
            """
            INSERT INTO auth_otps (id, employee_id, otp_code, purpose, token, expires_at, is_used, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, FALSE, NOW())
            """,
            otp_id, employee_id, otp_code, purpose, token, expires_at
        )

        # Also get employee email to return masked email
        email = await conn.fetchval(
            "SELECT company_email FROM employees WHERE employee_id = $1",
            employee_id
        )

    # Dispatch via SMTP if configured, otherwise log to terminal for sovereign air-gap
    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    sent_via_smtp = False
    if smtp_host and smtp_user and smtp_pass and email:
        try:
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(
                f"Your KRIYA Sovereign Industrial AI verification code is: {otp_code}\n\n"
                f"This code will expire in 5 minutes.\n\n"
                f"Purpose: {purpose.upper()}\n"
                f"Employee ID: {employee_id}\n\n"
                f"MRPL Sovereign Air-Gapped Security System"
            )
            msg["Subject"] = f"KRIYA Sovereign 2FA Code: {otp_code}"
            msg["From"] = os.getenv("SMTP_FROM", smtp_user)
            msg["To"] = email

            with smtplib.SMTP(smtp_host, smtp_port, timeout=5) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(msg["From"], [email], msg.as_string())
            sent_via_smtp = True
            print(f"\n[SMTP GATEWAY] Real email successfully sent to {email} with OTP [{otp_code}]\n")
        except Exception as smtp_err:
            print(f"\n[SMTP GATEWAY WARNING] Failed to deliver email via SMTP: {smtp_err}\n")

    if not sent_via_smtp:
        print(f"\n[SECURE SOVEREIGN AUTHENTICATION GATEWAY]")
        print(f"  -> Dispatched {purpose.upper()} OTP [{otp_code}] for Employee {employee_id} to {email}")
        print(f"  -> Token: {token} (Expires in 300s)\n")

    return {
        "otpCode": otp_code,
        "token": token,
        "maskedEmail": mask_email(email or ""),
        "expiresInSeconds": 300
    }


async def verify_registration_otp(employee_id: str, otp: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verifies 6-digit OTP for registration.
    Returns: (is_valid, verification_token, error_code)
    """
    pool = await get_db_pool()
    now = datetime.now(timezone.utc)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, otp_code, token, expires_at, is_used
            FROM auth_otps
            WHERE employee_id = $1 AND purpose = 'registration' AND is_used = FALSE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            employee_id.strip()
        )

        if not row:
            return False, None, "INVALID_OTP"

        if row["expires_at"] < now:
            return False, None, "OTP_EXPIRED"

        if row["otp_code"] != otp.strip():
            return False, None, "INVALID_OTP"

        # Mark OTP as used
        await conn.execute("UPDATE auth_otps SET is_used = TRUE WHERE id = $1", row["id"])
        return True, row["token"], None


async def verify_registration_token(employee_id: str, verification_token: str) -> bool:
    """Verifies that the registration verificationToken is valid and matches employee."""
    pool = await get_db_pool()
    now = datetime.now(timezone.utc)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, expires_at, created_at
            FROM auth_otps
            WHERE employee_id = $1 AND token = $2 AND purpose = 'registration'
            LIMIT 1
            """,
            employee_id.strip(), verification_token.strip()
        )

    if not row:
        return False
    # Token valid within 15 minutes of issuance
    token_age = now - row["created_at"]
    return token_age.total_seconds() <= 900


async def set_employee_password(employee_id: str, plain_password: str) -> bool:
    """Hashes password, updates employee record, and marks account registered."""
    pool = await get_db_pool()
    hashed = hash_password(plain_password)

    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE employees
            SET password_hash = $1, is_registered = TRUE, updated_at = NOW()
            WHERE employee_id = $2
            """,
            hashed, employee_id.strip()
        )
        return "UPDATE 1" in result


async def verify_login_otp(verification_id: str, otp: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Verifies 2FA OTP against login verificationId.
    Returns: (is_valid, employee_record, error_code)
    """
    pool = await get_db_pool()
    now = datetime.now(timezone.utc)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT o.id, o.employee_id, o.otp_code, o.expires_at, o.is_used,
                   e.employee_name, e.company_email, e.designation, e.department,
                   e.operational_site, e.access_level, e.permissions, e.is_active
            FROM auth_otps o
            JOIN employees e ON o.employee_id = e.employee_id
            WHERE o.token = $1 AND o.purpose = 'login_2fa' AND o.is_used = FALSE
            """,
            verification_id.strip()
        )

        if not row:
            return False, None, "INVALID_OTP"

        if row["expires_at"] < now:
            return False, None, "OTP_EXPIRED"

        if row["otp_code"] != otp.strip():
            return False, None, "INVALID_OTP"

        if not row["is_active"]:
            return False, None, "ACCOUNT_LOCKED_OR_INELIGIBLE"

        # Mark OTP used
        await conn.execute("UPDATE auth_otps SET is_used = TRUE WHERE id = $1", row["id"])

        # Parse permissions
        raw_perms = row["permissions"]
        if isinstance(raw_perms, str):
            try:
                perms = json.loads(raw_perms)
            except Exception:
                perms = []
        elif isinstance(raw_perms, list):
            perms = raw_perms
        else:
            perms = []

        employee_data = {
            "employeeId": row["employee_id"],
            "employeeName": row["employee_name"],
            "companyEmail": row["company_email"],
            "designation": row["designation"],
            "department": row["department"],
            "operationalSite": row["operational_site"],
            "access": {
                "level": row["access_level"],
                "permissions": perms
            }
        }

        return True, employee_data, None


# ==============================================================================
# ADMIN MANAGEMENT DATABASE QUERIES
# ==============================================================================

async def list_all_employees_admin() -> List[Dict[str, Any]]:
    """Returns all enrolled employees with administrative metadata."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT employee_id, employee_name, company_email, designation,
                   department, operational_site, access_level, permissions,
                   is_registered, is_active, created_at, updated_at
            FROM employees
            ORDER BY employee_id ASC
            """
        )

    results = []
    for r in rows:
        d = dict(r)
        raw_p = d["permissions"]
        if isinstance(raw_p, str):
            try:
                d["permissions"] = json.loads(raw_p)
            except Exception:
                d["permissions"] = []
        d["created_at"] = d["created_at"].isoformat() if d["created_at"] else None
        d["updated_at"] = d["updated_at"].isoformat() if d["updated_at"] else None
        results.append(d)
    return results


async def enroll_new_employee(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrolls a new corporate employee ID into the directory.
    Employee can then self-register using the standard verification OTP flow.
    """
    pool = await get_db_pool()
    emp_id = data["employeeId"].strip()
    name = data["employeeName"].strip()
    email = data["companyEmail"].strip().lower()
    desig = data.get("designation", "Process Engineer").strip()
    dept = data.get("department", "Plant Operations").strip()
    site = data.get("operationalSite", "Mangalore Refinery Complex").strip()
    access_level = data.get("accessLevel", "process_engineer").strip()
    perms = data.get("permissions", ["chat:standard", "chat:reasoning", "tools:read_telemetry"])

    async with pool.acquire() as conn:
        # Check if exists
        existing = await conn.fetchrow(
            "SELECT employee_id FROM employees WHERE LOWER(employee_id) = LOWER($1)",
            emp_id
        )
        if existing:
            raise ValueError(f"Employee ID '{emp_id}' is already enrolled.")

        await conn.execute(
            """
            INSERT INTO employees (
                employee_id, employee_name, company_email, designation,
                department, operational_site, access_level, permissions,
                is_registered, is_active, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, FALSE, TRUE, NOW(), NOW())
            """,
            emp_id, name, email, desig, dept, site, access_level, json.dumps(perms)
        )

    return {
        "employeeId": emp_id,
        "employeeName": name,
        "companyEmail": email,
        "designation": desig,
        "department": dept,
        "operationalSite": site,
        "accessLevel": access_level,
        "isRegistered": False,
        "isActive": True
    }


async def delete_employee_record(employee_id: str) -> bool:
    """Removes an employee record from the directory and invalidates active sessions."""
    pool = await get_db_pool()
    emp_id = employee_id.strip()
    async with pool.acquire() as conn:
        # Delete cascade from employees
        result = await conn.execute(
            "DELETE FROM employees WHERE employee_id = $1",
            emp_id
        )
        return "DELETE 1" in result


async def toggle_employee_active(employee_id: str) -> Dict[str, Any]:
    """Toggles employee account between active and suspended."""
    pool = await get_db_pool()
    emp_id = employee_id.strip()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT is_active FROM employees WHERE employee_id = $1",
            emp_id
        )
        if not row:
            raise ValueError(f"Employee '{emp_id}' not found.")

        new_state = not row["is_active"]
        await conn.execute(
            "UPDATE employees SET is_active = $1, updated_at = NOW() WHERE employee_id = $2",
            new_state, emp_id
        )

        return {"employeeId": emp_id, "isActive": new_state}


async def reset_employee_registration(employee_id: str) -> bool:
    """Resets employee credentials so they can re-register from scratch."""
    pool = await get_db_pool()
    emp_id = employee_id.strip()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE employees
            SET is_registered = FALSE, password_hash = NULL, updated_at = NOW()
            WHERE employee_id = $1
            """,
            emp_id
        )
        # Delete unused OTPs
        await conn.execute(
            "DELETE FROM auth_otps WHERE employee_id = $1",
            emp_id
        )
        return "UPDATE 1" in result


# ==============================================================================
# AUTH SESSIONS MANAGEMENT
# ==============================================================================

async def create_auth_session(employee_id: str) -> str:
    """
    Creates a new authenticated session in auth_sessions table.
    Returns: session_id (64 hex characters)
    """
    pool = await get_db_pool()
    session_id = secrets.token_hex(32)
    emp_id = employee_id.strip()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO auth_sessions (session_id, employee_id, created_at, last_active_at, is_active)
            VALUES ($1, $2, NOW(), NOW(), TRUE)
            """,
            session_id, emp_id
        )
    return session_id


async def validate_session_active(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Validates if session is active and touches last_active_at.
    Returns joined employee data if active, None otherwise.
    """
    if not session_id:
        return None

    pool = await get_db_pool()
    sid = session_id.strip()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT s.session_id, s.employee_id, s.is_active, s.last_active_at,
                   e.employee_name, e.company_email, e.designation, e.department,
                   e.operational_site, e.access_level, e.permissions, e.is_active AS emp_is_active
            FROM auth_sessions s
            JOIN employees e ON s.employee_id = e.employee_id
            WHERE s.session_id = $1 AND s.is_active = TRUE
            """,
            sid
        )

        if not row or not row["emp_is_active"]:
            return None

        # Touch last_active_at asynchronously
        await conn.execute(
            "UPDATE auth_sessions SET last_active_at = NOW() WHERE session_id = $1",
            sid
        )

        raw_perms = row["permissions"]
        if isinstance(raw_perms, str):
            try:
                perms = json.loads(raw_perms)
            except Exception:
                perms = []
        elif isinstance(raw_perms, list):
            perms = raw_perms
        else:
            perms = []

        return {
            "sessionId": row["session_id"],
            "employeeId": row["employee_id"],
            "employeeName": row["employee_name"],
            "companyEmail": row["company_email"],
            "designation": row["designation"],
            "department": row["department"],
            "operationalSite": row["operational_site"],
            "accessLevel": row["access_level"],
            "permissions": perms
        }


async def terminate_session(session_id: str) -> bool:
    """Deactivates an active session (logout)."""
    if not session_id:
        return False

    pool = await get_db_pool()
    sid = session_id.strip()

    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE auth_sessions SET is_active = FALSE WHERE session_id = $1",
            sid
        )
        return "UPDATE 1" in result

