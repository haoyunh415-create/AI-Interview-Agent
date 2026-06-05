"use client";

import dynamic from "next/dynamic";
import React from "react";

/* ── Lightweight MetricCard (stays in main bundle) ── */
export function MetricCard({
  icon, label, value, sub,
}: {
  icon: string; label: string; value: string; sub?: string;
}) {
  return (
    <div className="card-base" style={{ padding: "16px", textAlign: "center" }}>
      <div style={{ fontSize: "1.5rem", marginBottom: 6 }}>{icon}</div>
      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--fg)", fontVariantNumeric: "tabular-nums" }}>
        {value}
      </div>
      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 4 }}>{label}</div>
      {sub && <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

/* ── Charts (heavy — dynamically imported) ── */

const ChartsInner = dynamic(
  () => import("@/components/ui/charts-inner"),
  { ssr: false },
);

function ChartFallback() {
  return (
    <div style={{ display: "flex", gap: 12 }}>
      <div className="skeleton" style={{ flex: 1, height: 260, borderRadius: 8 }} />
      <div className="skeleton" style={{ flex: 1, height: 240, borderRadius: 8 }} />
    </div>
  );
}

interface RadarData { topic: string; score: number }
interface BarData { stage: string; score: number }

export function TopicRadar({ data }: { data: RadarData[] }) {
  if (data.length === 0) return null;
  return (
    <React.Suspense fallback={<div className="skeleton" style={{ height: 260, borderRadius: 8 }} />}>
      <ChartsInner type="radar" data={data} />
    </React.Suspense>
  );
}

export function StageBar({ data }: { data: BarData[] }) {
  if (data.length === 0) return null;
  return (
    <React.Suspense fallback={<div className="skeleton" style={{ height: 240, borderRadius: 8 }} />}>
      <ChartsInner type="bar" data={data} />
    </React.Suspense>
  );
}
