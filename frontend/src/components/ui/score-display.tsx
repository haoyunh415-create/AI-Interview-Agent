"use client";

interface ScoreDisplayProps {
  scoreText: string;
}

/**
 * Parses a score text (e.g. "8/10" or "7.5") and renders a visual badge.
 */
function extractScore(text: string): {
  score: number | null;
  maxScore: number | null;
  label: string;
} {
  // Try "X/Y" pattern
  const fractionMatch = text.match(/(\d+\.?\d*)\s*\/\s*(\d+)/);
  if (fractionMatch) {
    return {
      score: parseFloat(fractionMatch[1]),
      maxScore: parseInt(fractionMatch[2]),
      label: `${fractionMatch[1]}/${fractionMatch[2]}`,
    };
  }
  // Try "X%" pattern
  const pctMatch = text.match(/(\d+\.?\d*)\s*%/);
  if (pctMatch) {
    return {
      score: parseFloat(pctMatch[1]),
      maxScore: 100,
      label: `${pctMatch[1]}%`,
    };
  }
  return { score: null, maxScore: null, label: text };
}

export function ScoreBadge({ scoreText }: ScoreDisplayProps) {
  const { score, maxScore, label } = extractScore(scoreText);
  const pct = score !== null && maxScore !== null ? (score / maxScore) * 100 : null;

  let color = "var(--text-muted)";
  let bg = "var(--card-hover)";
  if (pct !== null) {
    if (pct >= 80) {
      color = "#22c55e";
      bg = "rgba(34, 197, 94, 0.12)";
    } else if (pct >= 60) {
      color = "#f59e0b";
      bg = "rgba(245, 158, 11, 0.12)";
    } else {
      color = "#ef4444";
      bg = "rgba(239, 68, 68, 0.12)";
    }
  }

  return (
    <span
      className="animate-fade-in"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: "3px 10px",
        borderRadius: "var(--radius-full)",
        background: bg,
        color,
        fontSize: "0.8rem",
        fontWeight: 600,
      }}
    >
      {pct !== null && pct >= 80 ? "🌟 " : pct !== null && pct >= 60 ? "📈 " : "📝 "}
      {label}
    </span>
  );
}

export function ScoreMeter({ scoreText }: ScoreDisplayProps) {
  const { score, maxScore, label } = extractScore(scoreText);
  const pct = score !== null && maxScore !== null ? (score / maxScore) * 100 : null;

  if (pct === null) {
    return <span style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>{label}</span>;
  }

  const color = pct >= 80 ? "#22c55e" : pct >= 60 ? "#f59e0b" : "#ef4444";

  return (
    <div style={{ width: "100%" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: 4,
        }}
      >
        <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
          得分
        </span>
        <span
          style={{
            fontSize: "0.9rem",
            fontWeight: 700,
            color,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {label}
        </span>
      </div>
      <div
        style={{
          width: "100%",
          height: 6,
          background: "var(--card-hover)",
          borderRadius: 4,
          overflow: "hidden",
        }}
      >
        <div
          className="animate-slide-in-right"
          style={{
            width: `${pct}%`,
            height: "100%",
            background: color,
            borderRadius: 4,
            transition: "width 0.8s cubic-bezier(0.4, 0, 0.2, 1)",
            boxShadow: `0 0 8px ${color}40`,
          }}
        />
      </div>
    </div>
  );
}
