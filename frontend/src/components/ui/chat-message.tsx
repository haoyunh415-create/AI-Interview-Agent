"use client";

import { useState, useCallback } from "react";
import { MarkdownRenderer } from "./markdown";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  isLoading?: boolean;
  isLast?: boolean;
  onRetry?: () => void;
  onCopy?: () => void;
}

function TypingDots() {
  return (
    <span className="typing-dots" style={{ fontSize: "0.95rem", color: "var(--text-muted)" }}>
      思考中
      <span>.</span><span>.</span><span>.</span>
    </span>
  );
}

function CopyButton({ onCopy }: { onCopy?: () => void }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    if (onCopy) {
      onCopy();
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  }, [onCopy]);

  return (
    <button
      onClick={handleCopy}
      title="复制消息"
      style={{
        padding: "3px 8px",
        fontSize: "0.65rem",
        lineHeight: 1,
        border: "none",
        borderRadius: 6,
        background: copied ? "rgba(34,197,94,0.2)" : "rgba(255,255,255,0.06)",
        color: copied ? "#22c55e" : "var(--text-dim)",
        cursor: "pointer",
        transition: "all 0.15s",
      }}
    >
      {copied ? "✓ 已复制" : "复制"}
    </button>
  );
}

export function ChatMessage({ role, content, isLoading, isLast, onRetry, onCopy }: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div
      className="chat-message"
      style={{
        display: "flex",
        gap: 12,
        padding: "12px 16px",
        maxWidth: 768,
        margin: "0 auto",
        width: "100%",
        flexDirection: isUser ? "row-reverse" : "row",
        alignItems: "flex-start",
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: 32, height: 32, borderRadius: 10,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "0.75rem", fontWeight: 700, flexShrink: 0,
          background: isUser ? "var(--primary)" : "var(--card-hover)",
          color: isUser ? "#fff" : "var(--primary-text)",
          border: isUser ? "none" : "1px solid var(--border)",
        }}
      >
        {isUser ? "U" : "AI"}
      </div>

      {/* Bubble */}
      <div style={{ maxWidth: "75%", display: "flex", flexDirection: "column", gap: 4 }}>
        <div
          style={{
            padding: "10px 16px",
            borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
            background: isUser ? "var(--primary)" : "var(--card)",
            color: isUser ? "#fff" : "var(--fg)",
            border: isUser ? "none" : "1px solid var(--border)",
            lineHeight: 1.7,
            fontSize: "0.95rem",
            wordBreak: "break-word",
            overflowWrap: "break-word",
          }}
        >
          {isLoading ? (
            <TypingDots />
          ) : isUser ? (
            <span style={{ whiteSpace: "pre-wrap" }}>{content}</span>
          ) : (
            <MarkdownRenderer content={content} />
          )}
        </div>

        {/* Action buttons row */}
        {!isUser && !isLoading && content && (
          <div style={{ display: "flex", gap: 4, paddingLeft: 4 }}>
            <CopyButton onCopy={onCopy} />
            {isLast && onRetry && (
              <button
                onClick={onRetry}
                title="重新生成"
                style={{
                  padding: "3px 8px",
                  fontSize: "0.65rem",
                  lineHeight: 1,
                  border: "none",
                  borderRadius: 6,
                  background: "rgba(255,255,255,0.06)",
                  color: "var(--text-dim)",
                  cursor: "pointer",
                  transition: "all 0.15s",
                }}
              >
                重新生成
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
