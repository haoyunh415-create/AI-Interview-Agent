"use client";

import React, { useState, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import type { Components } from "react-markdown";

/* ── Copy Button ── */
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    }
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      title="复制代码"
      style={{
        position: "absolute",
        top: 4,
        right: 4,
        padding: "4px 8px",
        fontSize: "0.7rem",
        lineHeight: 1,
        border: "none",
        borderRadius: 6,
        background: copied ? "rgba(34,197,94,0.2)" : "rgba(255,255,255,0.08)",
        color: copied ? "#22c55e" : "rgba(255,255,255,0.5)",
        cursor: "pointer",
        transition: "all 0.15s",
        zIndex: 2,
        fontWeight: 500,
      }}
    >
      {copied ? "✓ 已复制" : "复制"}
    </button>
  );
}

/* ── Markdown Renderer (heavy — loaded via dynamic import) ── */
interface MarkdownRendererInnerProps {
  content: string;
}

export default function MarkdownRendererInner({ content }: MarkdownRendererInnerProps) {
  const components: Partial<Components> = {
    code({ className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || "");
      const codeText = String(children).replace(/\n$/, "");

      if (match) {
        return (
          <div style={{ margin: "8px 0", position: "relative" }}>
            <div className="code-lang-label">{match[1]}</div>
            <CopyButton text={codeText} />
            <SyntaxHighlighter
              style={oneDark}
              language={match[1]}
              PreTag="div"
              customStyle={{
                margin: 0,
                borderRadius: "0 0 8px 8px",
                fontSize: "0.82rem",
              }}
            >
              {codeText}
            </SyntaxHighlighter>
          </div>
        );
      }

      return (
        <code
          style={{
            background: "var(--card-hover)",
            color: "var(--primary-text)",
            padding: "2px 6px",
            borderRadius: 4,
            fontSize: "0.85em",
          }}
          {...props}
        >
          {children}
        </code>
      );
    },
    p({ children }) {
      return (
        <p style={{ margin: "0 0 8px", lineHeight: 1.7, wordBreak: "break-word" }}>
          {children}
        </p>
      );
    },
    ul({ children }) {
      return <ul style={{ margin: "0 0 8px", paddingLeft: 20, lineHeight: 1.8 }}>{children}</ul>;
    },
    ol({ children }) {
      return <ol style={{ margin: "0 0 8px", paddingLeft: 20, lineHeight: 1.8 }}>{children}</ol>;
    },
    li({ children }) {
      return <li style={{ marginBottom: 4 }}>{children}</li>;
    },
    h1({ children }) {
      return <h1 style={{ fontSize: "1.2rem", fontWeight: 600, margin: "16px 0 8px" }}>{children}</h1>;
    },
    h2({ children }) {
      return <h2 style={{ fontSize: "1.1rem", fontWeight: 600, margin: "14px 0 6px" }}>{children}</h2>;
    },
    h3({ children }) {
      return (
        <h3 style={{ fontSize: "1rem", fontWeight: 600, margin: "12px 0 4px", color: "var(--primary-text)" }}>
          {children}
        </h3>
      );
    },
    blockquote({ children }) {
      return (
        <blockquote style={{ borderLeft: "3px solid var(--primary)", paddingLeft: 12, margin: "8px 0", color: "var(--text-secondary)", opacity: 0.9 }}>
          {children}
        </blockquote>
      );
    },
    a({ href, children }) {
      return (
        <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: "var(--primary)", textDecoration: "underline" }}>
          {children}
        </a>
      );
    },
    hr() {
      return <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "16px 0" }} />;
    },
    table({ children }) {
      return <div style={{ overflowX: "auto", margin: "8px 0" }}><table style={{ borderCollapse: "collapse", width: "100%", fontSize: "0.85rem" }}>{children}</table></div>;
    },
    th({ children }) {
      return <th style={{ border: "1px solid var(--border)", padding: "6px 10px", textAlign: "left", background: "var(--card-hover)", fontWeight: 600 }}>{children}</th>;
    },
    td({ children }) {
      return <td style={{ border: "1px solid var(--border)", padding: "6px 10px" }}>{children}</td>;
    },
  };

  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]} components={components}>
      {content}
    </ReactMarkdown>
  );
}
