/**
 * KRIYA Frontend - Conversation API Request Logics (TypeScript)
 * Handles communication with the PostgreSQL conversation endpoints in KRIYA backend.
 */

import {
  ConversationListItem,
  ConversationSummary,
  ConversationDetail,
  GenerateTitleResponse,
} from '../schemas/conversation';

// Backend endpoint configured strictly from .env via Vite
const RAW_BACKEND_URL: string = import.meta.env.VITE_BACKEND_URL || '';
const BACKEND_URL: string = RAW_BACKEND_URL.replace(/\/+$/, '');

/**
 * Creates a new conversation in PostgreSQL.
 */
export async function createConversation(
  backendUrl: string = BACKEND_URL
): Promise<ConversationDetail> {
  const res = await fetch(`${backendUrl}/api/conversations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error(`Failed to create conversation: ${res.status}`);
  return await res.json();
}

/**
 * Lists all conversations for the chats panel (returns strictly ID and name,
 * content is only loaded when user clicks a particular chat).
 */
export async function listConversations(
  backendUrl: string = BACKEND_URL
): Promise<ConversationListItem[]> {
  const res = await fetch(`${backendUrl}/api/conversations`);
  if (!res.ok) throw new Error(`Failed to list conversations: ${res.status}`);
  return await res.json();
}


/**
 * Loads a specific conversation history from PostgreSQL.
 */
export async function getConversation(
  convId: string,
  backendUrl: string = BACKEND_URL
): Promise<ConversationDetail> {
  const res = await fetch(`${backendUrl}/api/conversations/${convId}`);
  if (!res.ok) throw new Error(`Failed to get conversation ${convId}: ${res.status}`);
  return await res.json();
}

/**
 * Appends a completed exchange into PostgreSQL.
 */
export async function saveMessageExchange(
  convId: string,
  userMessage: string,
  assistantResponse: string,
  backendUrl: string = BACKEND_URL
): Promise<void> {
  const res = await fetch(`${backendUrl}/api/conversations/${convId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_message: userMessage,
      assistant_response: assistantResponse,
    }),
  });
  if (!res.ok) throw new Error(`Failed to save message exchange: ${res.status}`);
}

/**
 * Calls the mini-titling agent to generate a 2-3 word title and saves it to PostgreSQL.
 */
export async function generateConversationTitle(
  convId: string,
  userMessage: string,
  assistantResponse: string,
  backendUrl: string = BACKEND_URL
): Promise<string> {
  const res = await fetch(`${backendUrl}/api/conversations/${convId}/generate-title`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_message: userMessage,
      assistant_response: assistantResponse,
    }),
  });
  if (!res.ok) throw new Error(`Failed to generate title: ${res.status}`);
  const data: GenerateTitleResponse = await res.json();
  return data.title;
}

/**
 * Deletes a conversation from PostgreSQL.
 */
export async function deleteConversation(
  convId: string,
  backendUrl: string = BACKEND_URL
): Promise<void> {
  const res = await fetch(`${backendUrl}/api/conversations/${convId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(`Failed to delete conversation: ${res.status}`);
}
