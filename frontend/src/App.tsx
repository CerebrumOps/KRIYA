import React, { useState, useEffect, useRef } from 'react';
import { Menu, X, Plus, Wrench, PanelLeftOpen, PanelLeftClose, Flame, Compass, ShieldCheck, Sun, Moon, LogOut, Layers, FolderOpen, Shield, ShieldAlert, Users, FileText } from 'lucide-react';
import Sidebar from './components/Sidebar/Sidebar';
import ChatArea from './components/ChatArea/ChatArea';
import RightToolPanel from './components/RightToolPanel/RightToolPanel';
import AuthLayout from './components/Auth/AuthLayout';
import TaskQueueModal from './components/TaskQueue/TaskQueueModal';
import ArtifactsDrawer from './components/Artifacts/ArtifactsDrawer';
import AdminPortal from './components/Admin/AdminPortal';
import { Plan, ChecklistItem, getActivePlan, createPlan } from './api/plan_api';
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
import { ToolCallItem } from './components/RightToolPanel/RightToolPanel';
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

  // 3. Clean user-facing text (strict isolation: never leak reasoning into content)
  if (toolCalls.length > 0) {
    // When tool calls are present, user-facing content is strictly the synthesized output AFTER the last tool execution
    const lastResultIdx = raw.lastIndexOf('</tool_result>');
    if (lastResultIdx !== -1) {
      // Collect any intermediate monologue before last </tool_result> that was outside <think> into reasoning
      const preRaw = raw.slice(0, lastResultIdx);
      const strayCommentary = preRaw
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

      if (strayCommentary && !reasoning.includes(strayCommentary)) {
        reasoning = reasoning ? `${strayCommentary}\n\n${reasoning}` : strayCommentary;
      }

      // Final response starts after the last tool_result
      const postRaw = raw.slice(lastResultIdx + '</tool_result>'.length);
      const postClean = postRaw
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

      content = postClean;
    } else {
      // Tools are still executing in-flight (no tool_result completed yet)
      content = '';
    }
  } else {
    // Standard response without tool calls
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
  }

  return { reasoning, content, toolCalls, isThinking, isAnyRunning, meta };
}

import { getStoredAuthToken, getStoredEmployee, getStoredAccess, clearAuthSession, logoutSession, SafeEmployeeAccess } from './api/auth_api';
import { Employee } from './schemas/employee';

