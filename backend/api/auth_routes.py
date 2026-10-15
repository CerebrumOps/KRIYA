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
# Session:
#   - POST /api/auth/logout
# ==============================================================================

import json
import time
from typing import Any, Dict, Optional

import jwt
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from backend.config import JWT_ALGORITHM, JWT_EXPIRATION_SECONDS, JWT_SECRET
from backend.database.auth_db import (
    create_auth_session,
    generate_and_store_otp,
    get_employee_by_id,
    get_employee_by_identifier,
    mask_email,
    set_employee_password,
    terminate_session,
    verify_login_otp,
    verify_password,
    verify_registration_otp,
    verify_registration_token,
)
from backend.schemas.auth import (
    EmployeePublicRecord,
    FetchEmployeeRequest,
    FetchEmployeeResponse,
    LoginCredentialsRequest,
    LoginCredentialsResponse,
    LogoutRequest,
    LogoutResponse,
    SafeEmployeeAccess,
    SendRegistrationOtpRequest,
    SendRegistrationOtpResponse,
    SetRegistrationPasswordRequest,
    SetRegistrationPasswordResponse,
    VerifyLoginOtpRequest,
    VerifyLoginOtpResponse,
    VerifyRegistrationOtpRequest,
    VerifyRegistrationOtpResponse,
)

router = APIRouter(tags=["Authentication"])


def _err(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}}
    )


# ── Flow 1: New Employee Registration ─────────────────────────────────────────

@router.post("/auth/register/employee", response_model=FetchEmployeeResponse)
async def register_fetch_employee(req: FetchEmployeeRequest):
    """
    Step 1 of Registration: Validates Employee ID and returns directory information.
    """
    emp = await get_employee_by_id(req.employeeId.strip())
    if not emp:
        return _err(
            status.HTTP_404_NOT_FOUND,
            "EMPLOYEE_NOT_FOUND",
            f"The specified Employee ID '{req.employeeId}' was not found in the corporate directory."
        )

    if emp.get("is_registered"):
        return _err(
            status.HTTP_409_CONFLICT,
            "EMPLOYEE_ALREADY_REGISTERED",
            "This Employee ID is already registered. Please sign in instead."
        )

    return FetchEmployeeResponse(
        employee=EmployeePublicRecord(
            employeeId=emp["employee_id"],
            employeeName=emp["employee_name"],
            companyEmail=emp["company_email"],
            designation=emp["designation"],
            department=emp["department"],
            operationalSite=emp.get("operational_site", "Refinery Complex Alpha (Sector 4)")
        ),
        alreadyRegistered=False,
        message="Employee record found in corporate directory."
    )


@router.post("/auth/register/send-otp", response_model=SendRegistrationOtpResponse)
async def register_send_otp(req: SendRegistrationOtpRequest):
    """
    Step 2 of Registration: Dispatches registration OTP to employee's company email.
    """
    emp = await get_employee_by_id(req.employeeId.strip())
    if not emp:
        return _err(
            status.HTTP_404_NOT_FOUND,
            "EMPLOYEE_NOT_FOUND",
            "Employee ID not found in directory."
        )

    if emp.get("is_registered"):
        return _err(
            status.HTTP_409_CONFLICT,
            "EMPLOYEE_ALREADY_REGISTERED",
            "Employee is already registered."
        )

    otp_code, _ = await generate_and_store_otp(emp["employee_id"], "registration")
    masked = mask_email(emp["company_email"])

    return SendRegistrationOtpResponse(
        otpSent=True,
        maskedEmail=masked,
        expiresInSeconds=300,
        devOtp=otp_code,
        message=f"Verification code sent to {masked}."
    )


@router.post("/auth/register/verify-otp", response_model=VerifyRegistrationOtpResponse)
async def register_verify_otp(req: VerifyRegistrationOtpRequest):
    """
    Step 3 of Registration: Validates 6-digit OTP and returns temporary verificationToken.
    """
    emp = await get_employee_by_id(req.employeeId.strip())
    if not emp:
        return _err(status.HTTP_404_NOT_FOUND, "EMPLOYEE_NOT_FOUND", "Employee ID not found.")

    token = await verify_registration_otp(emp["employee_id"], req.otp)
    if not token:
        return _err(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_OTP",
            "The entered registration OTP is incorrect or has expired. Please try again."
        )

    return VerifyRegistrationOtpResponse(
        verified=True,
        verificationToken=token,
        message="Registration OTP verified successfully."
    )


