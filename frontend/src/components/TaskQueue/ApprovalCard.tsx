import React, { useState } from 'react';
import { ShieldAlert, Globe, Terminal, Check, X } from 'lucide-react';
import { resolveApproval } from '../../api/plan_api';

export interface ApprovalCardProps {
  approvalId: string;
  actionType: string;
  details: Record<string, any>;
  onResolved: (approvalId: string, approved: boolean) => void;
}

export default function ApprovalCard({
  approvalId,
  actionType,
  details,
  onResolved,
}: ApprovalCardProps) {
  const [isBusy, setIsBusy] = useState(false);

  const handleAction = async (approved: boolean) => {
    setIsBusy(true);
    try {
      await resolveApproval(approvalId, approved);
      onResolved(approvalId, approved);
    } catch {
      onResolved(approvalId, approved);
    } finally {
      setIsBusy(false);
    }
  };

  const isWeb = actionType.includes('web') || actionType.includes('search');

  return (
    <div style={{
      margin: '12px 0',
      padding: '14px 16px',
      borderRadius: 10,
      backgroundColor: 'rgba(245, 158, 11, 0.08)',
      border: '1px solid rgba(245, 158, 11, 0.4)',
      display: 'flex',
      flexDirection: 'column',
      gap: 10
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{
          width: 28,
          height: 28,
          borderRadius: 6,
          backgroundColor: 'rgba(245, 158, 11, 0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#d97706'
        }}>
          {isWeb ? <Globe size={16} /> : <Terminal size={16} />}
        </div>
        <div>
          <span style={{ fontSize: 13, fontWeight: 600, color: '#b45309' }}>
            Human Approval Gate: {isWeb ? 'Air-Gapped External Web Query' : 'Terminal Execution'}
          </span>
          <p style={{ margin: 0, fontSize: 12, color: 'var(--text-muted, #64748b)' }}>
            {isWeb
              ? 'KRIYA is requesting authorization to egress air-gapped boundary for DuckDuckGo search:'
              : 'KRIYA is requesting execution permission for command:'}
          </p>
        </div>
      </div>

      <div style={{
        padding: '8px 12px',
        borderRadius: 6,
        backgroundColor: 'rgba(0, 0, 0, 0.04)',
        fontFamily: 'monospace',
        fontSize: 12.5,
        color: 'var(--text-main, #0f172a)'
      }}>
        {details?.query || details?.command || JSON.stringify(details)}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 2 }}>
        <button
          type="button"
          onClick={() => handleAction(false)}
          disabled={isBusy}
          style={{
            padding: '6px 14px',
            borderRadius: 6,
            border: '1px solid rgba(239, 68, 68, 0.3)',
            backgroundColor: 'transparent',
            color: '#ef4444',
            fontSize: 12.5,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 4
          }}
        >
          <X size={14} />
          <span>Deny Query</span>
        </button>

        <button
          type="button"
          onClick={() => handleAction(true)}
          disabled={isBusy}
          style={{
            padding: '6px 16px',
            borderRadius: 6,
            border: 'none',
            backgroundColor: '#0e7490',
            color: '#ffffff',
            fontSize: 12.5,
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 4
          }}
        >
          <Check size={14} />
          <span>Authorize Access</span>
        </button>
      </div>
    </div>
  );
}
