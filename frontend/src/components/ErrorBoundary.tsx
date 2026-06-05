"use client";

import React from "react";

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("[ErrorBoundary]", error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <ErrorFallback
          error={this.state.error}
          onReset={this.handleReset}
        />
      );
    }

    return this.props.children;
  }
}

/* ── Default fallback UI ── */
/**
 * ErrorBoundary with a default full-page fallback.
 * Use at the app root level.
 */
export function ErrorBoundaryWithFallback({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      fallback={
        <ErrorFallback error={null} onReset={() => window.location.reload()} fullPage />
      }
    >
      {children}
    </ErrorBoundary>
  );
}

export function ErrorFallback({
  error,
  onReset,
  fullPage = false,
}: {
  error: Error | null;
  onReset?: () => void;
  fullPage?: boolean;
}) {
  const containerStyle: React.CSSProperties = fullPage
    ? {
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        background: "var(--bg)",
        padding: 16,
      }
    : {
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        padding: 32,
      };

  return (
    <div style={containerStyle}>
      <div
        style={{
          textAlign: "center",
          maxWidth: 400,
          animation: "fadeInUp 0.35s ease-out",
        }}
      >
        <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>⚠️</div>
        <h2
          style={{
            fontSize: "1rem",
            fontWeight: 600,
            color: "var(--fg)",
            margin: "0 0 8px",
          }}
        >
          页面出现异常
        </h2>
        <p
          style={{
            fontSize: "0.85rem",
            color: "var(--text-muted)",
            lineHeight: 1.6,
            margin: "0 0 16px",
          }}
        >
          发生了意外错误。请尝试刷新页面，如果问题持续存在请联系支持。
        </p>

        {error?.message && (
          <details
            style={{
              marginBottom: 16,
              textAlign: "left",
              background: "var(--card)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
              padding: "10px 14px",
            }}
          >
            <summary
              style={{
                cursor: "pointer",
                fontSize: "0.78rem",
                color: "var(--text-muted)",
                fontWeight: 500,
              }}
            >
              错误详情
            </summary>
            <pre
              style={{
                marginTop: 8,
                fontSize: "0.72rem",
                color: "var(--danger)",
                lineHeight: 1.5,
                overflow: "auto",
                maxHeight: 150,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
              }}
            >
              {error.message}
              {error.stack && `\n\n${error.stack}`}
            </pre>
          </details>
        )}

        <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
          {onReset && (
            <button onClick={onReset} className="btn-primary">
              重试
            </button>
          )}
          <button
            onClick={() => window.location.reload()}
            className="btn-ghost"
          >
            刷新页面
          </button>
        </div>
      </div>
    </div>
  );
}
