import React, { useState, useEffect, useRef } from 'react';
import { Menu, X, Plus, Wrench } from 'lucide-react';
import Sidebar from './components/Sidebar/Sidebar';
import ChatArea from './components/ChatArea/ChatArea';
import RightToolPanel from './components/RightToolPanel/RightToolPanel';
import { streamChatMessage } from './api/chat_api';
import { 
  createConversation, 
  listConversations, 
  getConversation, 
  saveMessageExchange, 
  generateConversationTitle,
  deleteConversation 
} from './api/conversation_api';
import { HistoryItem } from './components/Sidebar/ChatHistory';
import { UIMessage } from './components/ChatArea/MessageList';
import { ToolCallItem } from './components/RightPanel/ToolCalling';
import { parseErrorInfo, formatErrorMarkdown } from './utils/errorHandler';
import './App.css';

export interface ParsedLlamaMetadata {
  tokens_generated?: number;
  time_taken_ms?: number;
  prompt_tokens?: number;
  speed_tokens_per_second?: number;
}

interface ParsedStreamResult {
  reasoning: string;
  content: string;
  toolCalls: ToolCallItem[];
  isThinking: boolean;
  isAnyRunning: boolean;
  meta?: ParsedLlamaMetadata;
}

/**
 * Parses raw streaming chunk accumulator from KRIYA backend.
 * Extracts:
 * - reasoning: content from <think>...</think> blocks
 * - toolCalls: parsed <tool_call> and <tool_result> blocks for RightToolPanel
 * - content: clean user-facing markdown response without XML tokens
 * - isThinking: whether stream is currently within an active <think> block
 * - isAnyRunning: whether any tool call is currently in the running state
 */
function parseAssistantStream(text: string): ParsedStreamResult {
  const raw = text || '';
  let reasoning = '';
  let content = '';
  const toolCalls: ToolCallItem[] = [];
  let isThinking = false;
  let isAnyRunning = false;

  // 1. Tool calls and results
  const toolPattern = /<tool_call name="([^"]*)" args=([\x27"])([\s\S]*?)\2>([\s\S]*?)<\/tool_call>(?:\s*<tool_result name="[^"]*">([\s\S]*?)<\/tool_result>)?/g;
  let match: RegExpExecArray | null;
  let idx = 0;
  while ((match = toolPattern.exec(raw)) !== null) {
    const name = match[1];
    let args: any = match[3];
    try {
      args = JSON.parse(match[3]);
    } catch {
      // keep raw string if not JSON
    }

    const hasResult = match[5] !== undefined;
    const result = hasResult ? match[5].trim() : undefined;

    toolCalls.push({
      id: `tc_${idx++}_${name}`,
      name,
      status: hasResult ? 'completed' : 'running',
      args,
      result,
    });
    if (!hasResult) isAnyRunning = true;
  }

  // Detect in-flight unclosed tool call at end of chunk
  const unclosedTool = /<tool_call name="([^"]*)" args=([\x27"])([\s\S]*?)\2>([\s\S]*?)$/g.exec(raw);
  if (unclosedTool && !unclosedTool[0].includes('</tool_call>')) {
    let args: any = unclosedTool[3];
    try {
      args = JSON.parse(unclosedTool[3]);
    } catch {
      // keep raw string
    }
    toolCalls.push({
      id: `tc_${idx++}_${unclosedTool[1]}`,
      name: unclosedTool[1],
      status: 'running',
      args,
      result: undefined,
    });
    isAnyRunning = true;
  }

  // 2. Extract reasoning (<think>...</think>)
  const thinkRegex = /<think>([\s\S]*?)(?:<\/think>|$)/g;
  const thoughts: string[] = [];
  let tm: RegExpExecArray | null;
  while ((tm = thinkRegex.exec(raw)) !== null) {
    if (tm[1].trim()) thoughts.push(tm[1].trim());
  }
  reasoning = thoughts.join('\n\n');

  if (
    raw.includes('<think>') &&
    (!raw.includes('</think>') || raw.lastIndexOf('<think>') > raw.lastIndexOf('</think>'))
  ) {
    isThinking = true;
  }

  // 4. Extract response metadata (<response_metadata>...</response_metadata>)
  let meta: ParsedLlamaMetadata | undefined;
  const metaRegex = /<response_metadata>([\s\S]*?)(?:<\/response_metadata>|$)/g;
  let metaMatch: RegExpExecArray | null;
  while ((metaMatch = metaRegex.exec(raw)) !== null) {
    if (metaMatch[1].trim()) {
      try {
        meta = JSON.parse(metaMatch[1].trim());
      } catch {
        // partial or malformed
      }
    }
  }

  // 3. Clean user-facing text
  const clean = raw
    .replace(/<think>[\s\S]*?<\/think>/g, '')
    .replace(/<think>[\s\S]*$/g, '')
    .replace(/<tool_call[\s\S]*?<\/tool_call>/g, '')
    .replace(/<tool_result[\s\S]*?<\/tool_result>/g, '')
    .replace(/<tool_call[\s\S]*$/g, '')
    .replace(/<tool_result[\s\S]*$/g, '')
    .replace(/<response_metadata>[\s\S]*?<\/response_metadata>/g, '')
    .replace(/<response_metadata>[\s\S]*$/g, '')
    .replace(/<\/?(think|response_metadata)>/g, '')
    .trim();
  content = clean;

  return { reasoning, content, toolCalls, isThinking, isAnyRunning, meta };
}

