import React from 'react';
import { 
  Flame,
  ChevronDown,
  ShieldCheck,
  PanelLeftClose,
  Sun,
  Moon
} from 'lucide-react';
import NewChat from './NewChat';
import ChatHistory, { HistoryItem } from './ChatHistory';
import './Sidebar.css';

export interface SidebarProps {
  history?: HistoryItem[];
  activeChatId?: string | null;
  theme?: 'light' | 'dark';
  onToggleTheme?: () => void;
  onNewChat?: () => void;
  onSelectChat?: (id: string) => void;
  onDeleteChat?: (id: string) => void;
  onSelectPrompt?: (prompt: string) => void;
  onToggleCollapse?: () => void;
}

export default function Sidebar({ 
  history = [], 
  activeChatId = null, 
  theme = 'light',
  onToggleTheme,
  onNewChat, 
  onSelectChat, 
  onDeleteChat,
  onSelectPrompt,
  onToggleCollapse
}: SidebarProps) {
  return (
    <aside className="sidebar" aria-label="Workbench navigation sidebar">
      {/* 1. Brand Header */}
      <div className="sidebar-brand-header">
        <div className="brand-logo-group">
          <div className="brand-emblem-circle">
            <Flame size={17} className="brand-flame-icon" />
          </div>
          <span className="brand-name">KRIYA</span>
        </div>

        <div className="sidebar-header-actions">
          {onToggleTheme && (
            <button
              type="button"
              className="sidebar-theme-btn"
              onClick={onToggleTheme}
              aria-label={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
            </button>
          )}

          {onToggleCollapse && (
            <button
              type="button"
              className="sidebar-collapse-btn"
              onClick={onToggleCollapse}
              aria-label="Collapse sidebar"
              title="Collapse sidebar"
            >
              <PanelLeftClose size={16} />
            </button>
          )}
        </div>
      </div>

      {/* 2. New Chat Action Card */}
      <div className="sidebar-new-chat-wrapper">
        <NewChat onNewChat={onNewChat || (() => {})} />
      </div>

      {/* 3. Recent Chats History */}
      <div className="sidebar-history-wrapper">
        <ChatHistory 
          history={history} 
          activeChatId={activeChatId} 
          onSelectChat={onSelectChat} 
          onDeleteChat={onDeleteChat}
        />
      </div>

      {/* 4. Bottom User Profile Card */}
      <div className="sidebar-user-footer">
        <div className="user-profile-card">
          <div className="user-avatar-wrap">
            <div className="user-avatar-placeholder">
              <span>OP</span>
            </div>
            <span className="user-status-dot" title="Air-Gapped | Sovereign" />
          </div>
          <div className="user-info-text">
            <div className="user-name-row">
              <span className="user-name">MRPL Operations</span>
            </div>
            <span className="user-meta">engineer@mrpl.co.in</span>
          </div>
          <ChevronDown size={15} className="user-card-chevron" />
        </div>
      </div>
    </aside>
  );
}
