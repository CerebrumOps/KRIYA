import React from 'react';
import ToolCalling, { ToolCallItem } from './ToolCalling';
import './RightPanel.css';

export interface RightPanelProps {
  toolCalls?: ToolCallItem[];
}

export default function RightPanel({ toolCalls = [] }: RightPanelProps) {
  return (
    <aside className="right-panel dedicated-tool-panel" aria-label="Tool Calling inspection panel">
      <ToolCalling toolCalls={toolCalls} />
    </aside>
  );
}
