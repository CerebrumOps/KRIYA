import React from 'react';
import MessageList, { UIMessage } from './MessageList';
import ChatInput from './ChatInput';
import TaskChecklistPanel from './TaskChecklistPanel';
import { Plan, ChecklistItem } from '../../api/plan_api';
import './ChatArea.css';

export interface ChatAreaProps {
  messages?: UIMessage[];
  onSendMessage: (text: string) => void;
  onRequestPlan?: (text: string) => void;
  isLoading?: boolean;
  isPlanning?: boolean;
  activePlan?: Plan | null;
  checklistItems?: ChecklistItem[];
  isChecklistOpen?: boolean;
  onCloseChecklist?: () => void;
}

export default function ChatArea({ 
  messages = [], 
  onSendMessage, 
  onRequestPlan,
  isLoading = false,
  isPlanning = false,
  activePlan = null,
  checklistItems = [],
  isChecklistOpen = false,
  onCloseChecklist = () => {},
}: ChatAreaProps) {
  return (
    <main className="chat-area" aria-label="Main chat area">
      {isChecklistOpen && activePlan && (
        <TaskChecklistPanel
          plan={activePlan}
          items={checklistItems}
          isOpen={isChecklistOpen}
          onClose={onCloseChecklist}
        />
      )}

      <MessageList 
        messages={messages} 
        isLoading={isLoading} 
        onSelectPrompt={onSendMessage} 
      />

      <ChatInput 
        onSendMessage={onSendMessage} 
        onRequestPlan={onRequestPlan}
        disabled={isLoading} 
        isPlanning={isPlanning}
      />
    </main>
  );
}
