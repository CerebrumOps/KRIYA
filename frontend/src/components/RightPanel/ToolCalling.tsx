import React, { useState } from 'react';
import { Wrench, Terminal, Copy, Check, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';

export interface ToolCallItem {
  id?: string;
  name: string;
  status?: 'running' | 'completed' | 'error' | 'failed' | string;
  args?: any;
  result?: any;
}

export interface ToolCallingProps {
  toolCalls?: ToolCallItem[];
}

export default function ToolCalling({ toolCalls = [] }: ToolCallingProps) {
  const [copiedId, setCopiedId] = useState<string | number | null>(null);

  const handleCopy = (id: string | number, text: any) => {
    navigator.clipboard.writeText(typeof text === 'string' ? text : JSON.stringify(text, null, 2));
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const isAnyRunning = toolCalls.some((tc) => tc.status === 'running');

  return (
    <section className="panel-section tool-calling-section" aria-label="Tool Calling panel">
      <div className="panel-header">
        <div className="panel-title-wrapper">
          <Wrench size={16} className={`panel-icon tool-icon ${isAnyRunning ? 'tool-icon-active' : ''}`} />
          <h3 className="panel-title">Tool Executions</h3>
        </div>
        <div className="panel-header-actions">
          {isAnyRunning && (
            <span className="tool-running-badge">
              <Loader2 size={11} className="spinner-icon" />
              Active
            </span>
          )}
          {toolCalls.length > 0 && (
            <span className="panel-badge tool-badge">{toolCalls.length}</span>
          )}
        </div>
      </div>

      <div className="panel-content">
        {toolCalls.length === 0 ? (
          <div className="panel-empty-state">
            <div className="empty-state-icon-tool">
              <Terminal size={24} />
            </div>
            <p className="empty-state-text">No tool calls executed.</p>
            <span className="empty-state-hint">
              When the model triggers automated tools, SCADA queries, or API calls, their live arguments and results will appear here.
            </span>
          </div>
        ) : (
          <div className="tool-calls-list">
            {toolCalls.map((call, idx) => {
              const isRunning = call.status === 'running';
              const isError = call.status === 'error' || call.status === 'failed';
              const formattedArgs =
                typeof call.args === 'string'
                  ? call.args
                  : JSON.stringify(call.args, null, 2);

              return (
                <div key={call.id || idx} className={`tool-call-item ${isRunning ? 'tool-item-running' : ''}`}>
                  <div className="tool-call-header">
                    <div className="tool-name-wrapper">
                      <span className="tool-index">#{idx + 1}</span>
                      <span className="tool-name">{call.name}</span>
                    </div>
                    <span className={`tool-status status-${call.status || 'completed'}`}>
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

                  {call.args && (
                    <div className="tool-block">
                      <div className="tool-block-header">
                        <span className="tool-block-title">Parameters & Arguments</span>
                        <button
                          type="button"
                          className="copy-btn"
                          onClick={() => handleCopy(call.id || idx, formattedArgs)}
                          title="Copy JSON arguments"
                        >
                          {copiedId === (call.id || idx) ? <Check size={11} /> : <Copy size={11} />}
                          <span>{copiedId === (call.id || idx) ? 'Copied' : 'Copy'}</span>
                        </button>
                      </div>
                      <pre className="tool-args">{formattedArgs}</pre>
                    </div>
                  )}

                  {call.result && (
                    <div className="tool-block">
                      <div className="tool-block-header">
                        <span className="tool-block-title">Execution Result</span>
                      </div>
                      <pre className="tool-result">
                        {typeof call.result === 'string'
                          ? call.result
                          : JSON.stringify(call.result, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
