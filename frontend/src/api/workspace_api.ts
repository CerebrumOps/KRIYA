/**
 * KRIYA Frontend - Workspace & Deliverables API Contract (TypeScript)
 * Handles listing and downloading generated deliverable artifacts scoped
 * to the authenticated employee and specific chat workspace.
 */

import { getAuthHeaders, getStoredAuthToken } from './auth_api';

const RAW_BACKEND_URL: string = import.meta.env.VITE_BACKEND_URL || '';
const BACKEND_URL: string = RAW_BACKEND_URL.replace(/\/+$/, '');

export interface DeliverableItem {
  id: string;
  name: string;
  type: 'docx' | 'xlsx' | 'pptx' | 'csv' | 'pdf' | 'json' | 'png' | 'file';
  title: string;
  description: string;
  size: string;
  size_bytes?: number;
  generated_at: string;
  status: 'verified' | 'draft';
  download_url: string;
}

/**
 * Fetches real deliverables from the active chat's workspace directory.
 */
export async function fetchDeliverables(
  chatId?: string | null,
  backendUrl: string = BACKEND_URL
): Promise<DeliverableItem[]> {
  if (!chatId) return [];
  const base = (backendUrl || BACKEND_URL).replace(/\/+$/, '');
  try {
    const res = await fetch(`${base}/api/workspace/deliverables?chat_id=${encodeURIComponent(chatId)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      console.warn(`Failed to fetch deliverables for chat ${chatId}: ${res.status}`);
      return [];
    }
    const data = await res.json();
    return data.deliverables || [];
  } catch (err) {
    console.error(`Error fetching deliverables for chat ${chatId}:`, err);
    return [];
  }
}

/**
 * Constructs direct download URL including session token query parameter.
 */
export function getFileDownloadUrl(
  chatId: string,
  filename: string,
  backendUrl: string = BACKEND_URL
): string {
  const base = (backendUrl || BACKEND_URL).replace(/\/+$/, '');
  const token = getStoredAuthToken();
  const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : '';
  return `${base}/api/workspace/download/${encodeURIComponent(chatId)}/${encodeURIComponent(filename)}${tokenQuery}`;
}

/**
 * Initiates direct browser blob download of a deliverable artifact.
 */
export async function downloadDeliverable(
  chatId: string,
  filename: string,
  backendUrl: string = BACKEND_URL
): Promise<void> {
  const base = (backendUrl || BACKEND_URL).replace(/\/+$/, '');
  const url = `${base}/api/workspace/download/${encodeURIComponent(chatId)}/${encodeURIComponent(filename)}`;
  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(`Failed to download file ${filename}: ${res.status}`);
  }
  const blob = await res.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(downloadUrl);
}
