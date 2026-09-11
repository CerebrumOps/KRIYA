import React from 'react';
import { 
  Flame,
  ChevronDown,
  ShieldCheck,
  PanelLeftClose,
  Sun,
  Moon,
  LogOut
} from 'lucide-react';
import NewChat from './NewChat';
import ChatHistory, { HistoryItem } from './ChatHistory';
import { Employee } from '../../schemas/employee';
import './Sidebar.css';

export interface SidebarProps {
  currentUser?: Employee | null;
  history?: HistoryItem[];
  activeChatId?: string | null;
  theme?: 'light' | 'dark';
  onToggleTheme?: () => void;
  onNewChat?: () => void;
  onSelectChat?: (id: string) => void;
  onDeleteChat?: (id: string) => void;
  onSelectPrompt?: (prompt: string) => void;
  onToggleCollapse?: () => void;
  onSignOut?: () => void;
}

export default function Sidebar({ 
  currentUser = null,
  history = [], 
  activeChatId = null, 
  theme = 'light',
  onToggleTheme,
  onNewChat, 
  onSelectChat, 
  onDeleteChat,
  onSelectPrompt,
  onToggleCollapse,
  onSignOut
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
              <span>
                {currentUser?.employeeName
                  ? currentUser.employeeName
                      .split(' ')
                      .filter(Boolean)
                      .map((n) => n[0])
                      .slice(0, 2)
                      .join('')
                      .toUpperCase()
                  : 'OP'}
              </span>
            </div>
            <span className="user-status-dot" title="Air-Gapped | Secure" />
          </div>
          <div className="user-info-text">
            <div className="user-name-row">
              <span className="user-name">{currentUser?.employeeName || 'MRPL Operations'}</span>
            </div>
            <span className="user-meta" title={currentUser?.companyEmail || currentUser?.designation || 'engineer@mrpl.co.in'}>
              {currentUser?.companyEmail || currentUser?.designation || 'engineer@mrpl.co.in'}
            </span>
          </div>
          {onSignOut ? (
            <button
              type="button"
              className="sidebar-signout-btn"
              onClick={onSignOut}
              title="Sign Out / Return to Auth Screen"
              aria-label="Sign Out"
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--c-text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                padding: '4px',
                borderRadius: '6px',
                transition: 'color 0.15s ease, background-color 0.15s ease'
              }}
            >
              <LogOut size={15} />
            </button>
          ) : (
            <ChevronDown size={15} className="user-card-chevron" />
          )}
        </div>
      </div>
    </aside>
  );
}
