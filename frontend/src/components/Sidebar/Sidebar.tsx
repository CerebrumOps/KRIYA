import React from 'react';
import NewChat from './NewChat';
import ChatHistory, { HistoryItem } from './ChatHistory';
import './Sidebar.css';

export interface SidebarProps {
  history?: HistoryItem[];
  activeChatId?: string | null;
  onNewChat?: () => void;
  onSelectChat?: (id: string) => void;
  onDeleteChat?: (id: string) => void;
}

export default function Sidebar({ 
  history = [], 
  activeChatId = null, 
  onNewChat, 
  onSelectChat,
  onDeleteChat
}: SidebarProps) {
  return (
    <aside className="sidebar" aria-label="Chat sidebar">
      <div className="sidebar-header">
        <NewChat onNewChat={onNewChat || (() => {})} />
      </div>
      <ChatHistory 
        history={history} 
        activeChatId={activeChatId} 
        onSelectChat={onSelectChat} 
        onDeleteChat={onDeleteChat}
      />
    </aside>
  );
}
