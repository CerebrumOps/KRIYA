import React, { memo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import remarkGfm from 'remark-gfm';
import { Copy, Check } from 'lucide-react';

/**
 * Normalizes LaTeX delimiters so that:
 *  - \[ ... \] becomes $$ ... $$ (display equations)
 *  - \( ... \) becomes $ ... $ (inline equations)
 */
function preprocessLaTeX(content: string): string {
  if (!content || typeof content !== 'string') return '';
  return content
    .replace(/\\\[([\s\S]*?)\\\]/g, (_, equation) => `\n$$\n${equation.trim()}\n$$\n`)
    .replace(/\\\(([\s\S]*?)\\\)/g, (_, equation) => `$${equation.trim()}$`);
}

interface CodeBlockProps extends React.HTMLAttributes<HTMLElement> {
  className?: string;
  children?: React.ReactNode;
}

/**
 * Code Block component with language tag and clipboard copy button
 */
function CodeBlock({ className, children, ...props }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';
  const codeString = String(children).replace(/\n$/, '');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(codeString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
      setCopied(false);
    }
  };

  return (
    <div className="markdown-code-container">
      <div className="markdown-code-header">
        <span className="markdown-code-lang">{language || 'code'}</span>
        <button
          type="button"
          className="markdown-code-copy"
          onClick={handleCopy}
          title="Copy code"
        >
          {copied ? <Check size={13} className="copy-check" /> : <Copy size={13} />}
          <span>{copied ? 'Copied!' : 'Copy'}</span>
        </button>
      </div>
      <pre className="markdown-code-pre">
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    </div>
  );
}

export interface MarkdownRendererProps {
  content: string;
}

/**
 * Robust Markdown & LaTeX Equation Renderer
 */
const MarkdownRenderer = memo(function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const normalized = preprocessLaTeX(content);

  return (
    <div className="markdown-rendered-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[
          [
            rehypeKatex,
            {
              throwOnError: false,
              strict: false,
              output: 'htmlAndMathml',
            },
          ],
        ]}
        components={{
          // Custom code rendering: differentiates inline vs code-block
          code({ _node, inline, className, children, ...props }: any) {
            const hasNewline = String(children).includes('\n');
            if (!inline && (className || hasNewline)) {
              return (
                <CodeBlock className={className} {...props}>
                  {children}
                </CodeBlock>
              );
            }
            return (
              <code className="markdown-inline-code" {...props}>
                {children}
              </code>
            );
          },
          // Make pre element a transparent pass-through since CodeBlock handles container
          pre({ children }) {
            return <>{children}</>;
          },
          // External links open in new tab securely
          a({ href, children, ...props }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="markdown-link"
                {...props}
              >
                {children}
              </a>
            );
          },
          // Responsive table wrapper so wide tables scroll smoothly
          table({ children, ...props }) {
            return (
              <div className="markdown-table-wrapper">
                <table className="markdown-table" {...props}>
                  {children}
                </table>
              </div>
            );
          },
          // Clean paragraph spacing
          p({ children, ...props }) {
            return (
              <p className="markdown-paragraph" {...props}>
                {children}
              </p>
            );
          },
          // Styled blockquote
          blockquote({ children, ...props }) {
            return (
              <blockquote className="markdown-blockquote" {...props}>
                {children}
              </blockquote>
            );
          },
        }}
      >
        {normalized}
      </ReactMarkdown>
    </div>
  );
});

export default MarkdownRenderer;
