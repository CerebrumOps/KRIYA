/**
 * KRIYA Frontend - API Request Logics (TypeScript)
 * Handles communication with the KRIYA FastAPI backend.
 */

import { WebChatRequest, WebChatResponse } from '../schemas/chat';

// Default backend endpoint (port 5000 avoids 8000 and 8080)
const DEFAULT_BACKEND_URL = 'http://localhost:5000';

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
  backendUrl: string = DEFAULT_BACKEND_URL
): Promise<void> {
  const url = `${backendUrl}/api/chat/stream`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Server returned error status ${response.status}`);
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
  backendUrl: string = DEFAULT_BACKEND_URL
): Promise<WebChatResponse> {
  const url = `${backendUrl}/api/chat`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Server returned error status ${response.status}`);
  }

  const data: WebChatResponse = await response.json();
  return data;
}
