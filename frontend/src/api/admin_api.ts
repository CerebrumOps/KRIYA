/**
 * KRIYA Sovereign Administration API Client (TypeScript)
 * Location: frontend/src/api/admin_api.ts
 *
 * REST API client for administrative actions:
 * - Listing corporate employee directory
 * - Enrolling new corporate employee IDs
 * - Toggling account activation / suspension
 * - Resetting employee credentials / registration state
 * - Deleting employee directory entries
 * - Fetching high-level refinery & air-gap telemetry
 */

import { getStoredAuthToken } from './auth_api';

const RAW_BACKEND_URL: string = (import.meta as any).env?.VITE_BACKEND_URL || '';
const BACKEND_URL: string = RAW_BACKEND_URL.replace(/\/+$/, '');

export interface AdminEmployee {
  employee_id: string;
  employee_name: string;
  company_email: string;
  designation: string;
  department: string;
  operational_site: string;
  access_level: string;
  permissions: string[];
  is_registered: boolean;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface EnrollEmployeePayload {
  employeeId: string;
  employeeName: string;
  companyEmail: string;
  designation: string;
  department: string;
  operationalSite: string;
  accessLevel: string;
  permissions?: string[];
}

export interface AdminMetrics {
  totalEmployees: number;
  registeredEmployees: number;
  pendingRegistration: number;
  activeEmployees: number;
  suspendedEmployees: number;
  adminCount: number;
  distinctSites: number;
  refineryUnits: number;
}

export interface AdminStatsResponse {
  success: boolean;
  metrics: AdminMetrics;
  airGapStatus: {
    networkMesh: string;
    database: string;
    modelBalancer: string;
    sandboxEnvironment: string;
  };
}

function getAuthHeaders(): HeadersInit {
  const token = getStoredAuthToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function handleAdminResponse<T>(res: Response): Promise<T> {
  let data: any;
  try {
    data = await res.json();
  } catch {
    throw new Error(`Server returned status ${res.status}`);
  }

  if (!res.ok) {
    const msg = data?.error?.message || data?.detail || `Admin request failed with status ${res.status}`;
    throw new Error(msg);
  }

  return data as T;
}

export async function fetchAdminEmployees(): Promise<AdminEmployee[]> {
  const res = await fetch(`${BACKEND_URL}/api/admin/employees`, {
    headers: getAuthHeaders(),
  });
  const data = await handleAdminResponse<{ success: boolean; employees: AdminEmployee[] }>(res);
  return data.employees || [];
}

export async function enrollEmployee(payload: EnrollEmployeePayload): Promise<any> {
  const res = await fetch(`${BACKEND_URL}/api/admin/employees`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  return handleAdminResponse<any>(res);
}

export async function deleteEmployee(employeeId: string): Promise<any> {
  const res = await fetch(`${BACKEND_URL}/api/admin/employees/${encodeURIComponent(employeeId)}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  return handleAdminResponse<any>(res);
}

export async function toggleEmployeeActive(employeeId: string): Promise<{ success: boolean; employeeId: string; isActive: boolean }> {
  const res = await fetch(`${BACKEND_URL}/api/admin/employees/${encodeURIComponent(employeeId)}/toggle-active`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
  });
  return handleAdminResponse<{ success: boolean; employeeId: string; isActive: boolean }>(res);
}

export async function resetEmployeeRegistration(employeeId: string): Promise<any> {
  const res = await fetch(`${BACKEND_URL}/api/admin/employees/${encodeURIComponent(employeeId)}/reset-registration`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return handleAdminResponse<any>(res);
}

export async function fetchAdminStats(): Promise<AdminStatsResponse> {
  const res = await fetch(`${BACKEND_URL}/api/admin/stats`, {
    headers: getAuthHeaders(),
  });
  return handleAdminResponse<AdminStatsResponse>(res);
}
