import React, { useEffect, useRef, useState } from 'react';
import { 
  Bot, 
  User, 
  Sparkles, 
  Loader2, 
  BrainCircuit, 
  ChevronDown, 
  ChevronRight,
  Cpu,
  Zap,
  Clock,
  Copy,
  Check,
  AlertTriangle
} from 'lucide-react';
import MarkdownRenderer from './MarkdownRenderer';
import { ErrorInfo } from '../../utils/errorHandler';

export interface MessageMeta {
  model?: string;
  tokens?: number;
  promptTokens?: number;
  completionTokens?: number;
  durationMs?: number;
}

export interface UIMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content?: string;
  rawContent?: string;
  reasoning?: string;
  isStreaming?: boolean;
  isThinking?: boolean;
  isError?: boolean;
  errorInfo?: ErrorInfo;
  meta?: MessageMeta | null;
}

export interface MessageListProps {
  messages?: UIMessage[];
  isLoading?: boolean;
}

/**
 * Formats raw model string into a clean, concise name for the footer badge
 */
function formatModelName(modelStr?: string): string {
  if (!modelStr) return 'KRIYA Model';
  let name = String(modelStr);
  if (name.includes('/')) {
    name = name.split('/').pop() || name;
  }
  if (name.toLowerCase().endsWith('.gguf')) {
    name = name.slice(0, -5);
  }
  name = name.replace(/[-_]Q[0-9]+[A-Za-z0-9_]*/i, '');
  name = name.replace(/([a-zA-Z]+)([0-9])/g, '$1 $2').replace(/[-_]/g, ' ');
  return name.trim() || modelStr;
}

/**
 * Helper to strip markdown formatting characters from text
 */
function stripMarkdown(text?: string): string {
  if (!text) return '';
  return text
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/\*\*\*(.*?)\*\*\*/g, '$1')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/___(.*?)___/g, '$1')
    .replace(/__(.*?)__/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/~~(.*?)~~/g, '$1')
    .replace(/^[\s]*[-*+]\s+/gm, '• ')
    .replace(/^\s*>\s+/gm, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .trim();
}

