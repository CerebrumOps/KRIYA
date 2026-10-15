import React, { useState, useRef, useEffect } from 'react';
import {
  ArrowUp,
  Plus,
  FileText,
  Image as ImageIcon,
  X,
  Loader2,
  AlertCircle,
  Paperclip,
  Check
} from 'lucide-react';
import { uploadFileToWorkspace, UploadedFileItem } from '../../api/workspace_api';

export interface ChatInputProps {
  onSendMessage: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
  initialValue?: string;
  activeChatId?: string | null;
}

interface PendingAttachment {
  id: string;
  file: File;
  filename: string;
  sizeFormatted: string;
  status: 'uploading' | 'ready' | 'error';
  uploadedName?: string;
  uploadedPath?: string;
  error?: string;
  isImage: boolean;
  isPdf: boolean;
}

export default function ChatInput({ 
  onSendMessage, 
  disabled = false,
  placeholder = "Search P&ID diagrams, review inspection reports, execute calculations or attach photos/PDFs....",
  initialValue = "",
  activeChatId = null,
}: ChatInputProps) {
  const [input, setInput] = useState(initialValue);
  const [attachments, setAttachments] = useState<PendingAttachment[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (initialValue) {
      setInput(initialValue);
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }
  }, [initialValue]);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const processFiles = async (fileList: FileList | File[]) => {
    const rawFiles = Array.from(fileList);
    if (rawFiles.length === 0) return;

    const newAttachments: PendingAttachment[] = rawFiles.map((f) => {
      const isImage = f.type.startsWith('image/') || /\.(png|jpe?g|webp|bmp|tiff)$/i.test(f.name);
      const isPdf = f.type === 'application/pdf' || /\.pdf$/i.test(f.name);
      return {
        id: `${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
        file: f,
        filename: f.name,
        sizeFormatted: formatFileSize(f.size),
        status: 'uploading',
        isImage,
        isPdf,
      };
    });

    setAttachments((prev) => [...prev, ...newAttachments]);

    for (const att of newAttachments) {
      try {
        const res: UploadedFileItem = await uploadFileToWorkspace(att.file, activeChatId);
        setAttachments((prev) =>
          prev.map((item) =>
            item.id === att.id
              ? {
                  ...item,
                  status: 'ready',
                  uploadedName: res.filename,
                  uploadedPath: res.path,
                }
              : item
          )
        );
      } catch (err: any) {
        setAttachments((prev) =>
          prev.map((item) =>
            item.id === att.id
              ? {
                  ...item,
                  status: 'error',
                  error: err.message || 'Upload failed',
                }
              : item
          )
        );
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
      // Reset input value to allow selecting same file again
      e.target.value = '';
    }
  };

  const removeAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget.contains(e.relatedTarget as Node)) return;
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = input.trim();
    const isStillUploading = attachments.some((a) => a.status === 'uploading');

    if (isStillUploading) return;
    if (!trimmed && attachments.length === 0) return;
    if (disabled) return;

    // If any attachment had a transient error, retry uploading it now before sending
    const currentAttachments = [...attachments];
    for (let i = 0; i < currentAttachments.length; i++) {
      const att = currentAttachments[i];
      if (att.status === 'error') {
        try {
          const res = await uploadFileToWorkspace(att.file, activeChatId);
          currentAttachments[i] = {
            ...att,
            status: 'ready',
            uploadedName: res.filename,
            uploadedPath: res.path,
            error: undefined,
          };
        } catch (err: any) {
          console.error('Retry upload failed:', err);
          return; // Keep attachment and text in input so user doesn't lose context
        }
      }
    }

    const readyAttachments = currentAttachments.filter((a) => a.status === 'ready');
    if (!trimmed && readyAttachments.length === 0) return;

    let finalPrompt = trimmed;
    if (readyAttachments.length > 0) {
      const fileNotices = readyAttachments.map((a) => 
        `[Uploaded ${a.isImage ? 'Image/Photo' : a.isPdf ? 'PDF Document' : 'Document'} in Workspace: \`${a.uploadedName}\` at path \`${a.uploadedPath}\`]`
      ).join('\n');

      const toolCallsHint = readyAttachments.map((a) =>
        `ocr_extract_text(file_path="${a.uploadedPath}")`
      ).join(', ');

      if (finalPrompt) {
        finalPrompt = `${fileNotices}\n\nUser Request: ${finalPrompt}\n\n[System Instruction: Call \`${toolCallsHint}\` immediately to extract and read the text from the uploaded file before responding.]`;
      } else {
        finalPrompt = `${fileNotices}\n\nPlease inspect and analyze this uploaded document.\n\n[System Instruction: Call \`${toolCallsHint}\` immediately to extract and read the text from the uploaded file before responding.]`;
      }
    }

    onSendMessage(finalPrompt);
    setInput('');
    setAttachments([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  };

  const isUploadingAny = attachments.some((a) => a.status === 'uploading');
  const canSubmit = !disabled && !isUploadingAny && (Boolean(input.trim()) || attachments.some((a) => a.status === 'ready'));

  return (
    <div 
      className={`chat-input-wrapper ${isDragging ? 'drag-active' : ''}`}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Hidden file input triggered by "+" button */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        style={{ display: 'none' }}
        accept="image/*,.pdf,.txt,.csv,.json,.docx,.xlsx,.pptx"
        onChange={handleFileSelect}
      />

      <div className="chat-input-inner">
        {/* Drag-and-drop Visual Overlay */}
        {isDragging && (
          <div className="chat-dropzone-overlay">
            <Paperclip size={24} className="bounce-icon" />
            <span>Drop photos, scans, or PDFs here for OCR analysis</span>
          </div>
        )}

        <form className="chat-input-form" onSubmit={handleSubmit}>
          {/* Attachment Preview Chips Bar */}
          {attachments.length > 0 && (
            <div className="chat-attachments-tray">
              {attachments.map((att) => (
                <div key={att.id} className={`chat-attachment-chip status-${att.status}`}>
                  <div className="attachment-chip-icon">
                    {att.isImage ? (
                      <ImageIcon size={14} color="#0284c7" />
                    ) : (
                      <FileText size={14} color="#f59e0b" />
                    )}
                  </div>
                  <div className="attachment-chip-details">
                    <span className="attachment-chip-name" title={att.filename}>
                      {att.filename}
                    </span>
                    <span className="attachment-chip-size">
                      {att.sizeFormatted}
                    </span>
                  </div>
                  <div className="attachment-chip-status">
                    {att.status === 'uploading' && (
                      <Loader2 size={13} className="animate-spin text-muted" />
                    )}
                    {att.status === 'ready' && (
                      <span className="ocr-ready-pill" title="File uploaded and ready for OCR tool analysis">
                        <Check size={10} /> OCR Ready
                      </span>
                    )}
                    {att.status === 'error' && (
                      <span className="attachment-error-pill" title={att.error}>
                        <AlertCircle size={11} color="#ef4444" />
                      </span>
                    )}
                  </div>
                  <button
                    type="button"
                    className="attachment-chip-remove-btn"
                    onClick={() => removeAttachment(att.id)}
                    title="Remove attachment"
                  >
                    <X size={13} />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className={`chat-prompt-card ${input.includes('\n') || attachments.length > 0 ? 'multiline' : ''}`}>
            {/* "+" Add File Action Button */}
            <button
              type="button"
              className="card-attach-btn"
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled}
              title="Attach photo, diagram, or PDF for OCR analysis (+)"
              aria-label="Attach file"
            >
              <Plus size={16} strokeWidth={2.5} />
            </button>

            <textarea
              ref={textareaRef}
              id="chat-textarea"
              className="chat-textarea"
              placeholder={attachments.length > 0 ? "Add instructions for the model about this file (or press Send)..." : placeholder}
              value={input}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={disabled}
            />

            <button
              type="submit"
              id="send-message-btn"
              className={`card-send-btn ${canSubmit ? 'active' : ''}`}
              disabled={!canSubmit}
              aria-label="Send message"
            >
              <span className="send-btn-label">
                {isUploadingAny ? 'Uploading...' : 'Send'}
              </span>
              <div className="send-btn-icon-wrap">
                {isUploadingAny ? (
                  <Loader2 size={13} className="animate-spin" />
                ) : (
                  <ArrowUp size={13} strokeWidth={2.8} />
                )}
              </div>
            </button>
          </div>

          <div className="chat-input-bottom-bar">
            <span className="chat-input-hint">
              Air-gapped Sovereign AI • Drag & drop photos / PDFs for autonomous OCR • MRPL Process Integrity
            </span>
          </div>
        </form>
      </div>
    </div>
  );
}
