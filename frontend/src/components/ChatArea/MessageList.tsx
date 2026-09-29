import React, { useState, useRef, useEffect } from 'react';
import { 
  Flame, 
  User, 
  ChevronDown, 
  ChevronRight, 
  Sparkles, 
  BrainCircuit, 
  Loader2,
  Terminal,
  Cpu,
  Clock,
  Copy,
  Check,
  AlertTriangle,
  FileCheck,
  Layers,
  Calculator,
  Activity,
  Wrench,
  ShieldCheck,
  FileText,
  Sheet,
  Presentation,
  FileCode,
  Download,
  FolderOpen,
  CheckCircle2
} from 'lucide-react';
import MarkdownRenderer from './MarkdownRenderer';
import { ErrorInfo } from '../../utils/errorHandler';
import { copyTextToClipboard } from '../../utils/clipboard';
import { downloadDeliverable } from '../../api/workspace_api';

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
  onSelectPrompt?: (prompt: string) => void;
  activeChatId?: string | null;
  onOpenDeliverables?: () => void;
}

const SUGGESTION_PILLS = [
  {
    icon: Flame,
    label: 'Refinery Alerts',
    prompt: 'Check all active refinery operational alarms, relief valve status, and GPU node telemetry.'
  },
  {
    icon: Layers,
    label: 'P&ID Analysis',
    prompt: 'Inspect the P&ID drawing for Crude Distillation Unit and verify safety relief valves.'
  },
  {
    icon: FileCheck,
    label: 'Inspection SOPs',
    prompt: 'Review the latest compressor inspection report and draft a formal approval note.'
  },
  {
    icon: Calculator,
    label: 'Compressor Calc',
    prompt: 'Calculate the Darcy-Weisbach pressure drop and Reynolds number for a 12-inch crude oil pipeline.'
  },
  {
    icon: Wrench,
    label: 'Execute Tool',
    prompt: 'Execute the pipeline throughput calculation tool with flow rate 850 m3/h and viscosity 32 cSt.'
  },
  {
    icon: Activity,
    label: 'Process Monitor',
    prompt: 'Show live telemetry, GPU cluster temperature, and gas compressor vibration status.'
  }
];

interface ExtractedDeliverable {
  filename: string;
  type: 'docx' | 'xlsx' | 'pptx' | 'csv' | 'pdf' | 'py' | 'json';
  title: string;
  description: string;
}

function buildDeliverableInfo(filename: string): ExtractedDeliverable {
  const ext = (filename.split('.').pop() || '').toLowerCase();
  let type: 'docx' | 'xlsx' | 'pptx' | 'csv' | 'pdf' | 'py' | 'json' = 'docx';
  let title = filename.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
  let description = 'Verified Corporate Deliverable';

  if (ext === 'docx') {
    type = 'docx';
    description = 'Microsoft Word Engineering Approval Note';
  } else if (ext === 'xlsx') {
    type = 'xlsx';
    description = 'Excel Multi-Tab Financial & Cost Model';
  } else if (ext === 'pptx') {
    type = 'pptx';
    description = 'Executive Management PowerPoint Slide Deck';
  } else if (ext === 'csv') {
    type = 'csv';
    description = 'Structured Telemetry / Inspection CSV Dataset';
  } else if (ext === 'py') {
    type = 'py';
    description = 'Sandboxed & Verified Python Engineering Utility';
  } else if (ext === 'pdf') {
    type = 'pdf';
    description = 'Compiled Engineering Specification Document';
  }

  return { filename, type, title, description };
}

function extractDeliverablesFromMessage(msg: UIMessage): ExtractedDeliverable[] {
  const text = (msg.rawContent || '') + ' ' + (msg.content || '');
  const files: ExtractedDeliverable[] = [];
  const seen = new Set<string>();

  // Pattern 1: [Deliverable Created]: ... saved to '.../filename.ext'
  const createdMatches = text.matchAll(/\[Deliverable Created\]:.*?saved to '([^']+)'/gi);
  for (const m of createdMatches) {
    const rawPath = m[1];
    const filename = rawPath.split(/[\/\\]/).pop() || '';
    if (filename && !seen.has(filename)) {
      seen.add(filename);
      files.push(buildDeliverableInfo(filename));
    }
  }

  // Pattern 2: [Deliverables Saved to Workspace]: file1, file2
  const wsMatches = text.matchAll(/\[Deliverables Saved to Workspace\]:\s*([^\n]+)/gi);
  for (const m of wsMatches) {
    const rawNames = m[1].split(',');
    for (const raw of rawNames) {
      const filename = raw.trim();
      if (filename && !seen.has(filename) && filename.includes('.')) {
        seen.add(filename);
        files.push(buildDeliverableInfo(filename));
      }
    }
  }

  // Pattern 3 removed: Hardcoded regexes caused "ghost files" because they matched
  // the suffix of dynamically generated filenames (e.g. "Approval_Note.docx" matching
  // the end of "FCCU_Pump_Approval_Note.docx"). Pattern 1 handles dynamic extraction.

  return files;
}