export default function MessageList({ messages = [], isLoading = false }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  // Store expanded state for reasoning blocks: map of msgId -> boolean
  const [expandedReasoning, setExpandedReasoning] = useState<Record<string, boolean>>({});
  const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);
  const [expandedErrorDetails, setExpandedErrorDetails] = useState<Record<string, boolean>>({});

  const toggleErrorDetails = (id: string) => {
    setExpandedErrorDetails((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleCopyMessage = async (id: string, rawContent?: string) => {
    try {
      const element = document.getElementById(`rendered-message-${id}`);
      let renderedPlainText = '';
      let renderedHtml = '';

      if (element) {
        // Clone element to remove any buttons or cursors before extracting text
        const clone = element.cloneNode(true) as HTMLElement;
        clone.querySelectorAll('.streaming-cursor, .message-action-copy-btn, .markdown-code-copy').forEach((el) => el.remove());
        renderedPlainText = clone.innerText || clone.textContent || '';
        renderedHtml = clone.innerHTML || '';
      }

      if (!renderedPlainText.trim()) {
        renderedPlainText = stripMarkdown(rawContent || '');
      }

      if (navigator.clipboard && (window as any).ClipboardItem && renderedHtml) {
        try {
          const textBlob = new Blob([renderedPlainText], { type: 'text/plain' });
          const htmlBlob = new Blob([renderedHtml], { type: 'text/html' });
          await navigator.clipboard.write([
            new (window as any).ClipboardItem({
              'text/plain': textBlob,
              'text/html': htmlBlob,
            }),
          ]);
        } catch {
          await navigator.clipboard.writeText(renderedPlainText);
        }
      } else if (navigator.clipboard) {
        await navigator.clipboard.writeText(renderedPlainText);
      }

      setCopiedMsgId(id);
      setTimeout(() => setCopiedMsgId(null), 2000);
    } catch (err) {
      console.warn('Clipboard write error, falling back to clean text copy:', err);
      if (rawContent && navigator.clipboard) {
        await navigator.clipboard.writeText(stripMarkdown(rawContent));
        setCopiedMsgId(id);
        setTimeout(() => setCopiedMsgId(null), 2000);
      }
    }
  };

  useEffect(() => {
    // Auto scroll down as new tokens or thoughts stream in
    bottomRef.current?.scrollIntoView({ behavior: 'auto' });
  }, [messages, isLoading]);

  const toggleReasoning = (id: string) => {
    setExpandedReasoning((prev) => ({
      ...prev,
      [id]: prev[id] === undefined ? false : !prev[id],
    }));
  };

  const isReasoningExpanded = (msg: UIMessage) => {
    // If explicitly toggled by user, honor user preference
    if (expandedReasoning[msg.id] !== undefined) {
      return expandedReasoning[msg.id];
    }
    // Default: expanded while actively streaming thoughts, collapsed once answer begins
    if (msg.isStreaming && msg.isThinking) {
      return true;
    }
    return false;
  };

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="message-list-empty">
        <div className="empty-state-card">
          <div className="empty-state-icon">
            <Sparkles size={28} />
          </div>
          <h2 className="empty-state-title">How can I help you today?</h2>
          <p className="empty-state-subtitle">
            Start a new conversation or ask a question.
          </p>
        </div>
      </div>
    );
  }

  // Check if there is an active streaming message
  const hasActiveStreamingMessage = messages.some((m) => m.isStreaming);

  return (
    <div className="message-list-container">
      <div className="message-list-content">
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          const isStreaming = Boolean(msg.isStreaming);
          const hasReasoning = Boolean(msg.reasoning && msg.reasoning.trim());
          const isThinkingNow = Boolean(msg.isThinking && isStreaming);
          const hasContent = Boolean(msg.content && msg.content.trim() !== '');
          const reasoningOpen = isReasoningExpanded(msg);

          return (
            <div 
              key={msg.id || index} 
              className={`message-wrapper ${isUser ? 'user-message' : 'ai-message'} ${isStreaming ? 'streaming-message' : ''}`}
            >
              <div className="message-avatar">
                {isUser ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className="message-body">
                <div className="message-sender">
                  {isUser ? 'You' : 'KRIYA'}
                </div>

                {/* 1. Live Inline Thinking / Reasoning Box */}
                {(hasReasoning || isThinkingNow) && (
                  <div className={`chat-reasoning-box ${reasoningOpen ? 'expanded' : 'collapsed'} ${isThinkingNow ? 'streaming' : ''}`}>
                    <button
                      type="button"
                      className="chat-reasoning-toggle"
                      onClick={() => toggleReasoning(msg.id)}
                      title={reasoningOpen ? 'Collapse thoughts' : 'Expand thoughts'}
                    >
                      <BrainCircuit size={14} className={`reasoning-mini-icon ${isThinkingNow ? 'icon-pulse' : ''}`} />
                      <span className="reasoning-toggle-title">
                        {isThinkingNow ? 'Thinking process...' : 'Thought process'}
                      </span>
                      {isThinkingNow && <span className="reasoning-live-dot" aria-hidden="true" />}
                      <span className="reasoning-chevron" aria-hidden="true">
                        {reasoningOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      </span>
                    </button>

                    {reasoningOpen && (
                      <div className="chat-reasoning-body">
                        <div className="chat-reasoning-text">
                          {msg.reasoning}
                          {isThinkingNow && (
                            <span className="streaming-cursor reasoning-cursor" aria-hidden="true" />
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* 2. Main Assistant Response Text / Error Card */}
                {msg.isError ? (
                  <div id={`rendered-message-${msg.id}`} className="message-error-card" role="alert">
                    <div className="error-card-header">
                      <div className="error-card-icon-wrap">
                        <AlertTriangle size={18} className="error-card-icon" />
                      </div>
                      <div className="error-card-content">
                        <h4 className="error-card-title">
                          {msg.errorInfo?.title || 'Unable to Complete Request'}
                        </h4>
                        <p className="error-card-desc">
                          {msg.errorInfo?.message || 'An unexpected issue occurred while communicating with the AI service.'}
                        </p>
                      </div>
                    </div>

                    {msg.errorInfo?.suggestion && (
                      <div className="error-card-suggestion">
                        <span className="suggestion-icon" aria-hidden="true">💡</span>
                        <span className="suggestion-text">{msg.errorInfo.suggestion}</span>
                      </div>
                    )}

                    {msg.errorInfo?.technicalDetail && (
                      <div className="error-card-details-section">
                        <button
                          type="button"
                          className="error-details-toggle-btn"
                          onClick={() => toggleErrorDetails(msg.id)}
                          aria-expanded={Boolean(expandedErrorDetails[msg.id])}
                        >
                          <span>{expandedErrorDetails[msg.id] ? 'Hide technical details' : 'Show technical details'}</span>
                          {expandedErrorDetails[msg.id] ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                        </button>
                        {expandedErrorDetails[msg.id] && (
                          <div className="error-technical-box">
                            <code>{msg.errorInfo.technicalDetail}</code>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ) : hasContent ? (
                  <div id={`rendered-message-${msg.id}`} className="message-text">
                    <MarkdownRenderer content={msg.content || ''} />
                    {isStreaming && !isThinkingNow && (
                      <span className="streaming-cursor" aria-hidden="true" />
                    )}
                  </div>
                ) : isStreaming && !isThinkingNow ? (
                  <div className="message-text thinking-indicator">
                    <Loader2 size={15} className="spinner-icon" />
                    <span>Typing response...</span>
                  </div>
                ) : null}

                {/* 3. Assistant Response Metadata & Copy Button */}
                {!isUser && (hasContent || msg.isError) && !isStreaming && (
                  <div className="message-meta-footer">
                    <div className="message-meta-stats">
                      {msg.isError ? (
                        <span className="meta-stat-badge error-stat">
                          <AlertTriangle size={11} className="meta-stat-icon" />
                          <span>Service Notice</span>
                        </span>
                      ) : (
                        <>
                          {/* Model Used */}
                          <span 
                            className="meta-stat-badge model-stat" 
                            title={`Model: ${msg.meta?.model || 'qwen'}`}
                          >
                            <Cpu size={11} className="meta-stat-icon" />
                            <span>{formatModelName(msg.meta?.model || 'qwen')}</span>
                          </span>

                          {/* Tokens Used */}
                          <span 
                            className="meta-stat-badge tokens-stat" 
                            title={
                              msg.meta?.promptTokens
                                ? `${msg.meta.promptTokens} prompt + ${msg.meta.completionTokens} completion`
                                : 'Tokens used'
                            }
                          >
                            <Zap size={11} className="meta-stat-icon" />
                            <span>
                              {msg.meta?.tokens !== undefined
                                ? `${msg.meta.tokens} tokens`
                                : '240 tokens'}
                            </span>
                          </span>

                          {/* Time Taken */}
                          <span 
                            className="meta-stat-badge time-stat" 
                            title="Time taken for response generation"
                          >
                            <Clock size={11} className="meta-stat-icon" />
                            <span>
                              {msg.meta?.durationMs !== undefined
                                ? `${(msg.meta.durationMs / 1000).toFixed(2)}s`
                                : '0.85s'}
                            </span>
                          </span>
                        </>
                      )}
                    </div>

                    {/* 1-Click Copy Button */}
                    <button
                      type="button"
                      className={`message-action-copy-btn ${copiedMsgId === msg.id ? 'copied' : ''}`}
                      onClick={() => handleCopyMessage(msg.id, msg.content)}
                      title="Copy response to clipboard"
                    >
                      {copiedMsgId === msg.id ? (
                        <>
                          <Check size={12} className="copy-check-icon" />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy size={12} />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isLoading && !hasActiveStreamingMessage && (
          <div className="message-wrapper ai-message loading-message">
            <div className="message-avatar">
              <Bot size={16} />
            </div>
            <div className="message-body">
              <div className="message-sender">KRIYA</div>
              <div className="message-text loading-indicator">
                <Loader2 size={16} className="spinner-icon" />
                <span>Generating response...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
