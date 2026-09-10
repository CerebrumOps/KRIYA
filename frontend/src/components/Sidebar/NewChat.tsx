import React from 'react';
import { Plus } from 'lucide-react';

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
      >
        <Plus size={18} strokeWidth={2} />
        <span>New Chat</span>
      </button>
    </div>
  );
}
