import React, { useState } from 'react';
import {
  Wrench,
  Terminal,
  Copy,
  Check,
  CheckCircle2,
  Loader2,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Clock,
  FolderGit2
} from 'lucide-react';

export interface ToolCallItem {
  id?: string;
  name: string;
  status?: 'running' | 'completed' | 'error' | 'failed' | string;
  args?: any;
  result?: any;
}

import './RightToolPanel.css';
import { copyTextToClipboard } from '../../utils/clipboard';

export interface RightToolPanelProps {
  toolCalls?: ToolCallItem[];
  isExpanded?: boolean;
  onToggleExpand?: () => void;
  isAnyRunning?: boolean;
}

export default function RightToolPanel({
  toolCalls = [],
  isExpanded = false,
  onToggleExpand,
  isAnyRunning = false,
}: RightToolPanelProps) {
  const [copiedId, setCopiedId] = useState<string | number | null>(null);

  const handleCopy = async (id: string | number, text: any, e?: React.MouseEvent) => {
    e?.stopPropagation();
    const str = typeof text === 'string' ? text : JSON.stringify(text, null, 2);
    const ok = await copyTextToClipboard(str);
    if (ok) {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const hasTools = toolCalls.length > 0;
  const hasErrors = toolCalls.some((tc) => tc.status === 'failed' || tc.status === 'error');

  // Classes for animation and display state
  const panelClass = [
    'right-tool-panel',
    !hasTools && !isAnyRunning ? 'right-panel-hidden' : isExpanded ? 'right-panel-expanded' : 'right-panel-collapsed',
    isAnyRunning ? 'right-panel-running' : '',
  ].filter(Boolean).join(' ');

  return (
    <aside
      className={panelClass}
      aria-label="Tool execution panel"
      aria-expanded={isExpanded}
    >
      {/* -------------------------------------------------------------
          A. COLLAPSED RAIL VIEW (When panel is minimized to a slim bar)
          ------------------------------------------------------------- */}
      <div
        className="right-rail-bar"
        onClick={onToggleExpand}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (onToggleExpand) onToggleExpand();
          }
        }}
        title={isExpanded ? 'Collapse tool panel' : 'Expand tool execution panel'}
      >
        <button
          type="button"
          className="rail-toggle-btn"
          aria-label={isExpanded ? 'Collapse panel' : 'Expand panel'}
        >
          {isExpanded ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>

        <div className={`rail-icon-wrapper ${isAnyRunning ? 'rail-icon-pulse' : hasTools ? 'rail-icon-active' : ''}`}>
          {isAnyRunning ? (
            <Loader2 size={16} className="spinner-icon tool-amber" />
          ) : (
            <Wrench size={16} className="tool-green" />
          )}
        </div>

        {hasTools && (
          <span className="rail-count-badge">
            {toolCalls.length}
          </span>
        )}

        <div className="rail-vertical-title">
          <span>Tool Executions</span>
        </div>

        <div className="rail-status-dot-wrap">
          {isAnyRunning ? (
            <span className="rail-dot dot-running" title="Running tools on host..." />
          ) : hasErrors ? (
            <span className="rail-dot dot-error" title="Issues detected" />
          ) : (
            <span className="rail-dot dot-success" title="Completed" />
          )}
        </div>
      </div>

      {/* -------------------------------------------------------------
          B. EXPANDED PANEL VIEW (Full tool inspection details)
          ------------------------------------------------------------- */}
      <div className="right-panel-inner">
        {/* Panel Header */}
        <div className="right-panel-header">
          <div className="panel-header-title-group">
            <div className={`tool-header-icon-box ${isAnyRunning ? 'header-icon-pulse' : ''}`}>
              {isAnyRunning ? (
                <Loader2 size={15} className="spinner-icon tool-amber" />
              ) : (
                <Wrench size={15} className="tool-green" />
              )}
            </div>
            <div className="panel-title-text-wrap">
              <h3 className="panel-title-heading">Tool Executions</h3>
              {hasTools && (
                <span className="panel-count-badge">{toolCalls.length} active</span>
              )}
            </div>
          </div>

          <div className="panel-header-actions">
            {isAnyRunning && (
              <span className="status-pill pill-running">
                <Loader2 size={11} className="spinner-icon" />
                Active
              </span>
            )}
            {!isAnyRunning && hasTools && !hasErrors && (
              <span className="status-pill pill-completed">
                <CheckCircle2 size={11} />
                Done
              </span>
            )}
            <button
              type="button"
              className="panel-collapse-btn"
              onClick={onToggleExpand}
              title="Collapse to right bar"
              aria-label="Collapse panel"
            >
              <ChevronRight size={17} />
            </button>
          </div>
        </div>

        {/* Panel Content List */}
        <div className="right-panel-body">
          {!hasTools ? (
            <div className="right-empty-state">
              <div className="empty-state-icon-box">
                <Terminal size={24} />
              </div>
              <p className="empty-state-title">No Active Tools</p>
              <span className="empty-state-hint">
                When the agent triggers terminal commands or plant telemetry, live outputs will slide out here.
              </span>
            </div>
          ) : (
            <div className="right-tools-list">
              {toolCalls.map((call, idx) => {
                const isRunning = call.status === 'running';
                const isError = call.status === 'error' || call.status === 'failed';
                const formattedArgs =
                  typeof call.args === 'string'
                    ? call.args
                    : JSON.stringify(call.args, null, 2);

                const resultObj =
                  typeof call.result === 'object' && call.result !== null ? call.result : null;
                const formattedResult =
                  typeof call.result === 'string'
                    ? call.result
                    : JSON.stringify(call.result, null, 2);

                const execTime = resultObj?.execution_time_ms;
                const cwd = resultObj?.cwd;

                return (
                  <div
                    key={call.id || idx}
                    className={`tool-execution-card ${isRunning ? 'card-running' : isError ? 'card-failed' : 'card-success'}`}
                  >
                    {/* Tool Header */}
                    <div className="tool-card-top">
                      <div className="tool-card-identity">
                        <span className="tool-card-index">#{idx + 1}</span>
                        <span className="tool-card-name">{call.name}</span>
                      </div>

                      <span className={`tool-badge-status status-${call.status || 'completed'}`}>
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

                    {/* Metadata: execution time & cwd */}
                    {(execTime || cwd) && (
                      <div className="tool-card-metadata">
                        {execTime && (
                          <span className="card-meta-tag" title="Execution duration">
                            <Clock size={10} />
                            {Math.round(execTime)}ms
                          </span>
                        )}
                        {cwd && (
                          <span className="card-meta-tag cwd-tag" title={`Working directory: ${cwd}`}>
                            <FolderGit2 size={10} />
                            {cwd.split(/[\\/]/).pop()}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Parameters & Arguments */}
                    {call.args && (
                      <div className="tool-sub-block">
                        <div className="sub-block-header">
                          <span className="sub-block-label">Parameters & Arguments</span>
                          <button
                            type="button"
                            className="mini-copy-btn"
                            onClick={(e) => handleCopy(`args-${call.id || idx}`, formattedArgs, e)}
                            title="Copy arguments"
                          >
                            {copiedId === `args-${call.id || idx}` ? <Check size={11} /> : <Copy size={11} />}
                            <span>{copiedId === `args-${call.id || idx}` ? 'Copied' : 'Copy'}</span>
                          </button>
                        </div>
                        <pre className="code-box args-box">{formattedArgs}</pre>
                      </div>
                    )}

                    {/* Execution Result */}
                    {call.result && (
                      <div className="tool-sub-block">
                        <div className="sub-block-header">
                          <span className="sub-block-label">Execution Result</span>
                          <button
                            type="button"
                            className="mini-copy-btn"
                            onClick={(e) => handleCopy(`res-${call.id || idx}`, formattedResult, e)}
                            title="Copy output"
                          >
                            {copiedId === `res-${call.id || idx}` ? <Check size={11} /> : <Copy size={11} />}
                            <span>{copiedId === `res-${call.id || idx}` ? 'Copied' : 'Copy'}</span>
                          </button>
                        </div>
                        <pre className={`code-box result-box ${isError ? 'box-error' : 'box-success'}`}>
                          {formattedResult}
                        </pre>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
