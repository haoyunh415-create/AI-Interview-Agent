"use client";

import { useTranslation } from "@/i18n";
import { CardSkeleton } from "@/components/ui/skeleton";
import type { UseMutationResult } from "@tanstack/react-query";

const TOPICS = [
  "Transformer 核心",
  "深度学习基础",
  "自然语言处理",
  "计算机视觉",
  "强化学习",
  "模型部署与优化",
  "推荐系统",
  "自定义",
];

const DEFAULT_TIMER = 120;

interface SessionItem {
  id: number;
  topic: string;
  stage_index: number;
  question_count: number;
}

interface InterviewSetupProps {
  apiKey: string;
  serverHasKey: boolean;
  topic: string;
  customTopic: string;
  timerEnabled: boolean;
  availableSessions: SessionItem[];
  startMutation: UseMutationResult<any, any, any, any>;
  resumeMutation: UseMutationResult<any, any, any, any>;
  onTopicChange: (topic: string) => void;
  onCustomTopicChange: (value: string) => void;
  onTimerToggle: (enabled: boolean) => void;
  onStart: () => void;
}

export function InterviewSetup({
  apiKey,
  serverHasKey,
  topic,
  customTopic,
  timerEnabled,
  availableSessions,
  startMutation,
  resumeMutation,
  onTopicChange,
  onCustomTopicChange,
  onTimerToggle,
  onStart,
}: InterviewSetupProps) {
  const { t } = useTranslation();

  return (
    <div
      className="smooth-scroll"
      style={{
        maxWidth: "var(--content-max-width)",
        margin: "0 auto",
        width: "100%",
        padding: "24px 16px",
        display: "flex",
        flexDirection: "column",
        gap: 16,
      }}
    >
      <div className="empty-state animate-fade-in" style={{ padding: "60px 20px" }}>
        <div style={{ fontSize: "2.5rem", opacity: 0.5 }}>🎙️</div>
        <h3 style={{ margin: 0, fontSize: "1rem", color: "var(--fg)" }}>
          {t("interview.title")}
        </h3>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", maxWidth: 360, textAlign: "center" }}>
          {t("interview.description")}
        </p>

        {/* Topic selector */}
        <div
          className="card-base"
          style={{
            padding: 16,
            width: "100%",
            maxWidth: 400,
            marginTop: 8,
          }}
        >
          <div className="section-title">{t("interview.select_topic")}</div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 6,
              marginBottom: topic === "自定义" ? 8 : 0,
            }}
          >
            {TOPICS.map((tpc) => (
              <button
                key={tpc}
                onClick={() => onTopicChange(tpc)}
                className={`tag ${topic === tpc ? "tag-primary" : "tag-muted"}`}
                style={{
                  cursor: "pointer",
                  padding: "8px 12px",
                  borderRadius: "var(--radius-sm)",
                  fontSize: "0.8rem",
                  border: topic === tpc ? "1px solid var(--primary)" : "1px solid var(--border)",
                  background:
                    topic === tpc ? "var(--primary-soft)" : "var(--card)",
                  color: topic === tpc ? "var(--primary-text)" : "var(--text-secondary)",
                  textAlign: "center",
                  transition: "all 0.15s",
                }}
              >
                {tpc}
              </button>
            ))}
          </div>
          {topic === "自定义" && (
            <input
              placeholder={t("interview.custom_topic")}
              value={customTopic}
              onChange={(e) => onCustomTopicChange(e.target.value)}
              className="input-base"
              style={{ width: "100%", padding: "8px 10px", fontSize: "0.82rem" }}
            />
          )}
        </div>

        {/* Timer toggle */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            fontSize: "0.82rem",
            color: "var(--text-secondary)",
          }}
        >
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              cursor: "pointer",
            }}
          >
            <input
              type="checkbox"
              checked={timerEnabled}
              onChange={(e) => onTimerToggle(e.target.checked)}
              style={{ accentColor: "var(--primary)", width: 16, height: 16, cursor: "pointer" }}
            />
            ⏱️ {t("interview.timer_label", { duration: DEFAULT_TIMER })}
          </label>
        </div>

        {startMutation.isPending && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12, width: "100%", maxWidth: 400 }}>
            <CardSkeleton lines={2} />
            <CardSkeleton lines={3} />
          </div>
        )}

        <button
          onClick={onStart}
          disabled={startMutation.isPending || (!apiKey && !serverHasKey)}
          className="btn-primary"
          style={{ marginTop: 12 }}
        >
          {startMutation.isPending ? t("interview.starting") : t("interview.start")}
        </button>

        {/* Session resume */}
        {availableSessions.length > 0 && (
          <div className="card-base" style={{ padding: 12, width: "100%", maxWidth: 400, marginTop: 4 }}>
            <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: 8 }}>
              📋 恢复未完成的面试
            </div>
            {availableSessions.slice(0, 3).map((s) => (
              <button
                key={s.id}
                onClick={() => resumeMutation.mutate(s.id)}
                disabled={resumeMutation.isPending}
                className="btn-ghost"
                style={{
                  width: "100%",
                  justifyContent: "flex-start",
                  padding: "6px 10px",
                  fontSize: "0.78rem",
                  marginBottom: 4,
                }}
              >
                ▶ {s.topic} · 阶段 {s.stage_index + 1} · {s.question_count} 题
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
