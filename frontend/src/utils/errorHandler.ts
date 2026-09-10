/**
 * Generic Error Handler & Formatter for KRIYA AI
 * Converts arbitrary API errors, HTTP status codes, network dropouts,
 * and JSON exception payloads into clean, user-friendly, and actionable messages.
 */

export interface ErrorInfo {
  type: string;
  title: string;
  message: string;
  suggestion: string;
  status: number | null;
  technicalDetail: string;
}

/**
 * Extracts and classifies any error into a standardized, generic error descriptor.
 */
export function parseErrorInfo(error: any): ErrorInfo {
  let rawMessage = '';
  let status: number | null = error?.status || null;
  let rawDetail = '';

  if (typeof error === 'string') {
    rawMessage = error;
  } else if (error instanceof Error) {
    rawMessage = error.message || '';
    if ((error as any).status) status = (error as any).status;
    if ((error as any).rawBody) rawDetail = (error as any).rawBody;
  } else if (typeof error === 'object' && error !== null) {
    rawMessage = error.message || error.error || JSON.stringify(error);
    if (error.status) status = error.status;
  }

  // Extract HTTP status code from raw strings (e.g., "status 503", "HTTP 404", "status 429", "503:")
  if (!status) {
    const statusMatch = rawMessage.match(/\b(?:status\s*[:=]?\s*|HTTP\s*|code\s*[:=]?\s*)?([45]\d{2})\b/i);
    if (statusMatch && statusMatch[1]) {
      status = parseInt(statusMatch[1], 10);
    }
  }

  // Extract JSON payload embedded inside message text, e.g. {"detail":"All nodes serving 'qwen' are currently offline."}
  const jsonMatch = rawMessage.match(/(\{[\s\S]*\}|\[[\s\S]*\])/);
  if (jsonMatch) {
    try {
      const parsed = JSON.parse(jsonMatch[1]);
      if (parsed.detail) {
        rawDetail = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail);
      } else if (parsed.error?.message) {
        rawDetail = parsed.error.message;
      } else if (parsed.message) {
        rawDetail = parsed.message;
      } else {
        rawDetail = JSON.stringify(parsed);
      }
    } catch {
      // Non-JSON substring match, ignore
    }
  }

  // Combined lower-case search space for pattern matching
  const searchPool = `${rawMessage} ${rawDetail}`.toLowerCase();

  // 1. Service Unavailable / Server Overloaded / Offline Nodes (503, 502, 504)
  if (
    status === 503 ||
    status === 502 ||
    status === 504 ||
    searchPool.includes('offline') ||
    searchPool.includes('nodes serving') ||
    searchPool.includes('service unavailable') ||
    searchPool.includes('temporarily unavailable') ||
    searchPool.includes('bad gateway') ||
    searchPool.includes('gateway timeout')
  ) {
    return {
      type: 'service_unavailable',
      title: 'AI Service Temporarily Unavailable',
      message: 'The AI model is currently offline or undergoing temporary maintenance.',
      suggestion: 'Please try again in a few moments, or select a different model if available.',
      status: status || 503,
      technicalDetail: rawDetail || rawMessage,
    };
  }

  // 2. Network connection interrupted / Unreachable / CORS (Failed to fetch, net::ERR)
  if (
    searchPool.includes('failed to fetch') ||
    searchPool.includes('networkerror') ||
    searchPool.includes('connection refused') ||
    searchPool.includes('connection reset') ||
    searchPool.includes('err_connection') ||
    searchPool.includes('load failed') ||
    searchPool.includes('cors')
  ) {
    return {
      type: 'network_error',
      title: 'Connection Lost',
      message: 'Unable to reach the AI server. Your network connection may be unstable or the host is offline.',
      suggestion: 'Please verify your internet connection and ensure the host server is running.',
      status: null,
      technicalDetail: rawDetail || rawMessage,
    };
  }

  // 3. Rate Limit / Quota Exceeded (429)
  if (
    status === 429 ||
    searchPool.includes('rate limit') ||
    searchPool.includes('too many requests') ||
    searchPool.includes('quota exceeded')
  ) {
    return {
      type: 'rate_limited',
      title: 'Rate Limit Reached',
      message: 'Too many requests were sent in a short period of time.',
      suggestion: 'Please pause for a few seconds before trying again.',
      status: 429,
      technicalDetail: rawDetail || rawMessage,
    };
  }

  // 4. Authentication / Authorization issues (401, 403)
  if (
    status === 401 ||
    status === 403 ||
    searchPool.includes('unauthorized') ||
    searchPool.includes('forbidden') ||
    searchPool.includes('invalid api key') ||
    searchPool.includes('api key')
  ) {
    return {
      type: 'auth_error',
      title: 'Authentication Required',
      message: 'The AI service could not verify your access credentials.',
      suggestion: 'Please verify your API key and permissions.',
      status: status || 401,
      technicalDetail: rawDetail || rawMessage,
    };
  }

  // 5. Backend Configuration Missing
  if (
    searchPool.includes('backend url is not configured') ||
    searchPool.includes('vite_backend_url')
  ) {
    return {
      type: 'generic_error',
      title: 'Backend URL Not Configured',
      message: 'The frontend does not know where the backend server is running.',
      suggestion: 'Set VITE_BACKEND_URL=http://<BACKEND_IP>:5000 in your .env file and restart Vite.',
      status: 404,
      technicalDetail: rawDetail || rawMessage,
    };
  }

  // 5b. Model or Endpoint Not Found (404)
  if (
    status === 404 ||
    searchPool.includes('model not found') ||
    searchPool.includes('does not exist') ||
    searchPool.includes('not found')
  ) {
    const isModelSpecific = searchPool.includes('model');
    return {
      type: 'not_found',
      title: isModelSpecific ? 'Model Not Found' : 'Backend Endpoint Not Found (404)',
      message: isModelSpecific
        ? 'The requested AI model could not be found on the server.'
        : 'The backend endpoint was not found (404). Please ensure VITE_BACKEND_URL in .env points to port 5000 (not port 3000) with no trailing slash.',
      suggestion: isModelSpecific
        ? 'Please verify the model configuration or select another available model.'
        : 'Verify VITE_BACKEND_URL=http://<BACKEND_IP>:5000 in .env and restart Vite on the frontend host.',
      status: 404,
      technicalDetail: rawDetail || rawMessage,
    };
  }

  // 6. Context Window / Token Length Exceeded (400)
  if (
    searchPool.includes('context_length') ||
    searchPool.includes('maximum context') ||
    searchPool.includes('token limit') ||
    searchPool.includes('too long')
  ) {
    return {
      type: 'context_length',
      title: 'Conversation Exceeds Token Limit',
      message: 'This conversation has exceeded the maximum token capacity supported by the model.',
      suggestion: 'Start a new chat or shorten your recent messages to continue.',
      status: 400,
      technicalDetail: rawDetail || rawMessage,
    };
  }

  // 7. Request Timeout / Aborted
  if (
    searchPool.includes('abort') ||
    searchPool.includes('timeout') ||
    searchPool.includes('timed out')
  ) {
    return {
      type: 'timeout',
      title: 'Request Timed Out',
      message: 'The AI model took too long to generate a response.',
      suggestion: 'Please try sending your message again or try a shorter prompt.',
      status: 408,
      technicalDetail: rawDetail || rawMessage,
    };
  }

  // 8. Internal Server Error (500)
  if (status === 500) {
    return {
      type: 'server_error',
      title: 'Internal Server Error',
      message: 'The AI server encountered an unexpected error while generating the response.',
      suggestion: 'Please try again in a few moments.',
      status: 500,
      technicalDetail: rawDetail || rawMessage,
    };
  }

  // 9. Generic Fallback for any other error
  return {
    type: 'generic_error',
    title: 'Unable to Complete Request',
    message: 'An unexpected issue occurred while processing your request.',
    suggestion: 'Please try sending your message again. If the issue persists, try switching models or restarting the chat.',
    status: status || null,
    technicalDetail: rawDetail || rawMessage,
  };
}

/**
 * Returns a clean, generic Markdown string representation of the error.
 * Used for clipboard copying or fallback markdown rendering.
 */
export function formatErrorMarkdown(errorInfo?: ErrorInfo | null): string {
  if (!errorInfo) {
    return '⚠️ **Unable to Complete Request**\n\nAn unexpected error occurred. Please try again.';
  }

  return `⚠️ **${errorInfo.title}**\n\n${errorInfo.message}\n\n*Tip: ${errorInfo.suggestion}*`;
}
