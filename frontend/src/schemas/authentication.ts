/**
 * KRIYA Frontend - Authentication Schemas (TypeScript)
 * Type definitions for authentication user input, OTP handling, and UI state.
 * Strictly decoupled from backend implementations, authentication logic, and API calls.
 */

import { Employee } from './employee';

// Re-export Employee for convenient access from authentication schemas
export type { Employee };

/* ==========================================================================
   1. USER INPUT SCHEMAS
   ========================================================================== */

/**
 * User-entered login form data.
 * Supports identification via either corporate Employee ID or company Email.
 */
export interface LoginFormData {
  employeeId?: string;
  email?: string;
  password: string;
  otp: string;
}

/**
 * User-entered form data for the initial employee verification stage of registration.
 */
export interface EmployeeVerificationFormData {
  employeeId: string;
  otp: string;
}

/**
 * User-entered form data for the password creation stage of registration.
 */
export interface SetPasswordFormData {
  password: string;
  confirmPassword: string;
}

/* ==========================================================================
   2. OTP SCHEMAS
   ========================================================================== */

/**
 * Lifecycle verification statuses for OTP verification.
 */
export type OtpVerificationStatus =
  | 'idle'
  | 'sent'
  | 'verifying'
  | 'verified'
  | 'failed'
  | 'expired';

/**
 * Reusable OTP state structure tracking the code and visual verification state.
 */
export interface OtpState {
  otp: string;
  status: OtpVerificationStatus;
  destinationEmail?: string;
}

/* ==========================================================================
   3. BACKEND RESPONSE SCHEMAS
   ========================================================================== */

/**
 * Backend-provided response returned upon successful employee ID & OTP verification.
 */
export interface EmployeeVerificationResponse {
  verified: boolean;
  employee: Employee;
}

/* ==========================================================================
   4. AUTHENTICATION UI FLOW & STATE SCHEMAS
   ========================================================================== */

/**
 * Active authentication mode on the split-screen landscape interface.
 */
export type AuthMode = 'login' | 'registration';

/**
 * Visual stages within the registration flow.
 */
export type RegistrationStage = 'employee-verification' | 'set-password';

/**
 * Generic visual execution status for authentication actions.
 */
export type AuthStatus = 'idle' | 'loading' | 'success' | 'error';

/**
 * Consolidated UI state representing current authentication view and action status.
 */
export interface AuthUiState {
  mode: AuthMode;
  stage: RegistrationStage;
  status: AuthStatus;
  errorMessage?: string;
}

