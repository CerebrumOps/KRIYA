import React, { useEffect, useState, useCallback } from 'react';
import {
  FileText,
  Sheet,
  Presentation,
  Download,
  CheckCircle2,
  X,
  FolderOpen,
  RefreshCw,
  FileCode,
  Inbox,
  Loader2
} from 'lucide-react';
import {
  fetchDeliverables,
  downloadDeliverable,
  DeliverableItem
} from '../../api/workspace_api';

export interface ArtifactsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activeChatId?: string | null;
}

export default function ArtifactsDrawer({
  isOpen,
  onClose,
  activeChatId,
}: ArtifactsDrawerProps) {
  const [artifacts, setArtifacts] = useState<DeliverableItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const loadDeliverables = useCallback(async () => {
    if (!activeChatId) {
      setArtifacts([]);
      return;
    }
    setLoading(true);
    try {
      const items = await fetchDeliverables(activeChatId);
      setArtifacts(items);
    } catch (err) {
      console.error('Failed to load deliverables:', err);
    } finally {
      setLoading(false);
    }
  }, [activeChatId]);

  useEffect(() => {
    if (isOpen) {
      loadDeliverables();
    }
  }, [isOpen, loadDeliverables]);

  if (!isOpen) return null;

  const handleDownload = async (filename: string, id: string) => {
    if (!activeChatId) return;
    setDownloadingId(id);
    try {
      await downloadDeliverable(activeChatId, filename);
    } catch (err: any) {
      alert(`Download failed: ${err.message || String(err)}`);
    } finally {
      setDownloadingId(null);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'docx':
        return <FileText size={20} color="#0284c7" />;
      case 'xlsx':
        return <Sheet size={20} color="#10b981" />;
      case 'pptx':
        return <Presentation size={20} color="#f59e0b" />;
      case 'csv':
        return <Sheet size={20} color="#06b6d4" />;
      case 'pdf':
        return <FileText size={20} color="#ef4444" />;
      case 'json':
      case 'py':
        return <FileCode size={20} color="#8b5cf6" />;
      default:
        return <FolderOpen size={20} color="#8b5cf6" />;
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: 440,
        maxWidth: '92vw',
        backgroundColor: 'var(--bg-panel, #ffffff)',
        borderLeft: '1px solid var(--border-color, #e2e8f0)',
        boxShadow: '-10px 0 25px -5px rgba(0, 0, 0, 0.15)',
        zIndex: 9998,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Drawer Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-color, #e2e8f0)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: 'var(--bg-panel-header, #f8fafc)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <FolderOpen size={18} color="#0e7490" />
          <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-main, #0f172a)' }}>
            Generated Deliverables
          </span>
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: '2px 7px',
              borderRadius: 10,
              backgroundColor: 'rgba(14, 116, 144, 0.12)',
              color: '#0e7490',
            }}
          >
            {artifacts.length}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <button
            type="button"
            onClick={loadDeliverables}
            title="Refresh deliverables"
            disabled={loading}
            style={{
              background: 'none',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer',
              color: 'var(--text-muted, #64748b)',
              padding: 4,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted, #64748b)',
              padding: 4,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Workspace Context Info Bar */}
      <div
        style={{
          padding: '8px 20px',
          backgroundColor: 'var(--bg-subtle, #f1f5f9)',
          borderBottom: '1px solid var(--border-color, #e2e8f0)',
          fontSize: 11.5,
          color: 'var(--text-muted, #64748b)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span>
          Chat Scope: <strong style={{ color: 'var(--text-main, #0f172a)' }}>{activeChatId ? activeChatId.slice(0, 14) + (activeChatId.length > 14 ? '...' : '') : 'None'}</strong>
        </span>
        <span style={{ fontSize: 10.5, color: '#0e7490' }}>
          Air-gapped Storage
        </span>
      </div>

      {/* Artifacts List or Empty State */}
      <div
        style={{
          padding: '16px 20px',
          overflowY: 'auto',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
        {loading && artifacts.length === 0 ? (
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-muted, #64748b)',
              gap: 12,
              minHeight: 250,
            }}
          >
            <Loader2 size={28} className="animate-spin" color="#0e7490" />
            <span style={{ fontSize: 13 }}>Scanning chat workspace...</span>
          </div>
        ) : artifacts.length === 0 ? (
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              padding: '40px 20px',
              color: 'var(--text-muted, #64748b)',
              gap: 12,
            }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                backgroundColor: 'rgba(14, 116, 144, 0.08)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#0e7490',
              }}
            >
              <Inbox size={24} />
            </div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-main, #0f172a)' }}>
              No deliverables generated yet
            </div>
            <p style={{ fontSize: 12, lineHeight: 1.5, maxWidth: 280, margin: 0 }}>
              When KRIYA creates technical approval notes (.docx), financial workbooks (.xlsx), or slide decks (.pptx), they will be saved here in this conversation's isolated workspace.
            </p>
          </div>
        ) : (
          artifacts.map((art) => (
            <div
              key={art.id}
              style={{
                padding: '14px',
                borderRadius: 8,
                border: '1px solid var(--border-color, #e2e8f0)',
                backgroundColor: 'var(--bg-card, #ffffff)',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                <div
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: 8,
                    backgroundColor: 'var(--bg-subtle, #f1f5f9)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  {getIcon(art.type)}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <span
                      style={{
                        fontSize: 13.5,
                        fontWeight: 600,
                        color: 'var(--text-main, #0f172a)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                      title={art.title}
                    >
                      {art.title}
                    </span>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 3,
                        fontSize: 10.5,
                        fontWeight: 600,
                        color: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        padding: '2px 6px',
                        borderRadius: 4,
                        flexShrink: 0,
                      }}
                    >
                      <CheckCircle2 size={11} />
                      <span>Verified</span>
                    </span>
                  </div>
                  <span
                    style={{
                      fontSize: 11,
                      fontFamily: 'monospace',
                      color: '#0e7490',
                      wordBreak: 'break-all',
                    }}
                  >
                    {art.name}
                  </span>
                </div>
              </div>

              <p
                style={{
                  margin: '2px 0 0',
                  fontSize: 12,
                  color: 'var(--text-muted, #64748b)',
                  lineHeight: 1.4,
                }}
              >
                {art.description}
              </p>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginTop: 4,
                  paddingTop: 8,
                  borderTop: '1px dashed var(--border-color, #f1f5f9)',
                }}
              >
                <div style={{ display: 'flex', gap: 8, fontSize: 11, color: 'var(--text-muted, #94a3b8)' }}>
                  <span>{art.size}</span>
                  <span>•</span>
                  <span>{art.generated_at}</span>
                </div>
                <button
                  type="button"
                  onClick={() => handleDownload(art.name, art.id)}
                  disabled={downloadingId === art.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 5,
                    padding: '5px 12px',
                    borderRadius: 4,
                    border: '1px solid var(--border-color, #cbd5e1)',
                    backgroundColor: 'var(--bg-subtle, #f8fafc)',
                    fontSize: 11.5,
                    fontWeight: 500,
                    cursor: downloadingId === art.id ? 'not-allowed' : 'pointer',
                    color: '#0e7490',
                    transition: 'background 0.15s ease',
                  }}
                >
                  {downloadingId === art.id ? (
                    <Loader2 size={12} className="animate-spin" />
                  ) : (
                    <Download size={12} />
                  )}
                  <span>Download</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
