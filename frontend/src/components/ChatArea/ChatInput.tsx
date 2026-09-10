import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';

export interface ChatInputProps {
  onSendMessage: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
  initialValue?: string;
}

export default function ChatInput({ 
  onSendMessage, 
  disabled = false,
  placeholder = "Search P&ID diagrams, review inspection reports, execute calculations and more....",
  initialValue = ""
}: ChatInputProps) {
  const [input, setInput] = useState(initialValue);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (initialValue) {
      setInput(initialValue);
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }
  }, [initialValue]);

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
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  };

  return (
    <div className="chat-input-wrapper">
      <div className="chat-input-inner">
        <form className="chat-input-form" onSubmit={handleSubmit}>
          <div className={`chat-prompt-card ${input.includes('\n') ? 'multiline' : ''}`}>
            <textarea
              ref={textareaRef}
              id="chat-textarea"
              className="chat-textarea"
              placeholder={placeholder}
              value={input}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={disabled}
            />

            <button
              type="submit"
              id="send-message-btn"
              className={`card-send-btn ${input.trim() ? 'active' : ''}`}
              disabled={disabled || !input.trim()}
              aria-label="Send message"
            >
              <span className="send-btn-label">Send</span>
              <div className="send-btn-icon-wrap">
                <ArrowUp size={13} strokeWidth={2.8} />
              </div>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
