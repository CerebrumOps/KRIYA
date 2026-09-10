import React from 'react';
import MessageList, { UIMessage } from './MessageList';
import ChatInput from './ChatInput';
import './ChatArea.css';

export interface ChatAreaProps {
  messages?: UIMessage[];
  onSendMessage: (text: string) => void;
  isLoading?: boolean;
}

export default function ChatArea({ 
  messages = [], 
  onSendMessage, 
  isLoading = false 
}: ChatAreaProps) {
  return (
    <main className="chat-area" aria-label="Main chat area">
      <MessageList 
        messages={messages} 
        isLoading={isLoading} 
        onSelectPrompt={onSendMessage} 
      />

      <ChatInput 
        onSendMessage={onSendMessage} 
        disabled={isLoading} 
      />
    </main>
  );
}
