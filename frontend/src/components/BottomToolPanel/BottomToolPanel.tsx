import React, { useState } from 'react';
import { 
  Wrench, 
  Terminal, 
  Copy, 
  Check, 
  CheckCircle2, 
  Loader2, 
  AlertCircle, 
  ChevronUp, 
  ChevronDown, 
  Clock, 
  FolderGit2 
} from 'lucide-react';
import { ToolCallItem } from '../RightPanel/ToolCalling';
import './BottomToolPanel.css';

export interface BottomToolPanelProps {
  toolCalls?: ToolCallItem[];
  isExpanded?: boolean;
  onToggleExpand?: () => void;
  isAnyRunning?: boolean;
}

export default function BottomToolPanel({ 
  toolCalls = [], 
  isExpanded = false, 
  onToggleExpand,
  isAnyRunning = false 
}: BottomToolPanelProps) {
  const [copiedId, setCopiedId] = useState<string | number | null>(null);

  const handleCopy = (id: string | number, text: any, e?: React.MouseEvent) => {
    e?.stopPropagation();
    navigator.clipboard.writeText(typeof text === 'string' ? text : JSON.stringify(text, null, 2));
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const hasTools = toolCalls.length > 0;
  const hasErrors = toolCalls.some((tc) => tc.status === 'failed' || tc.status === 'error');

  // If there are no tools and not running, keep panel collapsed/hidden
  const panelClass = [
    'bottom-tool-panel',
    !hasTools && !isAnyRunning ? 'panel-hidden' : isExpanded ? 'panel-expanded' : 'panel-collapsed',
    isAnyRunning ? 'panel-running' : '',
  ].filter(Boolean).join(' ');

  return (
    <section 
      className={panelClass} 
      aria-label="Bottom tool execution panel"
      aria-expanded={isExpanded}
    >
      {/* 1. Interactive Collapsible Header / Dropdown Trigger */}
      <div 
        className="bottom-tool-header" 
        onClick={onToggleExpand}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (onToggleExpand) onToggleExpand();
          }
        }}
        title={isExpanded ? "Collapse tool execution panel" : "Expand tool execution panel"}
      >
        <div className="bottom-tool-header-left">
          <div className={`tool-icon-circle ${isAnyRunning ? 'icon-pulse' : hasTools ? 'icon-active' : ''}`}>
            {isAnyRunning ? (
              <Loader2 size={15} className="spinner-icon tool-amber" />
            ) : (
              <Wrench size={15} className="tool-green" />
            )}
          </div>
          <span className="bottom-tool-title">Tool Executions</span>

          {hasTools && (
            <span className="bottom-tool-count-badge">
              {toolCalls.length}
            </span>
          )}

          {isAnyRunning && (
            <span className="bottom-tool-status-pill pill-running">
              <Loader2 size={11} className="spinner-icon" />
              Running on host...
            </span>
          )}

          {!isAnyRunning && hasTools && !hasErrors && (
            <span className="bottom-tool-status-pill pill-completed">
              <CheckCircle2 size={11} />
              Completed
            </span>
          )}

          {!isAnyRunning && hasTools && hasErrors && (
            <span className="bottom-tool-status-pill pill-failed">
              <AlertCircle size={11} />
              Issues detected
            </span>
          )}
        </div>

        <div className="bottom-tool-header-right">
          <button 
            type="button" 
            className="bottom-tool-toggle-btn"
            aria-label={isExpanded ? "Collapse panel" : "Expand panel"}
          >
            <span className="toggle-label">{isExpanded ? 'Collapse' : 'Expand'}</span>
            {isExpanded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
          </button>
        </div>
      </div>

      {/* 2. Expandable Scrollable Content Area */}
      <div className="bottom-tool-body">
        {!hasTools ? (
          <div className="bottom-tool-empty-state">
            <div className="empty-tool-icon">
              <Terminal size={22} />
            </div>
            <div className="empty-tool-text-group">
              <p className="empty-tool-title">No Active Tool Executions</p>
              <span className="empty-tool-desc">
                When the agent triggers local terminal commands or SCADA telemetry queries, live arguments and stdout will appear here.
              </span>
            </div>
          </div>
        ) : (
          <div className="bottom-tool-list">
            {toolCalls.map((call, idx) => {
              const isRunning = call.status === 'running';
              const isError = call.status === 'error' || call.status === 'failed';
              const formattedArgs =
                typeof call.args === 'string'
                  ? call.args
                  : JSON.stringify(call.args, null, 2);

              const resultObj = typeof call.result === 'object' && call.result !== null ? call.result : null;
              const formattedResult =
                typeof call.result === 'string'
                  ? call.result
                  : JSON.stringify(call.result, null, 2);

              const execTime = resultObj?.execution_time_ms;
              const cwd = resultObj?.cwd;

              return (
                <div 
                  key={call.id || idx} 
                  className={`bottom-tool-card ${isRunning ? 'card-running' : isError ? 'card-failed' : 'card-success'}`}
                >
                  {/* Card Header */}
                  <div className="bottom-card-header">
                    <div className="bottom-card-title-wrap">
                      <span className="card-index">#{idx + 1}</span>
                      <Terminal size={13} className="card-term-icon" />
                      <span className="card-tool-name">{call.name}</span>
                    </div>

                    <div className="bottom-card-meta-wrap">
                      {execTime && (
                        <span className="card-meta-pill" title="Execution duration">
                          <Clock size={10} />
                          {Math.round(execTime)}ms
                        </span>
                      )}
                      {cwd && (
                        <span className="card-meta-pill cwd-pill" title={`Working directory: ${cwd}`}>
                          <FolderGit2 size={10} />
                          {cwd.split(/[\\/]/).pop()}
                        </span>
                      )}
                      <span className={`card-status-badge status-${call.status || 'completed'}`}>
                        {isRunning ? (
                          <>
                            <Loader2 size={10} className="spinner-icon" />
                            Running
                          </>
                        ) : isError ? (
                          <>
                            <AlertCircle size={10} />
                            Failed
                          </>
                        ) : (
                          <>
                            <CheckCircle2 size={10} />
                            Completed
                          </>
                        )}
                      </span>
                    </div>
                  </div>

                  {/* Card Columns (Responsive Side-by-Side on Desktop) */}
                  <div className="bottom-card-grid">
                    {/* Left Column: Arguments */}
                    {call.args && (
                      <div className="bottom-block-container">
                        <div className="bottom-block-header">
                          <span className="bottom-block-title">Parameters & Arguments</span>
                          <button
                            type="button"
                            className="bottom-copy-btn"
                            onClick={(e) => handleCopy(`arg-${call.id || idx}`, formattedArgs, e)}
                            title="Copy arguments JSON"
                          >
                            {copiedId === `arg-${call.id || idx}` ? <Check size={11} /> : <Copy size={11} />}
                            <span>{copiedId === `arg-${call.id || idx}` ? 'Copied' : 'Copy'}</span>
                          </button>
                        </div>
                        <pre className="bottom-code-pre args-pre">{formattedArgs}</pre>
                      </div>
                    )}

                    {/* Right Column: Execution Output */}
                    {call.result && (
                      <div className="bottom-block-container">
                        <div className="bottom-block-header">
                          <span className="bottom-block-title">Execution Result</span>
                          <button
                            type="button"
                            className="bottom-copy-btn"
                            onClick={(e) => handleCopy(`res-${call.id || idx}`, formattedResult, e)}
                            title="Copy output"
                          >
                            {copiedId === `res-${call.id || idx}` ? <Check size={11} /> : <Copy size={11} />}
                            <span>{copiedId === `res-${call.id || idx}` ? 'Copied' : 'Copy'}</span>
                          </button>
                        </div>
                        <pre className={`bottom-code-pre result-pre ${isError ? 'pre-error' : 'pre-success'}`}>
                          {formattedResult}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
