import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, Trash2 } from 'lucide-react';

export interface HistoryItem {
  id: string;
  title: string;
}

export interface ChatHistoryProps {
  history?: HistoryItem[];
  activeChatId?: string | null;
  onSelectChat?: (id: string) => void;
  onDeleteChat?: (id: string) => void;
}

interface ContextMenuState {
  x: number;
  y: number;
  chatId: string;
}

export default function ChatHistory({ 
  history = [], 
  activeChatId = null, 
  onSelectChat,
  onDeleteChat
}: ChatHistoryProps) {
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close context menu on outside click or Escape key
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setContextMenu(null);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setContextMenu(null);
      }
    };

    if (contextMenu) {
      document.addEventListener('mousedown', handleOutsideClick);
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [contextMenu]);

  // Handle right-click on a chat item
  const handleContextMenu = (e: React.MouseEvent, chatId: string) => {
    e.preventDefault();
    e.stopPropagation();

    // Position menu near cursor while preventing viewport overflow
    const menuWidth = 175;
    const menuHeight = 56;
    const x = Math.min(e.clientX, window.innerWidth - menuWidth - 12);
    const y = Math.min(e.clientY, window.innerHeight - menuHeight - 12);

    setContextMenu({ x, y, chatId });
  };

  const handleContextDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (contextMenu?.chatId && onDeleteChat) {
      onDeleteChat(contextMenu.chatId);
    }
    setContextMenu(null);
  };

  const handleDirectDelete = (e: React.MouseEvent, chatId: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (onDeleteChat) {
      onDeleteChat(chatId);
    }
  };

  return (
    <div className="chat-history-section">
      <div className="chat-history-header">
        <span>Chat History</span>
      </div>
      
      <div className="chat-history-list">
        {history.length === 0 ? (
          <div className="chat-history-empty">
            No previous chats
          </div>
        ) : (
          history.map((item) => {
            const isActive = activeChatId === item.id;
            return (
              <div
                key={item.id}
                className={`chat-history-item-wrapper ${isActive ? 'active' : ''}`}
                onContextMenu={(e) => handleContextMenu(e, item.id)}
              >
                <button
                  type="button"
                  className={`chat-history-item ${isActive ? 'active' : ''}`}
                  onClick={() => onSelectChat && onSelectChat(item.id)}
                  onContextMenu={(e) => handleContextMenu(e, item.id)}
                  title={`${item.title} (Right-click to delete)`}
                >
                  <MessageSquare size={16} className="history-item-icon" />
                  <span className="history-item-title">{item.title}</span>
                </button>

                {/* Direct delete button (visible on hover) */}
                <button
                  type="button"
                  className="chat-item-delete-btn"
                  onClick={(e) => handleDirectDelete(e, item.id)}
                  title="Delete chat"
                  aria-label="Delete chat"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Floating Right-Click Context Menu */}
      {contextMenu && (
        <div
          ref={menuRef}
          className="chat-context-menu"
          style={{ top: `${contextMenu.y}px`, left: `${contextMenu.x}px` }}
          role="menu"
        >
          <button
            type="button"
            className="context-menu-item context-menu-delete"
            onClick={handleContextDelete}
            role="menuitem"
          >
            <Trash2 size={14} className="context-menu-icon" />
            <span>Delete Chat</span>
          </button>
        </div>
      )}
    </div>
  );
}