export default function MessageList({
  messages = [],
  isLoading = false,
  onSelectPrompt,
  activeChatId,
  onOpenDeliverables,
}: MessageListProps) {
  const [expandedReasoningMap, setExpandedReasoningMap] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const activeThoughtRef = useRef<HTMLDivElement>(null);
  const thoughtEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll handler: 'auto' for fast streaming updates, 'smooth' for settled completions
  const scrollToBottom = (behavior: ScrollBehavior = 'auto') => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior, block: 'end' });
    } else if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    if (messages.length === 0 && !isLoading) return;
    const streamingMsg = messages.find((m) => m.isStreaming);
    const isThinkingNow = Boolean(streamingMsg?.isThinking && streamingMsg?.isStreaming);

    if (isThinkingNow) {
      // While giving reasoning: auto-scroll inside the thought drawer to keep newest reasoning in view
      if (activeThoughtRef.current) {
        activeThoughtRef.current.scrollTop = activeThoughtRef.current.scrollHeight;
      }
      if (thoughtEndRef.current) {
        thoughtEndRef.current.scrollIntoView({ behavior: 'auto', block: 'end' });
      }

      // Also keep the main chat container scrolled to show the active reasoning drawer
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'auto', block: 'end' });
      } else if (containerRef.current) {
        containerRef.current.scrollTop = containerRef.current.scrollHeight;
      }
    } else if (streamingMsg || isLoading) {
      // Primary response is actively streaming - scroll immediately with 'auto'
      scrollToBottom('auto');
    } else {
      // Completed or message appended - smooth scroll
      scrollToBottom('smooth');
    }
  }, [messages, isLoading, expandedReasoningMap]);

  const toggleReasoning = (id: string) => {
    setExpandedReasoningMap((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const isReasoningExpanded = (msg: UIMessage) => {
    if (expandedReasoningMap[msg.id] !== undefined) {
      return expandedReasoningMap[msg.id];
    }
    return Boolean(msg.isThinking && msg.isStreaming);
  };

  const handleCopy = async (id: string, text?: string) => {
    if (!text) return;
    const ok = await copyTextToClipboard(text);
    if (ok) {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  // -------------------------------------------------------------
  // EMPTY STATE HERO (Exact Sorin-AI Reference Design)
  // -------------------------------------------------------------
  if (messages.length === 0 && !isLoading) {
    return (
      <div className="message-list-empty">
        <div className="empty-state-container">
          {/* Concentric Mint Halo Emblem */}
          <div className="empty-hero-emblem-wrap">
            <div className="hero-emblem-glow" />
            <div className="hero-emblem-outer-ring" />
            <div className="hero-emblem-middle-ring" />
            <div className="hero-emblem-core">
              <Flame size={30} className="hero-emblem-icon" />
            </div>
          </div>

          {/* Reference Headline: Hey, I'm sorin. How can I help you today? */}
          <h1 className="empty-hero-title">
            Hey, I'm <span className="hero-highlight-mint">kriya</span>. How can I help you today?
          </h1>

          {/* Reference Suggestion Pills Horizontal Row */}
          <div className="hero-suggestion-pills-row">
            {SUGGESTION_PILLS.map((pill, idx) => {
              const Icon = pill.icon;
              return (
                <button
                  key={idx}
                  type="button"
                  className="hero-suggestion-pill"
                  onClick={() => onSelectPrompt && onSelectPrompt(pill.prompt)}
                  title={pill.prompt}
                >
                  <Icon size={14} className="suggestion-pill-icon" />
                  <span>{pill.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  const hasActiveStreamingMessage = messages.some((m) => m.isStreaming);

  return (
    <div className="message-list-container" ref={containerRef}>
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
                {isUser ? <User size={15} /> : <Flame size={15} />}
              </div>
              <div className="message-body">
                <div className="message-sender">
                  {isUser ? 'You' : 'KRIYA'}
                </div>

                {/* 1. Live Inline Thinking / Reasoning Drawer */}
                {hasReasoning && (
                  <div className={`thought-container ${isThinkingNow ? 'thinking-active' : 'thinking-complete'} ${reasoningOpen ? 'is-expanded' : 'is-collapsed'}`}>
                    <button 
                      type="button" 
                      className="thought-header"
                      onClick={() => toggleReasoning(msg.id)}
                      aria-expanded={reasoningOpen}
                      aria-controls={`thought-${msg.id}`}
                    >
                      <div className="thought-header-left">
                        {isThinkingNow ? (
                          <Loader2 size={13} className="spinner-icon thought-status-icon" />
                        ) : (
                          <BrainCircuit size={13} className="thought-status-icon" />
                        )}
                        <span className="thought-label">
                          {isThinkingNow ? 'Thinking process...' : 'Reasoning process'}
                        </span>
                      </div>
                      <div className="thought-header-right">
                        <span className="thought-expand-hint">
                          {reasoningOpen ? 'Hide' : 'Show details'}
                        </span>
                        <ChevronDown 
                          size={13} 
                          className={`thought-chevron-icon ${reasoningOpen ? 'is-expanded' : ''}`} 
                        />
                      </div>
                    </button>

                    <div className={`thought-drawer-wrapper ${reasoningOpen ? 'expanded' : ''}`}>
                      <div className="thought-drawer-inner">
                        <div 
                          id={`thought-${msg.id}`} 
                          className="thought-content"
                          ref={isThinkingNow ? activeThoughtRef : undefined}
                        >
                          <MarkdownRenderer content={msg.reasoning!} />
                          {isThinkingNow && (
                            <span className="streaming-cursor" aria-hidden="true" />
                          )}
                          <div 
                            ref={isThinkingNow ? thoughtEndRef : undefined} 
                            style={{ height: 1, flexShrink: 0 }} 
                            aria-hidden="true" 
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* 2. Primary Markdown Response */}
                {hasContent ? (
                  <div className="message-text">
                    <MarkdownRenderer content={msg.content!} />
                    {isStreaming && !isThinkingNow && (
                      <span className="streaming-cursor" aria-hidden="true" />
                    )}
                  </div>
                ) : (
                  isStreaming && !hasReasoning && (
                    <div className="generating-indicator">
                      <Loader2 size={14} className="spinner-icon" />
                      <span>Synthesizing response...</span>
                    </div>
                  )
                )}

                {/* 2.5 In-Chat Interactive Deliverable Artifact Cards */}
                {!isUser && !isStreaming && (() => {
                  const delivs = extractDeliverablesFromMessage(msg);
                  if (delivs.length === 0) return null;
                  return (
                    <div className="message-deliverables-container">
                      <div className="message-deliverables-header">
                        <CheckCircle2 size={14} className="deliverables-header-icon" />
                        <span>Generated Engineering Deliverables</span>
                        <span className="deliverables-count-tag">{delivs.length} Ready</span>
                      </div>
                      <div className="message-deliverables-grid">
                        {delivs.map((d) => (
                          <div key={d.filename} className={`deliverable-card card-${d.type}`}>
                            <div className="deliverable-card-icon">
                              {d.type === 'docx' && <FileText size={18} color="#0284c7" />}
                              {d.type === 'xlsx' && <Sheet size={18} color="#10b981" />}
                              {d.type === 'pptx' && <Presentation size={18} color="#f59e0b" />}
                              {d.type === 'csv' && <Sheet size={18} color="#06b6d4" />}
                              {d.type === 'py' && <FileCode size={18} color="#8b5cf6" />}
                              {d.type === 'pdf' && <FileText size={18} color="#ef4444" />}
                            </div>
                            <div className="deliverable-card-details">
                              <div className="deliverable-card-title">{d.filename}</div>
                              <div className="deliverable-card-desc">{d.description}</div>
                            </div>
                            <button
                              type="button"
                              className="deliverable-download-action-btn"
                              onClick={() => downloadDeliverable(activeChatId || 'default_chat', d.filename)}
                              title={`Download ${d.filename}`}
                            >
                              <Download size={13} />
                              <span>Download</span>
                            </button>
                          </div>
                        ))}
                      </div>
                      {onOpenDeliverables && (
                        <button
                          type="button"
                          className="view-all-deliverables-btn"
                          onClick={onOpenDeliverables}
                        >
                          <FolderOpen size={12} />
                          <span>Open All Workspace Deliverables</span>
                        </button>
                      )}
                    </div>
                  );
                })()}

                {/* User Message Action Footer */}
                {isUser && hasContent && (
                  <div className="user-message-actions">
                    <button
                      type="button"
                      className={`message-action-copy-btn user-copy-btn ${copiedId === msg.id ? 'copied' : ''}`}
                      onClick={() => handleCopy(msg.id, msg.content)}
                      title="Copy message"
                      aria-label="Copy message"
                    >
                      {copiedId === msg.id ? (
                        <>
                          <Check size={11} />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy size={11} />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                )}

                {/* 3. Structured Error Card */}
                {msg.isError && msg.errorInfo && (
                  <div className="message-error-card">
                    <div className="error-card-header">
                      <AlertTriangle size={18} className="error-card-icon" />
                      <div className="error-card-title-group">
                        <span className="error-card-title">{msg.errorInfo.title}</span>
                        {msg.errorInfo.statusCode && (
                          <span className="error-status-badge">HTTP {msg.errorInfo.statusCode}</span>
                        )}
                      </div>
                    </div>
                    <div className="error-card-body">
                      <p className="error-message-text">{msg.errorInfo.message}</p>
                      {msg.errorInfo.fixSuggestion && (
                        <div className="error-fix-section">
                          <span className="error-fix-label">Recommended Action:</span>
                          <span className="error-fix-text">{msg.errorInfo.fixSuggestion}</span>
                        </div>
                      )}
                    </div>
                    <div className="error-card-footer">
                      <button
                        type="button"
                        className={`message-action-copy-btn ${copiedId === msg.id ? 'copied' : ''}`}
                        onClick={() => handleCopy(msg.id, `${msg.errorInfo?.title || 'Error'}: ${msg.errorInfo?.message || ''}\n${msg.errorInfo?.fixSuggestion || ''}`.trim())}
                        title="Copy error details"
                      >
                        {copiedId === msg.id ? (
                          <>
                            <Check size={12} />
                            <span>Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy size={12} />
                            <span>Copy Error</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}

                {/* 4. Metadata Footer (Tokens, Duration, Copy Action) */}
                {!isUser && !isStreaming && (hasContent || hasReasoning) && (
                  <div className="message-meta-footer">
                    <div className="message-meta-stats">
                      {msg.meta?.model && (
                        <span className="meta-stat-badge model-stat" title="Model Identifier">
                          <Cpu size={11} className="meta-stat-icon" />
                          <span>{msg.meta.model}</span>
                        </span>
                      )}
                      {msg.meta?.tokens !== undefined && msg.meta.tokens > 0 && (
                        <span className="meta-stat-badge tokens-stat" title="Tokens Generated">
                          <Terminal size={11} className="meta-stat-icon" />
                          <span>{msg.meta.tokens} tokens</span>
                        </span>
                      )}
                      {msg.meta?.durationMs !== undefined && msg.meta.durationMs > 0 && (
                        <span className="meta-stat-badge time-stat" title="Inference Latency">
                          <Clock size={11} className="meta-stat-icon" />
                          <span>{(msg.meta.durationMs / 1000).toFixed(2)}s</span>
                        </span>
                      )}
                    </div>

                    <button
                      type="button"
                      className={`message-action-copy-btn ${copiedId === msg.id ? 'copied' : ''}`}
                      onClick={() => handleCopy(msg.id, msg.content || msg.rawContent || msg.reasoning || '')}
                      title="Copy response markdown"
                    >
                      {copiedId === msg.id ? (
                        <>
                          <Check size={12} />
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

        {/* Global Loading Bar when awaiting first token */}
        {isLoading && !hasActiveStreamingMessage && (
          <div className="message-wrapper ai-message loading-placeholder">
            <div className="message-avatar">
              <Flame size={15} />
            </div>
            <div className="message-body">
              <div className="generating-indicator">
                <Loader2 size={14} className="spinner-icon" />
                <span>Accessing on-premise model runner...</span>
              </div>
            </div>
          </div>
        )}

        {/* Bottom Anchor for Auto-scroll */}
        <div ref={messagesEndRef} style={{ height: 1, flexShrink: 0 }} aria-hidden="true" />
      </div>
    </div>
  );
}
