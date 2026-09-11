import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Layers, Loader2, X, Sparkles } from 'lucide-react';

export interface ChatInputProps {
  onSendMessage: (text: string) => void;
  onRequestPlan?: (text: string) => void;
  disabled?: boolean;
  isPlanning?: boolean;
  placeholder?: string;
  initialValue?: string;
}

export default function ChatInput({ 
  onSendMessage, 
  onRequestPlan,
  disabled = false,
  isPlanning = false,
  placeholder = "Search P&ID diagrams, review inspection reports, execute calculations and more....",
  initialValue = ""
}: ChatInputProps) {
  const [input, setInput] = useState(initialValue);
  const [isPlanMode, setIsPlanMode] = useState(false);
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
    if (e.key === 'Escape' && isPlanMode) {
      e.preventDefault();
      setIsPlanMode(false);
      return;
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = input.trim();
    if (trimmed && !disabled && !isPlanning) {
      if (isPlanMode && onRequestPlan) {
        onRequestPlan(trimmed);
        setInput('');
        setIsPlanMode(false);
      } else {
        onSendMessage(trimmed);
        setInput('');
      }
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handlePlanClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (disabled || isPlanning) return;

    const trimmed = input.trim();
    if (trimmed && onRequestPlan) {
      // If user has already typed a prompt and clicks Plan, wake up planner immediately!
      onRequestPlan(trimmed);
      setInput('');
      setIsPlanMode(false);
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    } else {
      // If input is empty (or user wants to toggle mode), enter/exit Plan Mode
      setIsPlanMode((prev) => !prev);
      if (textareaRef.current) {
        textareaRef.current.focus();
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

  const activePlaceholder = isPlanMode
    ? "Describe task for Planning Agent to formulate strategy & checklist for operator approval..."
    : placeholder;

  return (
    <div className="chat-input-wrapper">
      <div className="chat-input-inner">
        {/* Active Plan Mode Indicator Banner */}
        {isPlanMode && (
          <div className="plan-mode-indicator-bar" role="status">
            <div className="plan-mode-indicator-left">
              <Layers size={13} className="plan-indicator-icon" />
              <span>
                <strong>Plan Mode Active:</strong> Prompt will wake up the Planning Agent to generate strategy & approval checklist.
              </span>
            </div>
            <button
              type="button"
              className="plan-mode-cancel-btn"
              onClick={() => setIsPlanMode(false)}
              title="Exit Plan Mode"
              aria-label="Exit Plan Mode"
            >
              <X size={12} />
              <span>Cancel</span>
            </button>
          </div>
        )}

        <form className="chat-input-form" onSubmit={handleSubmit}>
          <div className={`chat-prompt-card ${input.includes('\n') ? 'multiline' : ''} ${isPlanMode ? 'plan-card-active' : ''}`}>
            <textarea
              ref={textareaRef}
              id="chat-textarea"
              className="chat-textarea"
              placeholder={activePlaceholder}
              value={input}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={disabled || isPlanning}
            />

            <button
              type="submit"
              id="send-message-btn"
              className={`card-send-btn ${input.trim() ? 'active' : ''} ${isPlanMode ? 'plan-send-active' : ''}`}
              disabled={disabled || isPlanning || !input.trim()}
              aria-label={isPlanMode ? "Formulate plan" : "Send message"}
            >
              <span className="send-btn-label">{isPlanMode ? "Plan" : "Send"}</span>
              <div className="send-btn-icon-wrap">
                {isPlanMode ? (
                  <Layers size={13} strokeWidth={2.6} />
                ) : (
                  <ArrowUp size={13} strokeWidth={2.8} />
                )}
              </div>
            </button>
          </div>

          <div className="chat-input-bottom-bar">
            {onRequestPlan && (
              <button
                type="button"
                id="plan-action-btn"
                className={`chat-plan-btn ${isPlanMode ? 'plan-mode-active' : ''} ${input.trim() ? 'has-input' : ''}`}
                onClick={handlePlanClick}
                disabled={disabled || isPlanning}
                title={
                  isPlanMode
                    ? "Plan Mode active (click to exit)"
                    : input.trim()
                    ? "Formulate strategy & task checklist with current prompt"
                    : "Activate Plan Mode to formulate strategy before execution"
                }
              >
                {isPlanning ? (
                  <>
                    <Loader2 size={13} className="spinner-icon" />
                    <span>Planning Agent...</span>
                  </>
                ) : (
                  <>
                    <Layers size={13} />
                    <span>{isPlanMode ? "Plan Mode ON" : "Plan"}</span>
                  </>
                )}
              </button>
            )}
            <span className="chat-input-hint">
              {isPlanMode ? (
                <>Type prompt and press <strong>Enter</strong> or click <strong>Plan</strong> to open approval task queue</>
              ) : (
                <>Air-gapped Sovereign AI • Click <strong>Plan</strong> to formulate strategy & task queue for operator approval</>
              )}
            </span>
          </div>
        </form>
      </div>
    </div>
  );
}
