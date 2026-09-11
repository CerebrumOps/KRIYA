# ==============================================================================
# KRIYA Session Authentication & Verification Dependency
# ==============================================================================
# Verifies incoming HTTP Authorization Bearer tokens against the auth_sessions table
# and JWT signatures, returning active employee and session metadata.
# ==============================================================================

import os
import time
from typing import Any, Dict, Optional
import jwt
from fastapi import Header, Query, HTTPException, status
from dotenv import load_dotenv
from pathlib import Path

from backend.database.kriya_db.request.employee_db import (
    validate_session_active,
    terminate_session,
)

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

JWT_SECRET = os.getenv("JWT_SECRET", "kriya_sovereign_airgap_secret_2026_mrpl")
JWT_ALGORITHM = "HS256"


async def get_current_session(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    token_param: Optional[str] = Query(None, alias="token")
) -> Dict[str, Any]:
    """
    Enforces valid Bearer JWT session authentication via Authorization header or ?token= query param.
    Validates token signature, expiration, and PostgreSQL auth_sessions state.
    """
    token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
        elif len(parts) == 1:
            token = parts[0].strip()
    elif token_param:
        token = token_param.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing. Please authenticate.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token signature.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sid = payload.get("sid")
    emp_id = payload.get("sub")

    if not emp_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate against auth_sessions table if sid is present
    if sid:
        session_record = await validate_session_active(sid)
        if not session_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session is terminated, revoked, or inactive.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            "session_id": sid,
            "employee_id": emp_id,
            "name": session_record.get("employeeName", payload.get("name")),
            "email": session_record.get("companyEmail", payload.get("email")),
            "role": session_record.get("accessLevel", payload.get("role")),
            "permissions": session_record.get("permissions", []),
        }

    # Fallback if legacy token without sid
    return {
        "session_id": None,
        "employee_id": emp_id,
        "name": payload.get("name"),
        "email": payload.get("email"),
        "role": payload.get("role"),
        "permissions": [],
    }


async def get_optional_session(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    token_param: Optional[str] = Query(None, alias="token")
) -> Optional[Dict[str, Any]]:
    """
    Returns session dict if valid Bearer token provided, else None without raising 401.
    """
    if not authorization and not token_param:
        return None
    try:
        return await get_current_session(authorization, token_param)
    except HTTPException:
        return None
