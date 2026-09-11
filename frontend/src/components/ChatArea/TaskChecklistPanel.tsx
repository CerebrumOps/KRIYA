import React, { useState } from 'react';
import { 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Loader2, 
  ChevronDown, 
  ChevronUp, 
  X, 
  ListChecks,
  Sparkles
} from 'lucide-react';
import { ChecklistItem, Plan } from '../../api/plan_api';

export interface TaskChecklistPanelProps {
  plan: Plan | null;
  items: ChecklistItem[];
  isOpen: boolean;
  onClose: () => void;
}

export default function TaskChecklistPanel({
  plan,
  items,
  isOpen,
  onClose,
}: TaskChecklistPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  if (!isOpen || !plan || items.length === 0) return null;

  const totalCount = items.length;
  const completedCount = items.filter((it) => it.status === 'success' || it.status === 'completed').length;
  const isAllDone = totalCount > 0 && completedCount === totalCount;
  const isAnyRunning = items.some((it) => it.status === 'in_progress' || it.status === 'running');
  const percent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
      case 'completed':
        return <CheckCircle2 size={15} color="#10b981" style={{ flexShrink: 0 }} />;
      case 'in_progress':
      case 'running':
        return <Loader2 size={15} color="#0284c7" className="spin-icon" style={{ flexShrink: 0 }} />;
      case 'failed':
        return <AlertTriangle size={15} color="#ef4444" style={{ flexShrink: 0 }} />;
      default:
        return <Clock size={15} color="var(--c-text-muted, #94a3b8)" style={{ flexShrink: 0 }} />;
    }
  };

  return (
    <div
      style={{
        margin: '12px 20px 8px 20px',
        borderRadius: 10,
        border: '1px solid var(--c-border, #e2e8f0)',
        backgroundColor: 'var(--c-card, #ffffff)',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.06)',
        overflow: 'hidden',
        transition: 'all 0.2s ease',
      }}
    >
      {/* Panel Header */}
      <div
        style={{
          padding: '10px 16px',
          backgroundColor: isAllDone
            ? 'rgba(16, 185, 129, 0.08)'
            : 'var(--c-bg-subtle, #f8fafc)',
          borderBottom: isCollapsed ? 'none' : '1px solid var(--c-border, #e2e8f0)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 0 }}>
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: 6,
              backgroundColor: isAllDone ? 'rgba(16, 185, 129, 0.15)' : 'rgba(14, 116, 144, 0.12)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isAllDone ? '#10b981' : '#0e7490',
              flexShrink: 0,
            }}
          >
            {isAllDone ? <Sparkles size={16} /> : <ListChecks size={16} />}
          </div>

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span
                style={{
                  fontSize: 13,
                  fontWeight: 700,
                  color: 'var(--c-text-primary, #0f172a)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                Plan Execution Checklist
              </span>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  padding: '2px 7px',
                  borderRadius: 4,
                  backgroundColor: isAllDone
                    ? 'rgba(16, 185, 129, 0.15)'
                    : isAnyRunning
                    ? 'rgba(2, 132, 199, 0.15)'
                    : 'var(--c-bg-subtle, #e2e8f0)',
                  color: isAllDone ? '#10b981' : isAnyRunning ? '#0284c7' : 'var(--c-text-secondary, #475569)',
                }}
              >
                {isAllDone ? 'COMPLETED' : isAnyRunning ? 'RUNNING' : 'IN PROGRESS'}
              </span>
            </div>
            <div
              style={{
                fontSize: 11.5,
                color: 'var(--c-text-secondary, #64748b)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {plan.title}
            </div>
          </div>
        </div>

        {/* Progress & Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 3 }}>
            <span style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--c-text-primary, #0f172a)' }}>
              {completedCount} / {totalCount} Done ({percent}%)
            </span>
            <div
              style={{
                width: 90,
                height: 5,
                borderRadius: 3,
                backgroundColor: 'var(--c-border, #cbd5e1)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${percent}%`,
                  height: '100%',
                  backgroundColor: isAllDone ? '#10b981' : '#0e7490',
                  borderRadius: 3,
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <button
              type="button"
              onClick={() => setIsCollapsed(!isCollapsed)}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--c-text-muted, #64748b)',
                padding: 4,
                display: 'flex',
                alignItems: 'center',
              }}
              title={isCollapsed ? 'Expand checklist' : 'Collapse checklist'}
            >
              {isCollapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
            </button>
            <button
              type="button"
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--c-text-muted, #64748b)',
                padding: 4,
                display: 'flex',
                alignItems: 'center',
              }}
              title="Dismiss checklist panel"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Checklist Items (Collapsible) */}
      {!isCollapsed && (
        <div
          style={{
            padding: '10px 16px',
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            maxHeight: 220,
            overflowY: 'auto',
          }}
        >
          {items.map((it, idx) => {
            const isDone = it.status === 'success' || it.status === 'completed';
            const isRunning = it.status === 'in_progress' || it.status === 'running';

            return (
              <div
                key={it.id || idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '6px 10px',
                  borderRadius: 6,
                  backgroundColor: isRunning
                    ? 'rgba(2, 132, 199, 0.06)'
                    : isDone
                    ? 'rgba(16, 185, 129, 0.05)'
                    : 'var(--c-bg-subtle, #f8fafc)',
                  border: isRunning
                    ? '1px solid rgba(2, 132, 199, 0.3)'
                    : '1px solid var(--c-border, #f1f5f9)',
                  transition: 'background 0.2s ease',
                }}
              >
                {getStatusIcon(it.status)}

                <span
                  style={{
                    fontSize: 12.5,
                    fontWeight: isRunning ? 600 : 500,
                    color: isDone
                      ? 'var(--c-text-secondary, #64748b)'
                      : 'var(--c-text-primary, #0f172a)',
                    textDecoration: isDone ? 'line-through' : 'none',
                    flex: 1,
                  }}
                >
                  {it.task}
                </span>

                {it.tool && (
                  <span
                    style={{
                      fontSize: 10.5,
                      fontFamily: 'monospace',
                      color: '#0e7490',
                      backgroundColor: 'rgba(14, 116, 144, 0.08)',
                      padding: '2px 6px',
                      borderRadius: 4,
                      flexShrink: 0,
                    }}
                  >
                    {it.tool}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
