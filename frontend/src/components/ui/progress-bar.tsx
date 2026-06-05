"use client";

interface ProgressBarProps {
  current: number;
  total: number;
  label?: string;
}

export function ProgressBar({ current, total, label }: ProgressBarProps) {
  const pct = total > 0 ? Math.round((current / total) * 100) : 0;

  return (
    <div style={{ width: "100%" }}>
      {(label || total > 0) && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 6,
          }}
        >
          {label && (
            <span
              style={{
                fontSize: "0.72rem",
                fontWeight: 600,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: 0.5,
              }}
            >
              {label}
            </span>
          )}
          <span
            style={{
              fontSize: "0.75rem",
              color: "var(--text-secondary)",
              fontWeight: 500,
            }}
          >
            {current}/{total}
          </span>
        </div>
      )}
      <div
        style={{
          width: "100%",
          height: 4,
          background: "var(--card-hover)",
          borderRadius: 4,
          overflow: "hidden",
          position: "relative",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: "var(--primary)",
            borderRadius: 4,
            transition: "width 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
            boxShadow: "0 0 8px var(--primary-glow)",
          }}
        />
      </div>
    </div>
  );
}

interface StepIndicatorProps {
  steps: string[];
  currentIndex: number;
}

export function StepIndicator({ steps, currentIndex }: StepIndicatorProps) {
  return (
    <div
      style={{
        display: "flex",
        gap: 4,
        alignItems: "center",
        justifyContent: "center",
        padding: "4px 0",
      }}
    >
      {steps.map((label, i) => (
        <div
          key={i}
          style={{ display: "flex", alignItems: "center", gap: 4 }}
        >
          <div
            style={{
              width: 24,
              height: 24,
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "0.7rem",
              fontWeight: 600,
              background:
                i <= currentIndex ? "var(--primary)" : "var(--card-hover)",
              color: i <= currentIndex ? "#fff" : "var(--text-muted)",
              transition: "all 0.3s ease",
              boxShadow:
                i === currentIndex ? "0 0 12px var(--primary-glow)" : "none",
            }}
          >
            {i + 1}
          </div>
          <span
            style={{
              fontSize: "0.7rem",
              color:
                i === currentIndex
                  ? "var(--primary-text)"
                  : i < currentIndex
                    ? "var(--text-secondary)"
                    : "var(--text-muted)",
              fontWeight: i === currentIndex ? 600 : 400,
              display: "none",
            }}
          >
            {label}
          </span>
        </div>
      ))}
    </div>
  );
}
