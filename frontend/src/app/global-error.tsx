"use client";

import { useEffect } from "react";

interface Props {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: Props) {
  useEffect(() => {
    console.error("[GlobalError]", error);
  }, [error]);

  return (
    <html lang="zh-CN">
      <head>
        <style>{`
          :root {
            --bg: #0c0c12;
            --fg: #eeedf2;
            --card: #1a1a24;
            --border: #2a2a3a;
            --text-muted: #6b6a80;
            --primary: #10a37f;
            --text-secondary: #9d9cb0;
            --danger: #ef4444;
            --radius-md: 10px;
          }
          * { box-sizing: border-box; margin: 0; padding: 0; }
          body {
            background: var(--bg);
            color: var(--fg);
            font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 16px;
          }
        `}</style>
      </head>
      <body>
        <div style={{ textAlign: "center", maxWidth: 400 }}>
          <div style={{ fontSize: "3rem", marginBottom: 16 }}>💥</div>
          <h1 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: 8 }}>
            应用崩溃了
          </h1>
          <p
            style={{
              fontSize: "0.88rem",
              color: "var(--text-muted)",
              lineHeight: 1.6,
              marginBottom: 16,
            }}
          >
            发生了严重错误，应用无法继续运行。
            {error.digest && (
              <span style={{ display: "block", fontSize: "0.72rem", marginTop: 8 }}>
                错误 ID: {error.digest}
              </span>
            )}
          </p>
          <div style={{ color: "var(--danger)", fontSize: "0.78rem", marginBottom: 20 }}>
            {error.message}
          </div>
          <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
            <button
              onClick={reset}
              style={{
                padding: "10px 24px",
                borderRadius: "var(--radius-md)",
                border: "none",
                background: "var(--primary)",
                color: "#fff",
                fontSize: "0.9rem",
                cursor: "pointer",
                fontWeight: 500,
              }}
            >
              重试
            </button>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: "10px 24px",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border)",
                background: "transparent",
                color: "var(--text-secondary)",
                fontSize: "0.9rem",
                cursor: "pointer",
              }}
            >
              刷新页面
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
