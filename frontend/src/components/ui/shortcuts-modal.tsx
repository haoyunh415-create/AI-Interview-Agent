"use client";

import { useEffect, useState, useCallback } from "react";

interface Props {
  open: boolean;
  onClose: () => void;
}

const ITEMS = [
  { keys: "Ctrl+1-5", desc: "切换模式" },
  { keys: "Ctrl+Enter", desc: "发送消息 / 提交回答" },
  { keys: "Shift+Enter", desc: "换行" },
  { keys: "Escape", desc: "关闭设置 / 弹窗" },
  { keys: "?", desc: "显示此帮助" },
];

export function ShortcutsModal({ open, onClose }: Props) {
  const [visible, setVisible] = useState(open);

  useEffect(() => {
    setVisible(open);
  }, [open]);

  const close = useCallback(() => {
    setVisible(false);
    setTimeout(onClose, 150);
  }, [onClose]);

  useEffect(() => {
    if (!visible) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        close();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [visible, close]);

  if (!visible) return null;

  return (
    <div
      onClick={close}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(0,0,0,0.5)",
        backdropFilter: "blur(4px)",
        padding: 16,
        animation: "fadeIn 0.2s ease-out",
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "var(--card)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)",
          padding: 24,
          maxWidth: 400,
          width: "100%",
          boxShadow: "var(--shadow-lg)",
          animation: "fadeInScale 0.25s ease-out",
        }}
      >
        <h3
          style={{
            margin: "0 0 16px",
            fontSize: "1rem",
            fontWeight: 600,
            color: "var(--fg)",
          }}
        >
          ⌨️ 快捷键
        </h3>

        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {ITEMS.map((item) => (
            <div
              key={item.keys}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "6px 0",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <kbd
                style={{
                  background: "var(--card-hover)",
                  padding: "3px 8px",
                  borderRadius: 4,
                  fontSize: "0.78rem",
                  color: "var(--primary-text)",
                  fontWeight: 600,
                  fontFamily: "monospace",
                  border: "1px solid var(--border)",
                }}
              >
                {item.keys}
              </kbd>
              <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                {item.desc}
              </span>
            </div>
          ))}
        </div>

        <button
          onClick={close}
          style={{
            marginTop: 16,
            width: "100%",
            padding: "10px 20px",
            border: "none",
            borderRadius: "var(--radius-md)",
            background: "var(--primary)",
            color: "#fff",
            fontSize: "0.9rem",
            fontWeight: 500,
            cursor: "pointer",
          }}
        >
          关闭
        </button>
      </div>
    </div>
  );
}
