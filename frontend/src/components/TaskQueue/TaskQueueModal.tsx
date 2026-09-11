import React, { useState } from 'react';
import { 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Play, 
  X, 
  Wrench, 
  FileText, 
  Edit3, 
  Save, 
  Cpu
} from 'lucide-react';
import { Plan, approvePlan, rejectPlan, updatePlan } from '../../api/plan_api';
import MarkdownRenderer from '../ChatArea/MarkdownRenderer';

export interface TaskQueueModalProps {
  plan: Plan | null;
  isOpen: boolean;
  onClose: () => void;
  onPlanApproved?: (updatedPlan: Plan) => void;
  onPlanRejected?: () => void;
  onPlanUpdated?: (updatedPlan: Plan) => void;
}

export default function TaskQueueModal({
  plan: initialPlan,
  isOpen,
  onClose,
  onPlanApproved,
  onPlanRejected,
  onPlanUpdated,
}: TaskQueueModalProps) {
  const [currentPlan, setCurrentPlan] = useState<Plan | null>(initialPlan);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Edit Plan Mode
  const [isEditingPlan, setIsEditingPlan] = useState(false);
  const [editedPlanMarkdown, setEditedPlanMarkdown] = useState('');

  // Keep local state in sync when initialPlan prop changes
  React.useEffect(() => {
    setCurrentPlan(initialPlan);
    if (initialPlan?.plan) {
      setEditedPlanMarkdown(initialPlan.plan);
    }
  }, [initialPlan]);

  if (!isOpen || !currentPlan) return null;

  const plan = currentPlan;

  const handleApprove = async () => {
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const updated = await approvePlan(plan.plan_id);
      setCurrentPlan(updated);
      if (onPlanApproved) onPlanApproved(updated);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to approve plan.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      await rejectPlan(plan.plan_id);
      setCurrentPlan(null);
      if (onPlanRejected) {
        onPlanRejected();
      } else {
        onClose();
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to reject plan.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSavePlanMarkdown = async () => {
    if (!editedPlanMarkdown.trim()) return;
    setIsSubmitting(true);
    try {
      const updated = await updatePlan(plan.plan_id, {
        plan: editedPlanMarkdown,
      });
      setCurrentPlan(updated);
      setIsEditingPlan(false);
      if (onPlanUpdated) onPlanUpdated(updated);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update plan content.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
      case 'IN_PROGRESS':
        return (
          <span style={{
            backgroundColor: 'rgba(14, 116, 144, 0.15)',
            color: '#0e7490',
            border: '1px solid rgba(14, 116, 144, 0.35)',
            padding: '2px 8px',
            borderRadius: 4,
            fontSize: 11,
            fontWeight: 700
          }}>
            APPROVED & ACTIVE
          </span>
        );
      case 'COMPLETED':
        return (
          <span style={{
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            color: '#10b981',
            border: '1px solid rgba(16, 185, 129, 0.35)',
            padding: '2px 8px',
            borderRadius: 4,
            fontSize: 11,
            fontWeight: 700
          }}>
            COMPLETED
          </span>
        );
      case 'REJECTED':
      case 'CANCELLED':
        return (
          <span style={{
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            color: '#ef4444',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            padding: '2px 8px',
            borderRadius: 4,
            fontSize: 11,
            fontWeight: 700
          }}>
            REJECTED
          </span>
        );
      default:
        return (
          <span style={{
            backgroundColor: 'rgba(245, 158, 11, 0.15)',
            color: '#f59e0b',
            border: '1px solid rgba(245, 158, 11, 0.35)',
            padding: '2px 8px',
            borderRadius: 4,
            fontSize: 11,
            fontWeight: 700
          }}>
            PENDING APPROVAL
          </span>
        );
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      backdropFilter: 'blur(5px)',
      zIndex: 9999,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 16
    }}>
      <div style={{
        backgroundColor: 'var(--c-card, #ffffff)',
        color: 'var(--c-text-primary, #0f172a)',
        borderRadius: 14,
        border: '1px solid var(--c-border, #e2e8f0)',
        maxWidth: 820,
        width: '100%',
        maxHeight: '88vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 25px 35px -5px rgba(0, 0, 0, 0.35)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 24px',
          borderBottom: '1px solid var(--c-border, #e2e8f0)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          backgroundColor: 'var(--c-bg-subtle, #f8fafc)'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, fontWeight: 700, color: '#0e7490', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                <FileText size={14} />
                <span>TASK PLAN SPECIFICATION</span>
              </span>
              {getStatusBadge(plan.status)}
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: 'var(--c-text-primary, #0f172a)' }}>
              {plan.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--c-text-muted, #64748b)',
              cursor: 'pointer',
              padding: 4
            }}
            title="Close Plan View"
          >
            <X size={20} />
          </button>
        </div>

        {/* Metadata Pill Strip */}
        <div style={{
          padding: '10px 24px',
          backgroundColor: 'var(--c-bg-subtle, #f1f5f9)',
          borderBottom: '1px solid var(--c-border, #e2e8f0)',
          display: 'flex',
          flexWrap: 'wrap',
          gap: 16,
          fontSize: 12
        }}>
          {plan.skill && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--c-text-secondary, #475569)' }}>
              <Wrench size={13} color="#0284c7" />
              <span>Skill Protocol: <strong>{plan.skill}</strong></span>
            </div>
          )}
          {plan.model_profile && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--c-text-secondary, #475569)' }}>
              <Cpu size={13} color="#8b5cf6" />
              <span>Model Routing: <strong>{plan.model_profile}</strong></span>
            </div>
          )}
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: '#0e7490', marginLeft: 'auto' }}>
            <span>Approval Gate: <strong>Operator Authorization Required</strong></span>
          </div>
        </div>

        {/* Body Container - Exclusively Full Strategic Plan Content */}
        <div style={{
          padding: '20px 24px',
          overflowY: 'auto',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: 14
        }}>
          {errorMsg && (
            <div style={{
              padding: '10px 14px',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: 6,
              color: '#ef4444',
              fontSize: 13
            }}>
              {errorMsg}
            </div>
          )}

          {/* Strategic Plan Content Box */}
          <div style={{
            border: '1px solid var(--c-border, #e2e8f0)',
            borderRadius: 10,
            overflow: 'hidden',
            backgroundColor: 'var(--c-card, #ffffff)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '10px 16px',
              backgroundColor: 'var(--c-bg-subtle, #f8fafc)',
              borderBottom: '1px solid var(--c-border, #e2e8f0)'
            }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--c-text-primary, #0f172a)' }}>
                Full Strategic Execution Plan
              </span>
              <button
                type="button"
                onClick={() => {
                  if (isEditingPlan) {
                    handleSavePlanMarkdown();
                  } else {
                    setEditedPlanMarkdown(plan.plan || '');
                    setIsEditingPlan(true);
                  }
                }}
                disabled={isSubmitting}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 4,
                  fontSize: 12,
                  fontWeight: 600,
                  padding: '3px 8px',
                  borderRadius: 4,
                  border: '1px solid var(--c-border, #cbd5e1)',
                  backgroundColor: 'transparent',
                  color: isEditingPlan ? '#10b981' : 'var(--c-text-secondary, #475569)',
                  cursor: 'pointer'
                }}
              >
                {isEditingPlan ? (
                  <>
                    <Save size={12} />
                    <span>Save Edits</span>
                  </>
                ) : (
                  <>
                    <Edit3 size={12} />
                    <span>Edit Plan</span>
                  </>
                )}
              </button>
            </div>

            <div style={{ padding: '16px 20px', fontSize: 13.5, lineHeight: 1.6 }}>
              {isEditingPlan ? (
                <textarea
                  value={editedPlanMarkdown}
                  onChange={(e) => setEditedPlanMarkdown(e.target.value)}
                  rows={14}
                  style={{
                    width: '100%',
                    padding: 12,
                    borderRadius: 6,
                    border: '1px solid var(--c-border, #cbd5e1)',
                    backgroundColor: 'var(--c-bg-subtle, #f8fafc)',
                    color: 'var(--c-text-primary, #0f172a)',
                    fontSize: 13,
                    fontFamily: 'monospace',
                    resize: 'vertical',
                    outline: 'none',
                    lineHeight: 1.5
                  }}
                />
              ) : (
                <MarkdownRenderer content={plan.plan || 'No strategic plan provided.'} />
              )}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div style={{
          padding: '14px 24px',
          borderTop: '1px solid var(--c-border, #e2e8f0)',
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
          gap: 12,
          backgroundColor: 'var(--c-bg-subtle, #f8fafc)'
        }}>
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: '8px 16px',
              borderRadius: 6,
              border: '1px solid var(--c-border, #cbd5e1)',
              backgroundColor: 'transparent',
              fontSize: 13,
              cursor: 'pointer',
              color: 'var(--c-text-secondary, #334155)'
            }}
          >
            Close
          </button>

          {plan.status === 'PENDING_APPROVAL' && (
            <>
              <button
                type="button"
                onClick={handleReject}
                disabled={isSubmitting}
                style={{
                  padding: '8px 16px',
                  borderRadius: 6,
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  backgroundColor: 'rgba(239, 68, 68, 0.08)',
                  color: '#ef4444',
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Reject Plan
              </button>
              <button
                type="button"
                onClick={handleApprove}
                disabled={isSubmitting}
                style={{
                  padding: '8px 20px',
                  borderRadius: 6,
                  border: 'none',
                  backgroundColor: '#0e7490',
                  color: '#ffffff',
                  fontSize: 13,
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  cursor: 'pointer',
                  boxShadow: '0 2px 4px rgba(14, 116, 144, 0.25)'
                }}
              >
                <Play size={14} />
                <span>{isSubmitting ? 'Approving...' : 'Approve Plan'}</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
