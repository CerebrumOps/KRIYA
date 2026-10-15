# ==============================================================================
# KRIYA Authentication Schemas (Pydantic v2)
# ==============================================================================
# Implements the official API contract from AUTHENTICATION_API_CONTRACT.md
# ==============================================================================

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EmployeePublicRecord(BaseModel):
    employeeId: str = Field(..., description="Corporate employee ID (e.g. EMP-1008)")
    employeeName: str = Field(..., description="Full legal employee name")
    companyEmail: str = Field(..., description="Official enterprise email address")
    designation: str = Field(..., description="Job designation / title")
    department: str = Field(..., description="Department or business unit")
    operationalSite: str = Field(..., description="Primary refinery site / complex")


class SafeEmployeeAccess(BaseModel):
    level: str = Field(..., description="Role clearance level or code (e.g. ENG, GM, TECH)")
    permissions: List[str] = Field(default_factory=list, description="List of capability permissions")


# Flow 1: Registration
class FetchEmployeeRequest(BaseModel):
    employeeId: str


class FetchEmployeeResponse(BaseModel):
    employee: EmployeePublicRecord
    alreadyRegistered: bool = False
    message: Optional[str] = None


class SendRegistrationOtpRequest(BaseModel):
    employeeId: str


class SendRegistrationOtpResponse(BaseModel):
    otpSent: bool = True
    maskedEmail: str
    expiresInSeconds: int = 300
    devOtp: Optional[str] = None
    message: Optional[str] = None


class VerifyRegistrationOtpRequest(BaseModel):
    employeeId: str
    otp: str


class VerifyRegistrationOtpResponse(BaseModel):
    verified: bool = True
    verificationToken: str
    message: Optional[str] = None


class SetRegistrationPasswordRequest(BaseModel):
    employeeId: str
    password: str
    verificationToken: str


class SetRegistrationPasswordResponse(BaseModel):
    success: bool = True
    message: str = "Password set successfully. Account activated."


# Flow 2: Login
class LoginCredentialsRequest(BaseModel):
    employeeId: Optional[str] = None
    email: Optional[str] = None
    password: str


class LoginCredentialsResponse(BaseModel):
    credentialsValid: bool = True
    otpInitiated: bool = True
    verificationId: str
    maskedEmail: str
    expiresInSeconds: int = 300
    devOtp: Optional[str] = None
    message: Optional[str] = None


class VerifyLoginOtpRequest(BaseModel):
    verificationId: str
    otp: str


class VerifyLoginOtpResponse(BaseModel):
    authenticated: bool = True
    accessToken: str
    tokenType: str = "Bearer"
    sessionId: Optional[str] = None
    expiresIn: int = 86400
    employee: EmployeePublicRecord
    access: SafeEmployeeAccess
    message: Optional[str] = None


# Session
class LogoutRequest(BaseModel):
    session_id: Optional[str] = None


class LogoutResponse(BaseModel):
    success: bool = True
    message: str = "Session terminated successfully."


# Admin Portal
class AdminEmployeeRecord(BaseModel):
    employeeId: str
    employeeName: str
    companyEmail: str
    designation: str
    department: str
    operationalSite: str
    roleCode: str
    clearanceLevel: int
    isRegistered: bool
    isActive: bool
    registeredAt: Optional[str] = None


class EnrollEmployeeRequest(BaseModel):
    employeeId: str
    employeeName: str
    companyEmail: str
    designation: str
    department: str
    operationalSite: str
    roleCode: Optional[str] = "ENG"
    clearanceLevel: Optional[int] = 2


class AdminStatsResponse(BaseModel):
    totalEmployees: int
    registeredEmployees: int
    activeEmployees: int
    activeSessions: int
