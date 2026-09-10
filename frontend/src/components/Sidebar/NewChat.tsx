import React from 'react';
import { SquarePen } from 'lucide-react';

export interface NewChatProps {
  onNewChat: () => void;
}

export default function NewChat({ onNewChat }: NewChatProps) {
  return (
    <div className="new-chat-container">
      <button 
        type="button" 
        className="new-chat-btn"
        onClick={onNewChat}
        id="new-chat-btn"
        aria-label="Start a new chat session"
      >
        <SquarePen size={16} strokeWidth={2.2} className="new-chat-icon" />
        <span>New Chat</span>
      </button>
    </div>
  );
}
