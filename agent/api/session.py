# ==============================================================================
# KRIYA Session Verification (Decoupled Client Appliance)
# ==============================================================================
# Verifies incoming HTTP Authorization Bearer tokens via cryptographic JWT
# verification using the shared JWT_SECRET.
# Completely decoupled from central PostgreSQL auth_sessions table.
# ==============================================================================

import os
import time
from typing import Any, Dict, Optional
import jwt
from fastapi import Header, Query, HTTPException, status
from dotenv import load_dotenv
from pathlib import Path

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
    Decodes and validates token signature and expiration locally.
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

    emp_id = payload.get("sub")
    if not emp_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload: missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "session_id": payload.get("sid"),
        "employee_id": emp_id,
        "name": payload.get("name", "Operator"),
        "email": payload.get("email", ""),
        "role": payload.get("role", "engineer"),
        "permissions": payload.get("permissions", []),
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
