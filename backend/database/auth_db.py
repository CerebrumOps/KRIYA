# ==============================================================================
# KRIYA Authentication SQLite Database Engine
# ==============================================================================
# Self-contained, zero-external-dependency local database for employee auth,
# password hashing (bcrypt), OTP verification, and JWT session records.
# Stored at backend/data/kriya_auth.db.
# ==============================================================================

import asyncio
import json
import os
import random
import secrets
import sqlite3
import string
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import bcrypt

from backend.config import AUTH_DB_PATH

_is_initialized = False
_lock = asyncio.Lock()


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(AUTH_DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _init_schema_sync() -> None:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            employee_name TEXT NOT NULL,
            company_email TEXT NOT NULL UNIQUE,
            designation TEXT NOT NULL,
            department TEXT NOT NULL,
            operational_site TEXT NOT NULL DEFAULT 'Refinery Complex Alpha (Sector 4)',
            role_code TEXT NOT NULL DEFAULT 'ENG',
            clearance_level INTEGER NOT NULL DEFAULT 2,
            password_hash TEXT,
            is_registered INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            access_level TEXT NOT NULL DEFAULT 'process_engineer',
            permissions TEXT NOT NULL DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_emp_email ON employees (company_email);

        CREATE TABLE IF NOT EXISTS auth_otps (
            id TEXT PRIMARY KEY,
            employee_id TEXT NOT NULL,
            otp_code TEXT NOT NULL,
            purpose TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            is_used INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_otp_token ON auth_otps (token);
        CREATE INDEX IF NOT EXISTS idx_otp_emp ON auth_otps (employee_id, purpose);

        CREATE TABLE IF NOT EXISTS auth_sessions (
            session_id TEXT PRIMARY KEY,
            employee_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_emp ON auth_sessions (employee_id);
        """)
        conn.commit()


async def init_auth_db() -> None:
    global _is_initialized
    if _is_initialized:
        return
    async with _lock:
        if not _is_initialized:
            await asyncio.to_thread(_init_schema_sync)
            _is_initialized = True


# ── Queries & CRUD ────────────────────────────────────────────────────────────

def _get_employee_by_id_sync(employee_id: str) -> Optional[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


async def get_employee_by_id(employee_id: str) -> Optional[Dict[str, Any]]:
    await init_auth_db()
    return await asyncio.to_thread(_get_employee_by_id_sync, employee_id)


def _get_employee_by_identifier_sync(identifier: str) -> Optional[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        ident = identifier.strip().lower()
        cursor.execute(
            "SELECT * FROM employees WHERE LOWER(employee_id) = ? OR LOWER(company_email) = ?",
            (ident, ident)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


async def get_employee_by_identifier(identifier: str) -> Optional[Dict[str, Any]]:
    await init_auth_db()
    return await asyncio.to_thread(_get_employee_by_identifier_sync, identifier)


def _upsert_employee_sync(emp: Dict[str, Any]) -> None:
    with _get_connection() as conn:
        cursor = conn.cursor()
        permissions_json = json.dumps(emp.get("permissions", [])) if isinstance(emp.get("permissions"), list) else emp.get("permissions", "[]")
        cursor.execute("""
            INSERT INTO employees (
                employee_id, employee_name, company_email, designation, department,
                operational_site, role_code, clearance_level, password_hash,
                is_registered, is_active, access_level, permissions, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(employee_id) DO UPDATE SET
                employee_name = excluded.employee_name,
                company_email = excluded.company_email,
                designation = excluded.designation,
                department = excluded.department,
                operational_site = excluded.operational_site,
                role_code = excluded.role_code,
                clearance_level = excluded.clearance_level,
                access_level = excluded.access_level,
                permissions = excluded.permissions,
                updated_at = CURRENT_TIMESTAMP
        """, (
            emp["employee_id"],
            emp["employee_name"],
            emp["company_email"],
            emp["designation"],
            emp["department"],
            emp.get("operational_site", "Refinery Complex Alpha (Sector 4)"),
            emp.get("role_code", "ENG"),
            emp.get("clearance_level", 2),
            emp.get("password_hash"),
            1 if emp.get("is_registered") else 0,
            1 if emp.get("is_active", True) else 0,
            emp.get("access_level", "process_engineer"),
            permissions_json
        ))
        conn.commit()


async def upsert_employee(emp: Dict[str, Any]) -> None:
    await init_auth_db()
    await asyncio.to_thread(_upsert_employee_sync, emp)


def _list_all_employees_sync() -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees ORDER BY employee_id")
        return [dict(r) for r in cursor.fetchall()]


async def list_all_employees() -> List[Dict[str, Any]]:
    await init_auth_db()
    return await asyncio.to_thread(_list_all_employees_sync)


# ── OTP Management ────────────────────────────────────────────────────────────

def _generate_and_store_otp_sync(employee_id: str, purpose: str) -> Tuple[str, str]:
    otp_code = "".join(random.choices(string.digits, k=6))
    token = f"{purpose}_{secrets.token_urlsafe(32)}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO auth_otps (id, employee_id, otp_code, purpose, token, expires_at, is_used)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (str(uuid.uuid4()), employee_id, otp_code, purpose, token, expires_at.isoformat()))
        conn.commit()

    return otp_code, token


async def generate_and_store_otp(employee_id: str, purpose: str) -> Tuple[str, str]:
    await init_auth_db()
    return await asyncio.to_thread(_generate_and_store_otp_sync, employee_id, purpose)


def _verify_registration_otp_sync(employee_id: str, otp_code: str) -> Optional[str]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, token, expires_at FROM auth_otps
            WHERE employee_id = ? AND otp_code = ? AND purpose = 'registration' AND is_used = 0
            ORDER BY created_at DESC LIMIT 1
        """, (employee_id, otp_code.strip()))
        row = cursor.fetchone()
        if not row:
            return None

        # Check expiration
        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            return None

        # Mark OTP as used
        cursor.execute("UPDATE auth_otps SET is_used = 1 WHERE id = ?", (row["id"],))

        # Generate signed verificationToken for step 4
        verification_token = f"reg_verified_{secrets.token_urlsafe(32)}"
        cursor.execute("""
            INSERT INTO auth_otps (id, employee_id, otp_code, purpose, token, expires_at, is_used)
            VALUES (?, ?, '000000', 'step4_token', ?, ?, 0)
        """, (str(uuid.uuid4()), employee_id, verification_token, (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()))
        conn.commit()

        return verification_token


async def verify_registration_otp(employee_id: str, otp_code: str) -> Optional[str]:
    await init_auth_db()
    return await asyncio.to_thread(_verify_registration_otp_sync, employee_id, otp_code)


def _verify_registration_token_sync(employee_id: str, token: str) -> bool:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, expires_at FROM auth_otps
            WHERE employee_id = ? AND token = ? AND purpose = 'step4_token' AND is_used = 0
            LIMIT 1
        """, (employee_id, token.strip()))
        row = cursor.fetchone()
        if not row:
            return False

        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            return False

        # Mark token used
        cursor.execute("UPDATE auth_otps SET is_used = 1 WHERE id = ?", (row["id"],))
        conn.commit()
        return True


async def verify_registration_token(employee_id: str, token: str) -> bool:
    await init_auth_db()
    return await asyncio.to_thread(_verify_registration_token_sync, employee_id, token)


def _verify_login_otp_sync(verification_id: str, otp_code: str) -> Optional[str]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, employee_id, expires_at FROM auth_otps
            WHERE token = ? AND otp_code = ? AND purpose = 'login_2fa' AND is_used = 0
            LIMIT 1
        """, (verification_id.strip(), otp_code.strip()))
        row = cursor.fetchone()
        if not row:
            return None

        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            return None

        cursor.execute("UPDATE auth_otps SET is_used = 1 WHERE id = ?", (row["id"],))
        conn.commit()
        return row["employee_id"]


async def verify_login_otp(verification_id: str, otp_code: str) -> Optional[str]:
    await init_auth_db()
    return await asyncio.to_thread(_verify_login_otp_sync, verification_id, otp_code)


# ── Password Operations ───────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _set_employee_password_sync(employee_id: str, password: str) -> bool:
    hashed = hash_password(password)
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE employees
            SET password_hash = ?, is_registered = 1, updated_at = CURRENT_TIMESTAMP
            WHERE employee_id = ?
        """, (hashed, employee_id))
        conn.commit()
        return cursor.rowcount > 0


async def set_employee_password(employee_id: str, password: str) -> bool:
    await init_auth_db()
    return await asyncio.to_thread(_set_employee_password_sync, employee_id, password)


def _verify_password_sync(employee_id: str, password: str) -> bool:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM employees WHERE employee_id = ?", (employee_id,))
        row = cursor.fetchone()
        if not row or not row["password_hash"]:
            return False
        try:
            return bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8"))
        except Exception:
            return False


async def verify_password(employee_id: str, password: str) -> bool:
    await init_auth_db()
    return await asyncio.to_thread(_verify_password_sync, employee_id, password)


# ── Session Management ────────────────────────────────────────────────────────

def _create_auth_session_sync(employee_id: str) -> str:
    session_id = f"sess_{secrets.token_hex(16)}"
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO auth_sessions (session_id, employee_id, is_active)
            VALUES (?, ?, 1)
        """, (session_id, employee_id))
        conn.commit()
    return session_id


async def create_auth_session(employee_id: str) -> str:
    await init_auth_db()
    return await asyncio.to_thread(_create_auth_session_sync, employee_id)


def _terminate_session_sync(session_id: str) -> None:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE auth_sessions SET is_active = 0 WHERE session_id = ?", (session_id,))
        conn.commit()


async def terminate_session(session_id: str) -> None:
    await init_auth_db()
    await asyncio.to_thread(_terminate_session_sync, session_id)


# ── Admin Actions ─────────────────────────────────────────────────────────────

def _toggle_employee_active_sync(employee_id: str) -> Optional[bool]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_active FROM employees WHERE employee_id = ?", (employee_id,))
        row = cursor.fetchone()
        if not row:
            return None
        new_status = 0 if row["is_active"] else 1
        cursor.execute("UPDATE employees SET is_active = ? WHERE employee_id = ?", (new_status, employee_id))
        conn.commit()
        return bool(new_status)


async def toggle_employee_active(employee_id: str) -> Optional[bool]:
    await init_auth_db()
    return await asyncio.to_thread(_toggle_employee_active_sync, employee_id)


def _reset_employee_registration_sync(employee_id: str) -> bool:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE employees
            SET is_registered = 0, password_hash = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE employee_id = ?
        """, (employee_id,))
        conn.commit()
        return cursor.rowcount > 0


async def reset_employee_registration(employee_id: str) -> bool:
    await init_auth_db()
    return await asyncio.to_thread(_reset_employee_registration_sync, employee_id)


def _get_auth_stats_sync() -> Dict[str, int]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        total_emp = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM employees WHERE is_registered = 1")
        reg_emp = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM employees WHERE is_active = 1")
        act_emp = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM auth_sessions WHERE is_active = 1")
        act_sess = cursor.fetchone()[0]

        return {
            "totalEmployees": total_emp,
            "registeredEmployees": reg_emp,
            "activeEmployees": act_emp,
            "activeSessions": act_sess
        }


async def get_auth_stats() -> Dict[str, int]:
    await init_auth_db()
    return await asyncio.to_thread(_get_auth_stats_sync)


def mask_email(email: str) -> str:
    """Masks email address for display in OTP notifications (e.g. a***o@coastalrefinery.in)."""
    if "@" not in email:
        return "***"
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        masked_name = name[0] + "***"
    else:
        masked_name = name[0] + "***" + name[-1]
    return f"{masked_name}@{domain}"