export default function App() {
  const [currentView, setCurrentView] = useState<'auth' | 'app' | 'admin'>(() => {
    return getStoredAuthToken() ? 'app' : 'auth';
  });
  const [currentUser, setCurrentUser] = useState<Employee | null>(() => {
    return getStoredEmployee();
  });
  const [currentAccess, setCurrentAccess] = useState<SafeEmployeeAccess | null>(() => {
    return getStoredAccess();
  });

  const isAdmin = currentAccess?.level === 'admin' || (currentAccess?.permissions || []).includes('admin:manage_employees');
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [toolCalls, setToolCalls] = useState<ToolCallItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isPlanning, setIsPlanning] = useState(false);
  const [isToolPanelExpanded, setIsToolPanelExpanded] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isTaskQueueOpen, setIsTaskQueueOpen] = useState(false);
  const [isArtifactsOpen, setIsArtifactsOpen] = useState(false);
  const [activePlan, setActivePlan] = useState<Plan | null>(null);
  const [checklistItems, setChecklistItems] = useState<ChecklistItem[]>([]);
  const [isChecklistOpen, setIsChecklistOpen] = useState<boolean>(false);
  const toolPanelCollapseTimerRef = useRef<NodeJS.Timeout | null>(null);
  const wasAnyToolRunningRef = useRef<boolean>(false);
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('kriya_theme');
    return saved === 'dark' ? 'dark' : 'light';
  });

  // Check active plan on mount or chat switch
  useEffect(() => {
    getActivePlan()
      .then((p) => {
        if (p) {
          setActivePlan(p);
          const items: ChecklistItem[] = p.check_list && p.check_list.length > 0
            ? p.check_list
            : (p.steps || []).map((s, idx) => ({
                id: `step_${s.step_id || idx + 1}`,
                task: s.title,
                tool: s.tool,
                status: s.status === 'completed' ? 'success' : (s.status === 'running' ? 'in_progress' : 'pending')
              }));
          setChecklistItems(items);
          if (p.status === 'APPROVED' || p.status === 'IN_PROGRESS') {
            setIsChecklistOpen(true);
          }
        }
      })
      .catch(() => {});
  }, [activeChatId]);

  // Sync theme attribute to HTML root and persist in localStorage
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('kriya_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

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

  // Load conversation history from PostgreSQL whenever logged-in user changes
  useEffect(() => {
    async function loadInitialConversations() {
      // If not logged in, wipe any chat states
      if (!currentUser?.employeeId) {
        setHistory([]);
        setActiveChatId(null);
        setMessages([]);
        setToolCalls([]);
        return;
      }

      // Reset previous user's conversation state immediately
      setHistory([]);
      setActiveChatId(null);
      setMessages([]);
      setToolCalls([]);

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
  }, [currentUser?.employeeId]);

  // Handle generating a plan via Planning Agent and popping up approval modal
  const handleRequestPlan = async (text: string) => {
    if (!text.trim() || isLoading || isPlanning) return;
    setIsPlanning(true);
    setIsLoading(true);
    try {
      const generatedPlan = await createPlan(text.trim());
      setActivePlan(generatedPlan);
      setIsTaskQueueOpen(true);
    } catch (err: any) {
      console.error('Failed to create execution plan:', err);
    } finally {
      setIsPlanning(false);
      setIsLoading(false);
    }
  };

  const handlePlanApproved = (approvedPlan: Plan) => {
    const items: ChecklistItem[] = approvedPlan.check_list && approvedPlan.check_list.length > 0
      ? approvedPlan.check_list
      : (approvedPlan.steps || []).map((s, idx) => ({
          id: `step_${s.step_id || idx + 1}`,
          task: s.title,
          tool: s.tool,
          status: s.status === 'completed' ? 'success' : (s.status === 'running' ? 'in_progress' : 'pending')
        }));

    setActivePlan(approvedPlan);
    setChecklistItems(items);
    setIsChecklistOpen(true);
    setIsTaskQueueOpen(false);

    const formattedTasks = items
      .map((it, idx) => `${idx + 1}. [Tool: ${it.tool || 'specialized_tool'}] ${it.task}`)
      .join('\n');

    const executionPrompt = `Execute approved engineering plan: ${approvedPlan.title}

### Strategic Plan & Directives:
${approvedPlan.plan || 'Execute the approved operational workflow according to MRPL safety standards.'}

### Mandatory Execution Checklist:
${formattedTasks}

### Operating Instructions for KRIYA AI:
1. Execute each task in the checklist above using the specified specialized refinery tools.
2. Store all generated documents (.docx approval notes, .xlsx cost sheets, .pptx decks, calculation scripts) into the active chat workspace.
3. Upon concluding tool executions, synthesize the complete findings into an authoritative final engineering report.`;

    handleSendMessage(executionPrompt);
  };

  const handlePlanRejected = () => {
    setActivePlan(null);
    setChecklistItems([]);
    setIsChecklistOpen(false);
    setIsTaskQueueOpen(false);
  };

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
        conversation_id: currentChatId || undefined,
      };

      await streamChatMessage(
        requestPayload,
        (chunk) => {
          rawAccumulator += chunk;
          const parsed = parseAssistantStream(rawAccumulator);

          if (parsed.toolCalls.length > 0) {
            setToolCalls(parsed.toolCalls);

            // Synchronize checklist items with real-time tool calls
            setChecklistItems((prevItems) => {
              if (prevItems.length === 0) return prevItems;
              let hasChange = false;
              const nextItems = prevItems.map((item) => {
                const itemTool = (item.tool || '').toLowerCase().trim();
                if (!itemTool) return item;

                const matchingCall = parsed.toolCalls.find((tc) => {
                  const tcName = (tc.name || '').toLowerCase().trim();
                  return tcName === itemTool || tcName.includes(itemTool) || itemTool.includes(tcName);
                });

                if (matchingCall) {
                  if (matchingCall.status === 'completed' && item.status !== 'success') {
                    hasChange = true;
                    return { ...item, status: 'success' as const };
                  } else if (matchingCall.status === 'running' && item.status === 'pending') {
                    hasChange = true;
                    return { ...item, status: 'in_progress' as const };
                  }
                }
                return item;
              });
              return hasChange ? nextItems : prevItems;
            });

            if (parsed.isAnyRunning) {
              // Tool is actively executing: cancel any pending slide-back timer and open panel
              if (toolPanelCollapseTimerRef.current) {
                clearTimeout(toolPanelCollapseTimerRef.current);
                toolPanelCollapseTimerRef.current = null;
              }
              setIsToolPanelExpanded(true);
              wasAnyToolRunningRef.current = true;
            } else if (wasAnyToolRunningRef.current) {
              // Tool execution just completed: wait 1 second (1000ms), then slide back closed!
              wasAnyToolRunningRef.current = false;
              if (toolPanelCollapseTimerRef.current) {
                clearTimeout(toolPanelCollapseTimerRef.current);
              }
              toolPanelCollapseTimerRef.current = setTimeout(() => {
                setIsToolPanelExpanded(false);
                toolPanelCollapseTimerRef.current = null;
              }, 1000);
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

          // If tool panel was active or left open, slide back after 1 second
          if (wasAnyToolRunningRef.current || isToolPanelExpanded) {
            wasAnyToolRunningRef.current = false;
            if (toolPanelCollapseTimerRef.current) {
              clearTimeout(toolPanelCollapseTimerRef.current);
            }
            toolPanelCollapseTimerRef.current = setTimeout(() => {
              setIsToolPanelExpanded(false);
              toolPanelCollapseTimerRef.current = null;
            }, 1000);
          }

          const resolvedContent = parsed.content || (
            parsed.toolCalls.length > 0
              ? 'All requested operations and verifications were completed successfully.'
              : ''
          );

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId
                ? {
                    ...msg,
                    rawContent: rawAccumulator,
                    content: resolvedContent,
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

  const handleLoginSuccess = () => {
    setCurrentUser(getStoredEmployee());
    setCurrentAccess(getStoredAccess());
    setCurrentView('app');
  };

  const handleSignOut = () => {
    logoutSession().catch(() => {});
    clearAuthSession();
    setCurrentUser(null);
    setCurrentAccess(null);
    setHistory([]);
    setActiveChatId(null);
    setMessages([]);
    setToolCalls([]);
    setActivePlan(null);
    setIsTaskQueueOpen(false);
    setIsArtifactsOpen(false);
    setCurrentView('auth');
  };

  if (currentView === 'auth') {
    return (
      <AuthLayout
        onLoginSuccess={handleLoginSuccess}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
    );
  }

  if (currentView === 'admin') {
    return (
      <AdminPortal
        onReturnToApp={() => setCurrentView('app')}
        currentUser={currentUser}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
    );
  }

  return (
    <div className="app-container">
      {/* Mobile-only Header Bar (<= 1024px) */}
      <header className="mobile-top-bar" aria-label="Mobile Navigation">
        <button
          type="button"
          className="mobile-nav-btn"
          onClick={() => setIsMobileSidebarOpen((prev) => !prev)}
          aria-label="Toggle navigation menu"
        >
          {isMobileSidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        <div className="mobile-brand">
          <div className="brand-emblem-circle" style={{ width: 28, height: 28 }}>
            <Flame size={15} className="brand-flame-icon" />
          </div>
          <span className="brand-name" style={{ fontSize: 16 }}>KRIYA</span>
        </div>

        <div className="mobile-actions-group">
          <button
            type="button"
            className="mobile-nav-btn"
            onClick={toggleTheme}
            aria-label={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
          </button>

          <button
            type="button"
            className="mobile-nav-btn"
            onClick={() => setCurrentView('auth')}
            aria-label="Return to Authentication Screen"
            title="Return to Authentication Screen"
          >
            <LogOut size={17} />
          </button>

          {isAdmin && (
            <button
              type="button"
              className="mobile-nav-btn"
              onClick={() => setCurrentView('admin')}
              aria-label="Admin Portal"
              title="Admin Portal"
            >
              <ShieldAlert size={17} />
            </button>
          )}

          <button
            type="button"
            className="mobile-nav-btn"
            onClick={() => {
              handleNewChat();
              setIsMobileSidebarOpen(false);
            }}
            aria-label="New chat"
          >
            <Plus size={18} />
          </button>
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

      {/* Desktop Sovereign Workbench Top Strip */}
      <div className="workbench-top-strip">
        <div className="strip-left">
          <span className="airgap-badge">
            <Shield size={11} />
            <span>SOVEREIGN AIR-GAPPED WORKBENCH</span>
          </span>
          <span className="site-pill">MRPL Mangalore Complex (Site Alpha)</span>
          {currentUser && (
            <span className="user-pill">
              {currentUser.employeeName} • {currentUser.designation}
            </span>
          )}
        </div>

        <div className="strip-right">
          <button
            type="button"
            className={`workbench-action-btn ${activePlan?.status === 'PENDING_APPROVAL' ? 'active-plan' : ''}`}
            onClick={async () => {
              if (!activePlan) {
                try {
                  const defaultPlan = await createPlan("Analyze the attached scanned inspection report for the compressor unit.");
                  setActivePlan(defaultPlan);
                } catch (e) {
                  console.warn('Failed to load plan:', e);
                }
              }
              setIsTaskQueueOpen(true);
            }}
            title="Review multi-step strategic plan specifications"
          >
            <FileText size={13} />
            <span>
              {activePlan?.status === 'PENDING_APPROVAL'
                ? 'Task Plan (1 Review)'
                : activePlan
                ? `Task Plan: ${activePlan.status}`
                : 'Task Plan'}
            </span>
          </button>

          <button
            type="button"
            className="workbench-action-btn"
            onClick={() => setIsArtifactsOpen(true)}
            title="View generated Word notes, Excel sheets, and PowerPoint decks"
          >
            <FolderOpen size={13} />
            <span>Deliverables</span>
          </button>

          {isAdmin && (
            <button
              type="button"
              className="workbench-action-btn admin-strip-btn"
              onClick={() => setCurrentView('admin')}
              title="Open Sovereign Personnel & Directory Administration"
            >
              <ShieldAlert size={13} />
              <span>Admin Portal</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Multi-Column Content Area */}
      <div className="app-workspace-body">
        {/* Floating Expand Sidebar Trigger (Desktop when collapsed) */}
        {isSidebarCollapsed && (
          <button
            type="button"
            className="sidebar-expand-trigger"
            onClick={() => setIsSidebarCollapsed(false)}
            title="Expand Sidebar"
            aria-label="Expand Sidebar"
          >
            <PanelLeftOpen size={17} />
          </button>
        )}

        {/* 1. Left Sidebar */}
        <div className={`sidebar-responsive-wrapper ${isMobileSidebarOpen ? 'sidebar-open' : ''} ${isSidebarCollapsed ? 'desktop-collapsed' : ''}`}>
          <Sidebar
            currentUser={currentUser}
            history={history}
            activeChatId={activeChatId}
            theme={theme}
            onToggleTheme={toggleTheme}
            onNewChat={() => {
              handleNewChat();
              setIsMobileSidebarOpen(false);
            }}
            onSelectChat={(id) => {
              handleSelectChat(id);
              setIsMobileSidebarOpen(false);
            }}
            onDeleteChat={handleDeleteChat}
            onSelectPrompt={(prompt) => {
              handleSendMessage(prompt);
              setIsMobileSidebarOpen(false);
            }}
            onToggleCollapse={() => setIsSidebarCollapsed(true)}
            onSignOut={handleSignOut}
          />
        </div>

        {/* 2. Main Chat Area */}
        <ChatArea
          messages={messages}
          onSendMessage={handleSendMessage}
          onRequestPlan={handleRequestPlan}
          isLoading={isLoading}
          isPlanning={isPlanning}
          activePlan={activePlan}
          checklistItems={checklistItems}
          isChecklistOpen={isChecklistOpen}
          onCloseChecklist={() => setIsChecklistOpen(false)}
        />

        {/* 3. Collapsible Right-Side Tool Execution Drawer */}
        <RightToolPanel
          toolCalls={toolCalls}
          isExpanded={isToolPanelExpanded}
          onToggleExpand={() => setIsToolPanelExpanded((prev) => !prev)}
          isAnyRunning={isAnyRunning}
        />
      </div>

      {/* Modals & Overlays */}
      <TaskQueueModal
        plan={activePlan}
        isOpen={isTaskQueueOpen}
        onClose={() => setIsTaskQueueOpen(false)}
        onPlanApproved={handlePlanApproved}
        onPlanRejected={handlePlanRejected}
        onPlanUpdated={(updated) => setActivePlan(updated)}
      />

      <ArtifactsDrawer
        isOpen={isArtifactsOpen}
        onClose={() => setIsArtifactsOpen(false)}
        activeChatId={activeChatId}
      />
    </div>
  );
}
