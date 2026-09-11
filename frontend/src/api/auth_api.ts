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
  devOtp?: string;
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
  devOtp?: string;
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
  sessionId?: string;
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

/* ==========================================================================
   5. CLIENT API CALLERS & STORAGE HELPERS
   ========================================================================== */

const RAW_BACKEND_URL: string = (import.meta as any).env?.VITE_BACKEND_URL || '';
const BACKEND_URL: string = RAW_BACKEND_URL.replace(/\/+$/, '');

async function handleResponse<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const errorMsg = data?.error?.message || `Request failed with status ${res.status}`;
    const err = new Error(errorMsg) as Error & { code?: string; status: number };
    err.code = data?.error?.code || 'API_ERROR';
    err.status = res.status;
    throw err;
  }
  return data as T;
}

export async function fetchEmployeeDetails(
  req: FetchEmployeeDetailsRequest,
  backendUrl: string = BACKEND_URL
): Promise<FetchEmployeeDetailsResponse> {
  const res = await fetch(`${backendUrl}${AUTH_ENDPOINTS.REGISTER_EMPLOYEE}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  return handleResponse<FetchEmployeeDetailsResponse>(res);
}

export async function sendRegistrationOtp(
  req: SendRegistrationOtpRequest,
  backendUrl: string = BACKEND_URL
): Promise<SendRegistrationOtpResponse> {
  const res = await fetch(`${backendUrl}${AUTH_ENDPOINTS.REGISTER_SEND_OTP}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  return handleResponse<SendRegistrationOtpResponse>(res);
}

export async function verifyRegistrationOtp(
  req: VerifyRegistrationOtpRequest,
  backendUrl: string = BACKEND_URL
): Promise<VerifyRegistrationOtpResponse> {
  const res = await fetch(`${backendUrl}${AUTH_ENDPOINTS.REGISTER_VERIFY_OTP}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  return handleResponse<VerifyRegistrationOtpResponse>(res);
}

export async function setRegistrationPassword(
  req: SetRegistrationPasswordRequest,
  backendUrl: string = BACKEND_URL
): Promise<SetRegistrationPasswordResponse> {
  const res = await fetch(`${backendUrl}${AUTH_ENDPOINTS.REGISTER_SET_PASSWORD}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  return handleResponse<SetRegistrationPasswordResponse>(res);
}

export async function loginCredentials(
  req: LoginCredentialsRequest,
  backendUrl: string = BACKEND_URL
): Promise<LoginCredentialsResponse> {
  const res = await fetch(`${backendUrl}${AUTH_ENDPOINTS.LOGIN}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  return handleResponse<LoginCredentialsResponse>(res);
}

export async function verifyLoginOtp(
  req: VerifyLoginOtpRequest,
  backendUrl: string = BACKEND_URL
): Promise<VerifyLoginOtpResponse> {
  const res = await fetch(`${backendUrl}${AUTH_ENDPOINTS.LOGIN_VERIFY_OTP}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  return handleResponse<VerifyLoginOtpResponse>(res);
}

// Session & Local Storage Management
const AUTH_TOKEN_KEY = 'kriya_auth_token';
const AUTH_EMPLOYEE_KEY = 'kriya_auth_employee';
const AUTH_ACCESS_KEY = 'kriya_auth_access';
const AUTH_SESSION_ID_KEY = 'kriya_auth_session_id';

export function storeAuthSession(auth: VerifyLoginOtpResponse): void {
  try {
    localStorage.setItem(AUTH_TOKEN_KEY, auth.accessToken);
    localStorage.setItem(AUTH_EMPLOYEE_KEY, JSON.stringify(auth.employee));
    if (auth.sessionId) {
      localStorage.setItem(AUTH_SESSION_ID_KEY, auth.sessionId);
    }
    if (auth.access) {
      localStorage.setItem(AUTH_ACCESS_KEY, JSON.stringify(auth.access));
    }
  } catch (e) {
    console.warn('Failed to persist auth session to localStorage', e);
  }
}

export function getStoredAuthToken(): string | null {
  try {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getStoredSessionId(): string | null {
  try {
    return localStorage.getItem(AUTH_SESSION_ID_KEY);
  } catch {
    return null;
  }
}

export function getAuthHeaders(): Record<string, string> {
  const token = getStoredAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export function getStoredEmployee(): Employee | null {
  try {
    const raw = localStorage.getItem(AUTH_EMPLOYEE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function getStoredAccess(): SafeEmployeeAccess | null {
  try {
    const raw = localStorage.getItem(AUTH_ACCESS_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function clearAuthSession(): void {
  try {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_EMPLOYEE_KEY);
    localStorage.removeItem(AUTH_ACCESS_KEY);
    localStorage.removeItem(AUTH_SESSION_ID_KEY);
  } catch (e) {
    console.warn('Failed to clear auth session', e);
  }
}

export async function logoutSession(): Promise<void> {
  const sessionId = getStoredSessionId();
  try {
    const rawUrl: string = (import.meta as any).env?.VITE_BACKEND_URL || '';
    const backendUrl = rawUrl.replace(/\/+$/, '');
    await fetch(`${backendUrl}/api/auth/logout`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ session_id: sessionId }),
    });
  } catch (e) {
    console.warn('Backend logout failed:', e);
  }
}
