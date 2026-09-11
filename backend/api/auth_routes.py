# ==============================================================================
# KRIYA Authentication & Employee Directory REST API
# ==============================================================================
# Implements the official API contract from AUTHENTICATION_API_CONTRACT.md:
# Flow 1 (Registration):
#   - POST /auth/register/employee
#   - POST /auth/register/send-otp
#   - POST /auth/register/verify-otp
#   - POST /auth/register/set-password
# Flow 2 (Login):
#   - POST /auth/login
#   - POST /auth/login/verify-otp
# ==============================================================================

import os
import re
import time
from typing import Any, Dict, Optional
import jwt
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from backend.database.kriya_db.request.employee_db import (
    get_employee_by_id,
    get_employee_by_identifier,
    generate_and_store_otp,
    verify_registration_otp,
    verify_registration_token,
    set_employee_password,
    verify_password,
    verify_login_otp,
    mask_email,
    create_auth_session,
    terminate_session
)
from backend.database.kriya_db.schema.employee import (
    FetchEmployeeRequest,
    SendOtpRequest,
    VerifyOtpRequest,
    SetPasswordRequest,
    LoginCredentialsRequest,
    VerifyLoginOtpRequest,
)

router = APIRouter(tags=["Authentication"])

JWT_SECRET = os.getenv("JWT_SECRET", "kriya_sovereign_airgap_secret_2026_mrpl")
JWT_ALGORITHM = "HS256"


def make_error_response(status_code: int, code: str, message: str) -> JSONResponse:
    """Returns standardized JSON error envelope adhering to API contract."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message
            }
        }
    )


def validate_password_strength(password: str) -> bool:
    """
    Validates enterprise password policy:
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 digit
    - At least 1 special symbol
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
        return False
    return True


# ==============================================================================
# FLOW 1: NEW EMPLOYEE REGISTRATION
# ==============================================================================

@router.post("/auth/register/employee")
@router.post("/api/auth/register/employee")
async def register_fetch_employee(req: FetchEmployeeRequest):
    """
    Step 1: Check corporate directory, confirm eligibility, and return
    read-only profile details.
    """
    emp_id = req.employeeId.strip()
    if not emp_id:
        return make_error_response(400, "INVALID_IDENTIFIER", "Employee ID must not be empty.")

    emp = await get_employee_by_id(emp_id)
    if not emp:
        return make_error_response(
            404,
            "EMPLOYEE_NOT_FOUND",
            "The specified Employee ID was not found in the corporate directory."
        )

    if emp.get("is_registered"):
        return make_error_response(
            409,
            "EMPLOYEE_ALREADY_REGISTERED",
            "This Employee ID is already registered. Please sign in instead."
        )

    return {
        "employee": {
            "employeeId": emp["employee_id"],
            "employeeName": emp["employee_name"],
            "companyEmail": emp["company_email"],
            "designation": emp["designation"],
            "department": emp["department"],
            "operationalSite": emp["operational_site"]
        },
        "alreadyRegistered": False,
        "message": "Employee record found in corporate directory."
    }


@router.post("/auth/register/send-otp")
@router.post("/api/auth/register/send-otp")
async def register_send_otp(req: SendOtpRequest):
    """
    Step 2: Generate 6-digit OTP and dispatch to employee's registered corporate email.
    """
    emp_id = req.employeeId.strip()
    emp = await get_employee_by_id(emp_id)
    if not emp:
        return make_error_response(
            404,
            "EMPLOYEE_NOT_FOUND",
            "The specified Employee ID was not found in the corporate directory."
        )

    if emp.get("is_registered"):
        return make_error_response(
            409,
            "EMPLOYEE_ALREADY_REGISTERED",
            "This Employee ID is already registered. Please sign in instead."
        )

    otp_info = await generate_and_store_otp(emp_id, purpose="registration")

    return {
        "otpSent": True,
        "maskedEmail": otp_info["maskedEmail"],
        "expiresInSeconds": otp_info["expiresInSeconds"],
        "devOtp": otp_info.get("otpCode"),
        "message": "Verification code sent to registered company email."
    }


@router.post("/auth/register/verify-otp")
@router.post("/api/auth/register/verify-otp")
async def register_verify_otp(req: VerifyOtpRequest):
    """
    Step 3: Validate 6-digit OTP and return one-time verificationToken.
    """
    emp_id = req.employeeId.strip()
    otp_code = req.otp.strip()

    valid, token, error_code = await verify_registration_otp(emp_id, otp_code)
    if not valid:
        if error_code == "OTP_EXPIRED":
            return make_error_response(
                410,
                "OTP_EXPIRED",
                "The verification code has expired. Please request a new code."
            )
        return make_error_response(
            400,
            "INVALID_OTP",
            "The verification code entered is incorrect."
        )

    return {
        "verified": True,
        "verificationToken": token,
        "message": "Email verified successfully. Proceed to password creation."
    }


