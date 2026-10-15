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

/**
 * Transfers a deliverable directly into the host machine's shared directory (~/kriya-shared).
 */
export async function shareDeliverableToHost(
  chatId: string,
  filename: string,
  backendUrl: string = BACKEND_URL
): Promise<{ success: boolean; message: string; host_path?: string }> {
  const base = (backendUrl || BACKEND_URL).replace(/\/+$/, '');
  const url = `${base}/api/workspace/share-to-host`;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify({ chat_id: chatId, filename }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to export to host: ${res.status}`);
    }
    const data = await res.json();
    return {
      success: true,
      message: data.message || `Exported to ~/kriya-shared/${filename}`,
      host_path: data.host_path,
    };
  } catch (err: any) {
    return {
      success: false,
      message: err.message || String(err),
    };
  }
}

export interface UploadedFileItem {
  status: string;
  filename: string;
  path: string;
  size_bytes: number;
  content_type?: string;
  chat_id: string;
}

/**
 * Uploads an image, photo, or PDF document into the chat workspace for tool-based OCR analysis.
 */
export async function uploadFileToWorkspace(
  file: File,
  chatId?: string | null,
  backendUrl: string = BACKEND_URL
): Promise<UploadedFileItem> {
  const base = (backendUrl || BACKEND_URL).replace(/\/+$/, '');
  const url = `${base}/api/workspace/upload`;
  const formData = new FormData();
  formData.append('file', file);
  if (chatId) {
    formData.append('chat_id', chatId);
  }

  // IMPORTANT: Do NOT set 'Content-Type': 'application/json' for FormData!
  // The browser must automatically set 'Content-Type: multipart/form-data; boundary=...'
  const token = getStoredAuthToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detailMsg =
      typeof err.detail === 'string'
        ? err.detail
        : Array.isArray(err.detail)
        ? err.detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ')
        : err.detail
        ? JSON.stringify(err.detail)
        : `Upload failed with status ${res.status}`;
    throw new Error(detailMsg);
  }

  return await res.json();
}


