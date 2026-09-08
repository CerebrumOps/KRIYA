/**
 * KRIYA Frontend - Business Logic & Data Schemas (TypeScript)
 * Matches backend schemas for webchat communication.
 */

export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  role: MessageRole;
  content: string;
}

export interface WebChatRequest {
  user_message: string;
  history?: ChatMessage[];
  thinking?: boolean;
  model?: string;
  temperature?: number;
}

export interface WebChatResponse {
  reply: string;
  model_used: string;
  status: string;
}