@router.post("/auth/register/set-password")
@router.post("/api/auth/register/set-password")
async def register_set_password(req: SetPasswordRequest):
    """
    Step 4: Verify verificationToken, enforce password policy, set bcrypt password,
    and activate employee account.
    """
    emp_id = req.employeeId.strip()
    plain_password = req.password
    token = req.verificationToken.strip()

    # Validate password complexity
    if not validate_password_strength(plain_password):
        return make_error_response(
            400,
            "PASSWORD_POLICY_VIOLATION",
            "Password must be at least 8 characters with 1 uppercase, 1 digit, and 1 special symbol."
        )

    # Validate verificationToken
    is_token_valid = await verify_registration_token(emp_id, token)
    if not is_token_valid:
        return make_error_response(
            401,
            "INVALID_VERIFICATION_TOKEN",
            "Registration session has expired or is invalid. Please restart verification."
        )

    # Update password in DB
    updated = await set_employee_password(emp_id, plain_password)
    if not updated:
        return make_error_response(
            500,
            "PASSWORD_SETUP_FAILED",
            "Failed to configure password. Please contact system administrator."
        )

    return JSONResponse(
        status_code=201,
        content={
            "success": True,
            "message": "Password configured successfully. Your account is now active."
        }
    )


# ==============================================================================
# FLOW 2: EXISTING EMPLOYEE LOGIN
# ==============================================================================

@router.post("/auth/login")
@router.post("/api/auth/login")
async def login_credentials(req: LoginCredentialsRequest):
    """
    Step 1: Validate primary credentials (ID or Email + Password).
    If valid, dispatch 2FA OTP and return verificationId.
    """
    identifier = req.employeeId or req.email
    if not identifier:
        return make_error_response(
            400,
            "INVALID_IDENTIFIER",
            "Either Employee ID or company email must be provided."
        )

    emp = await get_employee_by_identifier(identifier)
    if not emp:
        return make_error_response(
            401,
            "INVALID_CREDENTIALS",
            "Invalid employee credentials provided."
        )

    if not emp.get("is_active"):
        return make_error_response(
            403,
            "ACCOUNT_LOCKED_OR_INELIGIBLE",
            "This account is inactive or restricted from sovereign AI access."
        )

    # Verify password
    hashed_pwd = emp.get("password_hash")
    if not hashed_pwd or not verify_password(req.password, hashed_pwd):
        return make_error_response(
            401,
            "INVALID_CREDENTIALS",
            "Invalid employee credentials provided."
        )

    # Credentials are valid -> initiate 2FA OTP
    otp_info = await generate_and_store_otp(emp["employee_id"], purpose="login_2fa")

    return {
        "credentialsValid": True,
        "otpInitiated": True,
        "verificationId": otp_info["token"],
        "maskedEmail": otp_info["maskedEmail"],
        "expiresInSeconds": otp_info["expiresInSeconds"],
        "devOtp": otp_info.get("otpCode"),
        "message": "Primary credentials valid. Security code dispatched to registered email."
    }


@router.post("/auth/login/verify-otp")
@router.post("/api/auth/login/verify-otp")
async def login_verify_otp(req: VerifyLoginOtpRequest):
    """
    Step 2: Validate 2FA OTP against verificationId.
    Returns Bearer JWT session token, employee profile, and permissions.
    """
    v_id = req.verificationId.strip()
    otp_code = req.otp.strip()

    valid, emp_data, error_code = await verify_login_otp(v_id, otp_code)
    if not valid:
        if error_code == "OTP_EXPIRED":
            return make_error_response(
                410,
                "OTP_EXPIRED",
                "Login verification session has expired. Please sign in again."
            )
        if error_code == "ACCOUNT_LOCKED_OR_INELIGIBLE":
            return make_error_response(
                403,
                "ACCOUNT_LOCKED_OR_INELIGIBLE",
                "This account is inactive or restricted from sovereign AI access."
            )
        return make_error_response(
            400,
            "INVALID_OTP",
            "Invalid security code."
        )

    # Generate persistent DB session
    session_id = await create_auth_session(emp_data["employeeId"])

    # Generate JWT token embedding session ID
    payload = {
        "sub": emp_data["employeeId"],
        "sid": session_id,
        "name": emp_data["employeeName"],
        "email": emp_data["companyEmail"],
        "role": emp_data["access"]["level"],
        "exp": int(time.time()) + 86400  # 24 hours
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {
        "authenticated": True,
        "accessToken": token,
        "tokenType": "Bearer",
        "sessionId": session_id,
        "expiresIn": 86400,
        "employee": {
            "employeeId": emp_data["employeeId"],
            "employeeName": emp_data["employeeName"],
            "companyEmail": emp_data["companyEmail"],
            "designation": emp_data["designation"],
            "department": emp_data["department"],
            "operationalSite": emp_data["operationalSite"]
        },
        "access": emp_data["access"],
        "message": "Authentication successful. Welcome to KRIYA Sovereign AI."
    }


@router.post("/auth/logout")
@router.post("/api/auth/logout")
async def logout_employee(req: Optional[Dict[str, Any]] = None):
    """
    Deactivates active session in PostgreSQL and invalidates token.
    """
    if req and "sessionId" in req:
        await terminate_session(req["sessionId"])
    return {"success": True, "message": "Logged out successfully."}

