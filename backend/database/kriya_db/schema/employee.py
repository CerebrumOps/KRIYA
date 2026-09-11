# ==============================================================================
# KRIYA Database Schema: Corporate Employee Directory & Authentication
# ==============================================================================
# Defines the PostgreSQL table schema and Pydantic models for sovereign
# employee onboarding, identity verification, OTP lifecycle, and enterprise access.
# ==============================================================================

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# 1. SQL DDL to initialize the employees and auth_otps tables in PostgreSQL
CREATE_EMPLOYEES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS employees (
    employee_id VARCHAR(64) PRIMARY KEY,
    employee_name VARCHAR(255) NOT NULL,
    company_email VARCHAR(255) NOT NULL,
    designation VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    operational_site VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    is_registered BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    access_level VARCHAR(64) NOT NULL DEFAULT 'process_engineer',
    permissions JSONB NOT NULL DEFAULT '["chat:standard", "chat:reasoning", "tools:read_telemetry"]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_employees_email ON employees (company_email);

CREATE TABLE IF NOT EXISTS auth_otps (
    id VARCHAR(64) PRIMARY KEY,
    employee_id VARCHAR(64) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    otp_code VARCHAR(6) NOT NULL,
    purpose VARCHAR(32) NOT NULL, -- 'registration' or 'login_2fa'
    token VARCHAR(255) UNIQUE NOT NULL, -- verificationToken (reg) or verificationId (login)
    expires_at TIMESTAMPTZ NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_auth_otps_token ON auth_otps (token);
CREATE INDEX IF NOT EXISTS idx_auth_otps_employee ON auth_otps (employee_id, purpose);

CREATE TABLE IF NOT EXISTS auth_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    employee_id VARCHAR(64) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_sessions_emp ON auth_sessions (employee_id);
"""


# 2. Pydantic Models for Employee Data
class EmployeeBase(BaseModel):
    employee_id: str = Field(..., description="Corporate employee identifier (e.g. EMP-1001)")
    employee_name: str = Field(..., description="Full legal name")
    company_email: str = Field(..., description="Official corporate email address")
    designation: str = Field(..., description="Corporate job title")
    department: str = Field(..., description="Assigned organizational department")
    operational_site: str = Field(..., description="Primary refinery or facility site")


class EmployeePublicRecord(BaseModel):
    employeeId: str
    employeeName: str
    companyEmail: str
    designation: str
    department: str
    operationalSite: str


class SafeEmployeeAccess(BaseModel):
    level: str = Field(..., description="Access level, e.g. lead_engineer, process_engineer")
    permissions: List[str] = Field(default_factory=list, description="List of granular capability scopes")


# 3. Pydantic Models for Auth Requests and Responses
class FetchEmployeeRequest(BaseModel):
    employeeId: str


class FetchEmployeeResponse(BaseModel):
    employee: EmployeePublicRecord
    alreadyRegistered: bool = False
    message: Optional[str] = None


class SendOtpRequest(BaseModel):
    employeeId: str


class SendOtpResponse(BaseModel):
    otpSent: bool
    maskedEmail: str
    expiresInSeconds: int = 300
    message: Optional[str] = None


class VerifyOtpRequest(BaseModel):
    employeeId: str
    otp: str


class VerifyOtpResponse(BaseModel):
    verified: bool
    verificationToken: str
    message: Optional[str] = None


class SetPasswordRequest(BaseModel):
    employeeId: str
    password: str
    verificationToken: str


class SetPasswordResponse(BaseModel):
    success: bool
    message: str


class LoginCredentialsRequest(BaseModel):
    employeeId: Optional[str] = None
    email: Optional[str] = None
    password: str


class LoginCredentialsResponse(BaseModel):
    credentialsValid: bool
    otpInitiated: bool
    verificationId: str
    maskedEmail: str
    expiresInSeconds: int = 300
    message: Optional[str] = None


class VerifyLoginOtpRequest(BaseModel):
    verificationId: str
    otp: str


class VerifyLoginOtpResponse(BaseModel):
    authenticated: bool
    accessToken: str
    tokenType: str = "Bearer"
    expiresIn: int = 86400
    sessionId: Optional[str] = None
    employee: EmployeePublicRecord
    access: SafeEmployeeAccess
    message: Optional[str] = None


class EnrollEmployeeRequest(BaseModel):
    employeeId: str = Field(..., description="Corporate employee ID (e.g. EMP-2045)")
    employeeName: str = Field(..., description="Full legal employee name")
    companyEmail: str = Field(..., description="Enterprise email address")
    designation: str = Field(..., description="Corporate job title")
    department: str = Field(..., description="Department or business unit")
    operationalSite: str = Field(..., description="Primary site / refinery facility")
    accessLevel: str = Field(default="process_engineer", description="admin, lead_engineer, senior_engineer, process_engineer, or technician")
    permissions: Optional[List[str]] = Field(default=None, description="Granular permissions granted")