@router.post("/auth/register/set-password", response_model=SetRegistrationPasswordResponse)
async def register_set_password(req: SetRegistrationPasswordRequest):
    """
    Step 4 of Registration: Sets enterprise password with valid verificationToken.
    """
    if len(req.password) < 6:
        return _err(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "PASSWORD_POLICY_VIOLATION",
            "Password must be at least 6 characters long."
        )

    valid = await verify_registration_token(req.employeeId.strip(), req.verificationToken)
    if not valid:
        return _err(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_VERIFICATION_TOKEN",
            "Invalid or expired verification token. Please restart registration."
        )

    success = await set_employee_password(req.employeeId.strip(), req.password)
    if not success:
        return _err(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "PASSWORD_SETUP_FAILED",
            "Failed to update employee password."
        )

    return SetRegistrationPasswordResponse(
        success=True,
        message="Password set successfully. Your account is now active and ready for sign-in."
    )


# ── Flow 2: Existing Employee Login ───────────────────────────────────────────

@router.post("/auth/login", response_model=LoginCredentialsResponse)
async def login_credentials(req: LoginCredentialsRequest):
    """
    Step 1 of Login: Verifies primary credentials and initiates 2FA OTP.
    """
    identifier = req.employeeId or req.email
    if not identifier:
        return _err(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_IDENTIFIER",
            "Please provide either Employee ID or Corporate Email."
        )

    emp = await get_employee_by_identifier(identifier)
    if not emp:
        return _err(
            status.HTTP_401_UNAUTHORIZED,
            "INVALID_CREDENTIALS",
            "Invalid Employee ID / Email or Password."
        )

    if not emp.get("is_active"):
        return _err(
            status.HTTP_403_FORBIDDEN,
            "ACCOUNT_LOCKED_OR_INELIGIBLE",
            "This account is inactive. Please contact the sovereign system administrator."
        )

    if not emp.get("is_registered") or not emp.get("password_hash"):
        return _err(
            status.HTTP_403_FORBIDDEN,
            "ACCOUNT_LOCKED_OR_INELIGIBLE",
            "Account has not been activated yet. Please complete registration first."
        )

    valid_pw = await verify_password(emp["employee_id"], req.password)
    if not valid_pw:
        return _err(
            status.HTTP_401_UNAUTHORIZED,
            "INVALID_CREDENTIALS",
            "Invalid Employee ID / Email or Password."
        )

    # Initiate 2FA OTP
    otp_code, verification_id = await generate_and_store_otp(emp["employee_id"], "login_2fa")
    masked = mask_email(emp["company_email"])

    return LoginCredentialsResponse(
        credentialsValid=True,
        otpInitiated=True,
        verificationId=verification_id,
        maskedEmail=masked,
        expiresInSeconds=300,
        devOtp=otp_code,
        message=f"Credentials verified. 2FA verification code sent to {masked}."
    )


@router.post("/auth/login/verify-otp", response_model=VerifyLoginOtpResponse)
async def login_verify_otp(req: VerifyLoginOtpRequest):
    """
    Step 2 of Login: Verifies 2FA OTP and issues signed JWT access token.
    """
    emp_id = await verify_login_otp(req.verificationId, req.otp)
    if not emp_id:
        return _err(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_OTP",
            "Invalid or expired 2FA verification code."
        )

    emp = await get_employee_by_id(emp_id)
    if not emp:
        return _err(status.HTTP_404_NOT_FOUND, "EMPLOYEE_NOT_FOUND", "Employee not found.")

    # Create session record
    session_id = await create_auth_session(emp_id)

    # Parse permissions
    permissions = []
    raw_perms = emp.get("permissions")
    if isinstance(raw_perms, list):
        permissions = raw_perms
    elif isinstance(raw_perms, str):
        try:
            permissions = json.loads(raw_perms)
        except Exception:
            permissions = []

    # Issue JWT token matching agent/api/session.py verification
    now = int(time.time())
    payload = {
        "sub": emp["employee_id"],
        "sid": session_id,
        "name": emp["employee_name"],
        "email": emp["company_email"],
        "role": emp.get("role_code", "ENG"),
        "clearance_level": emp.get("clearance_level", 2),
        "permissions": permissions,
        "iat": now,
        "exp": now + JWT_EXPIRATION_SECONDS
    }
    access_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return VerifyLoginOtpResponse(
        authenticated=True,
        accessToken=access_token,
        tokenType="Bearer",
        sessionId=session_id,
        expiresIn=JWT_EXPIRATION_SECONDS,
        employee=EmployeePublicRecord(
            employeeId=emp["employee_id"],
            employeeName=emp["employee_name"],
            companyEmail=emp["company_email"],
            designation=emp["designation"],
            department=emp["department"],
            operationalSite=emp.get("operational_site", "Refinery Complex Alpha (Sector 4)")
        ),
        access=SafeEmployeeAccess(
            level=emp.get("role_code", "ENG"),
            permissions=permissions
        ),
        message=f"Authentication successful. Welcome, {emp['employee_name']}."
    )


# ── Session Termination ───────────────────────────────────────────────────────

@router.post("/api/auth/logout", response_model=LogoutResponse)
async def logout(req: LogoutRequest):
    """
    Terminates the active session.
    """
    if req.session_id:
        await terminate_session(req.session_id)
    return LogoutResponse(success=True, message="Session terminated successfully.")
