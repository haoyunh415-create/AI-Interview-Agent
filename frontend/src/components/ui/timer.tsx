"use client";

import { useEffect, useRef, useCallback } from "react";

interface InterviewTimerProps {
  duration: number; // seconds
  running: boolean;
  onExpire: () => void;
  onTick?: (remaining: number) => void;
}

export function InterviewTimer({
  duration,
  running,
  onExpire,
  onTick,
}: InterviewTimerProps) {
  const remainingRef = useRef(duration);
  const startRef = useRef<number | null>(null);
  const frameRef = useRef<number>(0);
  const expiredRef = useRef(false);

  const tick = useCallback(
    (timestamp: number) => {
      if (!running || expiredRef.current) return;
      if (startRef.current === null) startRef.current = timestamp;

      const elapsed = (timestamp - startRef.current) / 1000;
      const remaining = Math.max(0, duration - elapsed);
      remainingRef.current = remaining;
      onTick?.(remaining);

      if (remaining <= 0 && !expiredRef.current) {
        expiredRef.current = true;
        onExpire();
        return;
      }

      frameRef.current = requestAnimationFrame(tick);
    },
    [duration, running, onExpire, onTick],
  );

  useEffect(() => {
    if (running) {
      startRef.current = null;
      expiredRef.current = false;
      remainingRef.current = duration;
      frameRef.current = requestAnimationFrame(tick);
    } else {
      cancelAnimationFrame(frameRef.current);
    }

    return () => cancelAnimationFrame(frameRef.current);
  }, [running, duration, tick]);

  // Reset on duration change
  useEffect(() => {
    remainingRef.current = duration;
  }, [duration]);

  return null; // visual rendering handled by parent via onTick
}

/* ── Visual countdown display ── */
export function TimerDisplay({
  remaining,
  duration,
}: {
  remaining: number;
  duration: number;
}) {
  const pct = duration > 0 ? (remaining / duration) * 100 : 0;
  const seconds = Math.ceil(remaining);
  const min = Math.floor(seconds / 60);
  const sec = seconds % 60;

  const isLow = seconds <= 15;
  const isCritical = seconds <= 5;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "4px 12px",
        borderRadius: "var(--radius-full)",
        background: isCritical
          ? "var(--danger-soft)"
          : isLow
            ? "var(--warning-soft)"
            : "var(--card-hover)",
        border: "1px solid",
        borderColor: isCritical
          ? "var(--danger)"
          : isLow
            ? "var(--warning)"
            : "var(--border)",
        transition: "all 0.3s ease",
        animation: isCritical ? "borderPulse 0.6s ease-in-out infinite" : "none",
      }}
    >
      {/* Icon */}
      <span
        style={{
          fontSize: "0.85rem",
          animation: isCritical ? "pulse 0.6s ease-in-out infinite" : "none",
        }}
      >
        ⏱️
      </span>

      {/* Circular progress */}
      <svg width="20" height="20" viewBox="0 0 36 36" style={{ flexShrink: 0 }}>
        <circle
          cx="18"
          cy="18"
          r="15"
          fill="none"
          stroke="var(--border)"
          strokeWidth="3"
        />
        <circle
          cx="18"
          cy="18"
          r="15"
          fill="none"
          stroke={
            isCritical
              ? "var(--danger)"
              : isLow
                ? "var(--warning)"
                : "var(--primary)"
          }
          strokeWidth="3"
          strokeDasharray={`${pct} ${100 - pct}`}
          strokeDashoffset={25}
          strokeLinecap="round"
          style={{
            transition: "stroke-dasharray 0.5s ease, stroke 0.3s ease",
            transform: "rotate(-90deg)",
            transformOrigin: "center",
          }}
        />
      </svg>

      {/* Time text */}
      <span
        style={{
          fontSize: "0.8rem",
          fontWeight: 700,
          fontVariantNumeric: "tabular-nums",
          color: isCritical
            ? "var(--danger)"
            : isLow
              ? "var(--warning)"
              : "var(--fg)",
          minWidth: 36,
          transition: "color 0.3s ease",
        }}
      >
        {`${min}:${sec.toString().padStart(2, "0")}`}
      </span>
    </div>
  );
}
