/**
 * KRIYA Frontend - API Request Logics (TypeScript)
 * Handles communication with the KRIYA FastAPI backend.
 */

import { WebChatRequest, WebChatResponse } from '../schemas/chat';
import { getAuthHeaders } from './auth_api';

// Backend endpoint configured strictly from .env via Vite
const RAW_BACKEND_URL: string = import.meta.env.VITE_BACKEND_URL || '';
const BACKEND_URL: string = RAW_BACKEND_URL.replace(/\/+$/, '');

/**
 * Sends a chat request and streams back tokens in real-time.
 * 
 * @param request The chat request payload
 * @param onChunk Callback triggered when a new token chunk arrives
 * @param onComplete Callback triggered when the stream finishes
 * @param onError Callback triggered if an error occurs
 * @param backendUrl Optional custom backend base URL
 */
export async function streamChatMessage(
  request: WebChatRequest,
  onChunk: (token: string) => void,
  onComplete?: () => void,
  onError?: (err: Error) => void,
  backendUrl: string = BACKEND_URL
): Promise<void> {
  const base = (backendUrl || BACKEND_URL).replace(/\/+$/, '');
  if (!base) {
    const configError = new Error(
      'Backend URL is not configured. Please set VITE_BACKEND_URL=http://<BACKEND_IP>:5000 in your .env file and restart Vite.'
    );
    if (onError) {
      onError(configError);
      return;
    }
    throw configError;
  }
  const url = `${base}/api/chat/stream`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      let detail = '';
      try {
        const body = await response.json();
        detail = body.detail ? String(body.detail) : JSON.stringify(body);
      } catch {
        detail = await response.text().catch(() => '');
      }
      throw new Error(
        `Server returned error status ${response.status} from ${url}${detail ? `: ${detail}` : ''}`
      );
    }

    if (!response.body) {
      throw new Error('ReadableStream not supported in this browser.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      const textChunk = decoder.decode(value, { stream: true });
      onChunk(textChunk);
    }

    if (onComplete) {
      onComplete();
    }
  } catch (error: any) {
    if (onError) {
      onError(error instanceof Error ? error : new Error(String(error)));
    } else {
      console.error('Streaming error in chat_api:', error);
    }
  }
}

/**
 * Sends a standard non-streaming chat request.
 * 
 * @param request The chat request payload
 * @param backendUrl Optional custom backend base URL
 * @returns Promise resolving to WebChatResponse
 */
export async function sendChatMessage(
  request: WebChatRequest,
  backendUrl: string = BACKEND_URL
): Promise<WebChatResponse> {
  const base = (backendUrl || BACKEND_URL).replace(/\/+$/, '');
  if (!base) {
    throw new Error(
      'Backend URL is not configured. Please set VITE_BACKEND_URL=http://<BACKEND_IP>:5000 in your .env file and restart Vite.'
    );
  }
  const url = `${base}/api/chat`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let detail = '';
    try {
      const body = await response.json();
      detail = body.detail ? String(body.detail) : JSON.stringify(body);
    } catch {
      detail = await response.text().catch(() => '');
    }
    throw new Error(
      `Server returned error status ${response.status} from ${url}${detail ? `: ${detail}` : ''}`
    );
  }

  const data: WebChatResponse = await response.json();
  return data;
}
