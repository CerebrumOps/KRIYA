/**
 * KRIYA Authentication API Contract (TypeScript)
 * Location: frontend/src/api/auth_api.ts
 * 
 * Defines the formal REST API contract, endpoint routes, request payloads,
 * success responses, access control structures, and error models for the authentication system.
 * Strictly decoupled from backend implementations and database logic.
 */

import { Employee } from '../schemas/employee';

/* ==========================================================================
   1. ENDPOINT ROUTE PATHS
   ========================================================================== */

export const AUTH_ENDPOINTS = {
  // Registration Flow (Flow 1)
  REGISTER_EMPLOYEE: '/auth/register/employee',
  REGISTER_SEND_OTP: '/auth/register/send-otp',
  REGISTER_VERIFY_OTP: '/auth/register/verify-otp',
  REGISTER_SET_PASSWORD: '/auth/register/set-password',

  // Login Flow (Flow 2)
  LOGIN: '/auth/login',
  LOGIN_VERIFY_OTP: '/auth/login/verify-otp',
} as const;

/* ==========================================================================
   2. REGISTRATION CONTRACTS (FLOW 1 - NEW EMPLOYEE)
   ========================================================================== */

/**
 * 1. POST /auth/register/employee
 * Fetch and verify corporate directory information for an assigned Employee ID.
 */
export interface FetchEmployeeDetailsRequest {
  employeeId: string;
}

export interface FetchEmployeeDetailsResponse {
  employee: Employee;
  alreadyRegistered: boolean;
  message?: string;
}

/**
 * 2. POST /auth/register/send-otp
 * Request dispatch of registration verification OTP to employee's company email.
 * Destination email is determined solely by the backend.
 */
export interface SendRegistrationOtpRequest {
  employeeId: string;
}

export interface SendRegistrationOtpResponse {
  otpSent: boolean;
  maskedEmail: string;
  expiresInSeconds: number;
  message?: string;
}

/**
 * 3. POST /auth/register/verify-otp
 * Verify 6-digit OTP entered during registration.
 * Returns a temporary verificationToken required for setting password in Step 4.
 */
export interface VerifyRegistrationOtpRequest {
  employeeId: string;
  otp: string;
}

export interface VerifyRegistrationOtpResponse {
  verified: boolean;
  verificationToken: string;
  message?: string;
}

/**
 * 4. POST /auth/register/set-password
 * Activate credentials with new enterprise password and verification token.
 */
export interface SetRegistrationPasswordRequest {
  employeeId: string;
  password: string;
  verificationToken: string;
}

export interface SetRegistrationPasswordResponse {
  success: boolean;
  message: string;
}

/* ==========================================================================
   3. LOGIN CONTRACTS (FLOW 2 - EXISTING EMPLOYEE)
   ========================================================================== */

/**
 * 5. POST /auth/login
 * Step 1 of Login: Verify primary credentials (Employee ID OR Email + Password).
 * Initiates 2FA OTP dispatch to employee's registered corporate email.
 */
export interface LoginCredentialsRequest {
  employeeId?: string;
  email?: string;
  password: string;
}

export interface LoginCredentialsResponse {
  credentialsValid: boolean;
  otpInitiated: boolean;
  verificationId: string;
  maskedEmail: string;
  expiresInSeconds: number;
  message?: string;
}

/**
 * 6. POST /auth/login/verify-otp
 * Step 2 of Login: Verify 2FA OTP against the active login verificationId.
 * Completes authentication and returns session token, employee info, and permissions.
 */
export interface VerifyLoginOtpRequest {
  verificationId: string;
  otp: string;
}

/**
 * Safe designation, role, and permission metadata provided by the backend.
 * Backend is the sole source of truth for authorization rules.
 */
export interface SafeEmployeeAccess {
  level: string;
  permissions: string[];
}

export interface VerifyLoginOtpResponse {
  authenticated: boolean;
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  employee: Employee;
  access: SafeEmployeeAccess;
  message?: string;
}

/* ==========================================================================
   4. STANDARDIZED API ERROR CONTRACT
   ========================================================================== */

export type AuthErrorCode =
  | 'EMPLOYEE_NOT_FOUND'
  | 'EMPLOYEE_ALREADY_REGISTERED'
  | 'INVALID_IDENTIFIER'
  | 'INVALID_CREDENTIALS'
  | 'OTP_EXPIRED'
  | 'INVALID_OTP'
  | 'OTP_LIMIT_EXCEEDED'
  | 'REGISTRATION_VERIFICATION_FAILED'
  | 'INVALID_VERIFICATION_TOKEN'
  | 'PASSWORD_POLICY_VIOLATION'
  | 'PASSWORD_SETUP_FAILED'
  | 'AUTHENTICATION_FAILED'
  | 'ACCOUNT_LOCKED_OR_INELIGIBLE'
  | 'INTERNAL_SERVER_ERROR';

export interface AuthErrorDetail {
  code: AuthErrorCode | string;
  message: string;
}

export interface AuthErrorResponse {
  error: AuthErrorDetail;
}