export default function App() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [toolCalls, setToolCalls] = useState<ToolCallItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isToolPanelExpanded, setIsToolPanelExpanded] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  const isAnyRunning = toolCalls.some((tc) => tc.status === 'running');
  const prevRunningRef = useRef<boolean>(false);

  // Auto-collapse tool panel smoothly when execution completes
  useEffect(() => {
    if (prevRunningRef.current && !isAnyRunning) {
      const timer = setTimeout(() => {
        setIsToolPanelExpanded(false);
      }, 1500);
      return () => clearTimeout(timer);
    }
    prevRunningRef.current = isAnyRunning;
  }, [isAnyRunning]);

  // Handle "+ New Chat" button click
  const handleNewChat = () => {
    if (isLoading) return;
    setActiveChatId(null);
    setMessages([]);
    setToolCalls([]);
    setIsToolPanelExpanded(false);
  };

  // Handle selecting a chat from Sidebar Chat History
  const handleSelectChat = async (id: string) => {
    if (isLoading) return;
    setActiveChatId(id);
    try {
      const data = await getConversation(id);
      if (data && data.messages && data.messages.length > 0) {
        let latestToolCalls: ToolCallItem[] = [];
        const formatted: UIMessage[] = data.messages.map((m, idx) => {
          if (m.role === 'assistant') {
            const parsed = parseAssistantStream(m.content);
            if (parsed.toolCalls.length > 0) {
              latestToolCalls = parsed.toolCalls;
            }
            return {
              id: `m_${idx}`,
              role: 'assistant',
              rawContent: m.content,
              content: parsed.content || m.content,
              reasoning: parsed.reasoning,
              isStreaming: false,
              isThinking: false,
              meta: {
                model: 'default',
                tokens: parsed.meta?.tokens_generated ?? Math.round(m.content.length / 4),
                promptTokens: parsed.meta?.prompt_tokens,
                completionTokens: parsed.meta?.tokens_generated,
                durationMs: parsed.meta?.time_taken_ms ?? 850,
              },
            };
          } else {
            return {
              id: `m_${idx}`,
              role: 'user',
              content: m.content,
            };
          }
        });
        setMessages(formatted);
        setToolCalls(latestToolCalls);
      } else {
        setMessages([]);
        setToolCalls([]);
      }
    } catch (err) {
      console.error('Failed to load conversation from DB:', err);
    }
  };

  // Handle deleting a chat from PostgreSQL
  const handleDeleteChat = async (id: string) => {
    // 1. Immediately update UI state
    const remaining = history.filter((h) => h.id !== id);
    setHistory(remaining);

    // 2. If deleting active chat, select next available or reset
    if (activeChatId === id) {
      if (remaining.length > 0) {
        handleSelectChat(remaining[0].id);
      } else {
        setActiveChatId(null);
        setMessages([]);
        setToolCalls([]);
        setIsToolPanelExpanded(false);
      }
    }

    // 3. Delete from database in background
    try {
      await deleteConversation(id);
    } catch (err) {
      console.error('Failed to delete conversation from DB:', err);
    }
  };

  const hasInitializedRef = useRef<boolean>(false);

  // Load conversation history from PostgreSQL on component mount
  useEffect(() => {
    if (hasInitializedRef.current) return;
    hasInitializedRef.current = true;

    async function loadInitialConversations() {
      try {
        const list = await listConversations();
        if (list && list.length > 0) {
          setHistory(list.map((c) => ({ id: c.id, title: c.name || 'New Chat' })));
          handleSelectChat(list[0].id);
        } else {
          setHistory([]);
          setActiveChatId(null);
          setMessages([]);
          setToolCalls([]);
        }
      } catch (err) {
        console.warn('Could not connect to PostgreSQL on startup:', err);
      }
    }

    loadInitialConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle sending a message with real-time streaming and tool execution
  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    let currentChatId = activeChatId;
    if (!currentChatId) {
      try {
        const newConv = await createConversation();
        currentChatId = newConv.id;
        setActiveChatId(currentChatId);
        setHistory((prev) => [{ id: currentChatId!, title: 'New Chat' }, ...prev]);
      } catch {
        currentChatId = Date.now().toString();
        setActiveChatId(currentChatId);
        setHistory((prev) => [{ id: currentChatId!, title: 'New Chat' }, ...prev]);
      }
    }

    const userMessage: UIMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
    };

    const assistantId = (Date.now() + 1).toString();
    const assistantMessage: UIMessage = {
      id: assistantId,
      role: 'assistant',
      rawContent: '',
      content: '',
      reasoning: '',
      isStreaming: true,
      isThinking: true,
      meta: null,
    };

    const updatedMessages = [...messages, userMessage];
    setMessages([...updatedMessages, assistantMessage]);
    setIsLoading(true);
    setToolCalls([]);

    const startTime = performance.now();
    let rawAccumulator = '';

    try {
      const historyPayload = messages
        .filter((m) => !m.isError)
        .map((m) => ({ role: m.role, content: m.rawContent || m.content || '' }));

      const requestPayload = {
        user_message: text,
        history: historyPayload,
        thinking: true,
        model: 'default',
        temperature: 0.2,
      };

      await streamChatMessage(
        requestPayload,
        (chunk) => {
          rawAccumulator += chunk;
          const parsed = parseAssistantStream(rawAccumulator);

          if (parsed.toolCalls.length > 0) {
            setToolCalls(parsed.toolCalls);
            if (parsed.isAnyRunning) {
              setIsToolPanelExpanded(true);
            }
          }

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId
                ? {
                    ...msg,
                    rawContent: rawAccumulator,
                    content: parsed.content,
                    reasoning: parsed.reasoning,
                    isStreaming: true,
                    isThinking: parsed.isThinking,
                  }
                : msg
            )
          );
        },
        async () => {
          // Stream complete
          const parsed = parseAssistantStream(rawAccumulator);
          const finalDurationMs = parsed.meta?.time_taken_ms ?? Math.round(performance.now() - startTime);
          const totalTokens = parsed.meta?.tokens_generated ?? Math.round((text.length + rawAccumulator.length) / 4);

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId
                ? {
                    ...msg,
                    rawContent: rawAccumulator,
                    content: parsed.content || 'Completed requested action.',
                    reasoning: parsed.reasoning,
                    isStreaming: false,
                    isThinking: false,
                    meta: {
                      model: 'default',
                      tokens: totalTokens,
                      promptTokens: parsed.meta?.prompt_tokens ?? Math.round(text.length / 4),
                      completionTokens: parsed.meta?.tokens_generated ?? Math.round(rawAccumulator.length / 4),
                      durationMs: finalDurationMs,
                    },
                  }
                : msg
            )
          );
          setIsLoading(false);

          // Save exchange to PostgreSQL
          if (currentChatId) {
            saveMessageExchange(currentChatId, text, rawAccumulator).catch((e) =>
              console.error('Error persisting exchange in DB:', e)
            );

            // Trigger naming mini-agent if title is still default
            const activeItem = history.find((h) => h.id === currentChatId);
            if (!activeItem || activeItem.title === 'New Chat' || !activeItem.title) {
              generateConversationTitle(currentChatId, text, rawAccumulator)
                .then((newTitle) => {
                  if (newTitle) {
                    setHistory((prev) =>
                      prev.map((h) =>
                        h.id === currentChatId ? { ...h, title: newTitle } : h
                      )
                    );
                  }
                })
                .catch((e) => console.warn('Error generating title:', e));
            }
          }
        },
        (error) => {
          console.error('AI Streaming Error:', error);
          const finalDurationMs = Math.round(performance.now() - startTime);
          const errorInfo = parseErrorInfo(error);
          const errorContent = formatErrorMarkdown(errorInfo);

          const errorMsg: UIMessage = {
            id: assistantId,
            role: 'assistant',
            content: errorContent,
            isError: true,
            errorInfo,
            reasoning: '',
            isStreaming: false,
            isThinking: false,
            meta: {
              model: 'default',
              tokens: 0,
              durationMs: finalDurationMs,
            },
          };
          setMessages((prev) =>
            prev.map((msg) => (msg.id === assistantId ? errorMsg : msg))
          );
          setIsLoading(false);
        }
      );
    } catch (err) {
      console.error('Failed to initiate stream:', err);
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Mobile / Tablet Header Bar */}
      <header className="mobile-top-bar" aria-label="Mobile Navigation">
        <button
          className="mobile-nav-btn"
          onClick={() => setIsMobileSidebarOpen((prev) => !prev)}
          aria-label="Toggle navigation menu"
          title="Menu"
        >
          {isMobileSidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        <div className="mobile-brand">
          <span className="mobile-brand-dot" />
          <span className="mobile-brand-title">KRIYA</span>
          <span className="mobile-brand-badge">AI</span>
        </div>

        <div className="mobile-actions">
          <button
            className="mobile-nav-btn"
            onClick={() => {
              handleNewChat();
              setIsMobileSidebarOpen(false);
            }}
            aria-label="Start new chat"
            title="New Chat"
          >
            <Plus size={18} />
          </button>

          {toolCalls.length > 0 && (
            <button
              className={`mobile-nav-btn mobile-tool-btn ${isAnyRunning ? 'running' : ''}`}
              onClick={() => setIsToolPanelExpanded((prev) => !prev)}
              aria-label="Toggle tool panel"
              title="Tool Execution Panel"
            >
              <Wrench size={17} />
              {isAnyRunning && <span className="mobile-tool-badge" />}
            </button>
          )}
        </div>
      </header>

      {/* Backdrop for Mobile / Tablet Sidebar Drawer */}
      {isMobileSidebarOpen && (
        <div
          className="mobile-sidebar-backdrop"
          onClick={() => setIsMobileSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Main Multi-Column Content Area */}
      <div className="app-workspace-body">
        {/* 1. Left Sidebar */}
        <div className={`sidebar-responsive-wrapper ${isMobileSidebarOpen ? 'sidebar-open' : ''}`}>
          <Sidebar
            history={history}
            activeChatId={activeChatId}
            onNewChat={() => {
              handleNewChat();
              setIsMobileSidebarOpen(false);
            }}
            onSelectChat={(id) => {
              handleSelectChat(id);
              setIsMobileSidebarOpen(false);
            }}
            onDeleteChat={handleDeleteChat}
          />
        </div>

        {/* 2. Main Chat Area */}
        <ChatArea
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />

        {/* 3. Collapsible Right-Side Tool Execution Drawer */}
        <RightToolPanel
          toolCalls={toolCalls}
          isExpanded={isToolPanelExpanded}
          onToggleExpand={() => setIsToolPanelExpanded((prev) => !prev)}
          isAnyRunning={isAnyRunning}
        />
      </div>
    </div>
  );
}
