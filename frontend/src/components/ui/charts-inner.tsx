"use client";

import { useState, useEffect, useRef } from "react";
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from "recharts";

// Suppress harmless recharts "width/height should be greater than 0" warning
// that fires on initial mount before layout is computed.
const _orig = console.warn;
console.warn = (...a: unknown[]) => {
  if (typeof a[0] === "string" && a[0].includes("width(-1) and height(-1)")) return;
  _orig(...a);
};

interface RadarData { topic: string; score: number }
interface BarData { stage: string; score: number }

const TOPIC_COLORS = ["#10a37f", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"];

interface ChartsInnerProps {
  type: "radar" | "bar";
  data: RadarData[] | BarData[];
}

export default function ChartsInner({ type, data }: ChartsInnerProps) {
  const [ready, setReady] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Only render charts after the container has been laid out with a real size
  useEffect(() => {
    const el = containerRef.current;
    if (el && el.clientWidth > 0 && el.clientHeight > 0) {
      setReady(true);
      return;
    }
    const timer = setInterval(() => {
      if (containerRef.current && containerRef.current.clientWidth > 10) {
        setReady(true);
        clearInterval(timer);
      }
    }, 50);
    return () => clearInterval(timer);
  }, []);

  if (data.length === 0) {
    return (
      <div style={{ height: 200, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)", fontSize: "0.85rem" }}>
        暂无数据
      </div>
    );
  }

  const content = type === "radar" ? (
    <RadarChart data={data as RadarData[]} cx="50%" cy="50%" outerRadius="70%">
      <PolarGrid stroke="var(--border)" />
      <PolarAngleAxis dataKey="topic" tick={{ fill: "var(--text-secondary)", fontSize: 11 }} />
      <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: "var(--text-muted)", fontSize: 10 }} tickCount={5} />
      <Radar dataKey="score" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.2} strokeWidth={2} />
    </RadarChart>
  ) : (
    <BarChart data={data as BarData[]} margin={{ top: 8, right: 8, left: -16, bottom: 4 }}>
      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
      <XAxis dataKey="stage" tick={{ fill: "var(--text-secondary)", fontSize: 11 }} axisLine={{ stroke: "var(--border)" }} />
      <YAxis domain={[0, 100]} tick={{ fill: "var(--text-muted)", fontSize: 10 }} axisLine={{ stroke: "var(--border)" }} />
      <Tooltip contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--fg)", fontSize: 12 }} formatter={(value: unknown) => [`${value}分`, "得分"]} />
      <Bar dataKey="score" radius={[4, 4, 0, 0]} maxBarSize={40}>
        {(data as BarData[]).map((_, i) => <Cell key={i} fill={TOPIC_COLORS[i % TOPIC_COLORS.length]} fillOpacity={0.8} />)}
      </Bar>
    </BarChart>
  );

  return (
    <div ref={containerRef} style={{ width: "100%", minWidth: 200, height: type === "radar" ? 260 : 240 }}>
      {ready ? (
        <ResponsiveContainer width="100%" height="100%">
          {content}
        </ResponsiveContainer>
      ) : (
        <div className="skeleton" style={{ width: "100%", height: "100%", borderRadius: 8 }} />
      )}
    </div>
  );
}
