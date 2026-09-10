import React, { useState, useRef } from 'react';
import { ArrowUp } from 'lucide-react';

export interface ChatInputProps {
  onSendMessage: (text: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSendMessage, disabled = false }: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = input.trim();
    if (trimmed && !disabled) {
      onSendMessage(trimmed);
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  };

  return (
    <div className="chat-input-wrapper">
      <div className="chat-input-inner">
        <form className="chat-input-form" onSubmit={handleSubmit}>
          <div className="chat-input-container">
            <textarea
              ref={textareaRef}
              id="chat-textarea"
              className="chat-textarea"
              placeholder="Type a message..."
              value={input}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={disabled}
            />
            <button
              type="submit"
              id="send-message-btn"
              className={`send-button ${input.trim() ? 'active' : ''}`}
              disabled={disabled || !input.trim()}
              aria-label="Send message"
            >
              <ArrowUp size={18} strokeWidth={2.5} />
            </button>
          </div>
        </form>
        <div className="chat-input-tagline">
          Knowledge-based Reasoning &amp; Intelligent Action
        </div>
      </div>
    </div>
  );
}
