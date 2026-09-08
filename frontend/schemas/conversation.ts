/**
 * KRIYA Frontend - Conversation Schemas (TypeScript)
 * Types for conversation sessions and database synchronization.
 */

import { ChatMessage } from './chat';

// Chat item for the panel: contains strictly id and name (no heavy messages content)
export interface ConversationListItem {
  id: string;
  name: string;
}

// Backwards-compatible alias for chats list
export type ConversationSummary = ConversationListItem;


export interface ConversationDetail {
  id: string;
  name: string;
  messages: ChatMessage[];
  created_at?: string;
  updated_at?: string;
}

export interface AppendExchangeRequest {
  user_message: string;
  assistant_response: string;
}

export interface GenerateTitleResponse {
  conversation_id: string;
  title: string;
}
