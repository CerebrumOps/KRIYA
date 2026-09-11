import { getAuthHeaders } from './auth_api';

export interface ChecklistItem {
  id: string;
  task: string;
  tool?: string;
  status: 'pending' | 'in_progress' | 'success' | 'failed';
}

export interface PlanStep {
  step_id: number;
  title: string;
  tool: string;
  tool_args?: Record<string, any>;
  expected_output?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  actual_output?: string;
}

export interface Plan {
  plan_id: string;
  title: string;
  task_type?: string;
  skill?: string | null;
  model_profile?: string;
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'EXECUTING' | 'COMPLETED' | 'REJECTED';
  plan?: string;
  check_list?: ChecklistItem[];
  total_steps?: number;
  steps?: PlanStep[];
  approved_at?: number;
}

const RAW_BACKEND_URL: string = (import.meta as any).env?.VITE_BACKEND_URL || '';
const BACKEND_URL: string = RAW_BACKEND_URL.replace(/\/+$/, '');

export async function getActivePlan(backendUrl: string = BACKEND_URL): Promise<Plan | null> {
  const res = await fetch(`${backendUrl}/api/plan/active`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data.plan;
}

export async function createPlan(
  userPrompt: string,
  backendUrl: string = BACKEND_URL
): Promise<Plan> {
  const res = await fetch(`${backendUrl}/api/plan/create`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ user_prompt: userPrompt }),
  });
  if (!res.ok) throw new Error(`Failed to generate plan: ${res.status}`);
  const data = await res.json();
  return data.plan;
}

export async function approvePlan(
  planId: string,
  backendUrl: string = BACKEND_URL
): Promise<Plan> {
  const res = await fetch(`${backendUrl}/api/plan/${planId}/approve`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to approve plan: ${res.status}`);
  const data = await res.json();
  return data.plan;
}

export async function rejectPlan(
  planId: string,
  backendUrl: string = BACKEND_URL
): Promise<Plan> {
  const res = await fetch(`${backendUrl}/api/plan/${planId}/reject`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to reject plan: ${res.status}`);
  const data = await res.json();
  return data.plan;
}

export async function updatePlan(
  planId: string,
  updates: { plan?: string; check_list?: ChecklistItem[] },
  backendUrl: string = BACKEND_URL
): Promise<Plan> {
  const res = await fetch(`${backendUrl}/api/plan/${planId}/update`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error(`Failed to update plan: ${res.status}`);
  const data = await res.json();
  return data.plan;
}

export async function getPendingApprovals(backendUrl: string = BACKEND_URL): Promise<any[]> {
  const res = await fetch(`${backendUrl}/api/approvals/pending`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.pendingApprovals || [];
}

export async function resolveApproval(
  approvalId: string,
  approved: boolean,
  backendUrl: string = BACKEND_URL
): Promise<any> {
  const res = await fetch(`${backendUrl}/api/approvals/${approvalId}/resolve`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ approved }),
  });
  if (!res.ok) throw new Error(`Failed to resolve approval: ${res.status}`);
  return await res.json();
}
