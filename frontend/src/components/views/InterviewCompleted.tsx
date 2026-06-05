"use client";

import { useState } from "react";
import toast from "react-hot-toast";
import { useInterviewStore } from "@/stores/interviewStore";
import { useAppStore } from "@/stores/appStore";
import { ScoreBadge } from "@/components/ui/score-display";
import { useTranslation } from "@/i18n";
import type { UseMutationResult } from "@tanstack/react-query";

interface InterviewCompletedProps {
  startMutation: UseMutationResult<any, any, any, any>;
  bookmarkMutation: UseMutationResult<any, any, any, any>;
  batchBookmarkMutation: UseMutationResult<any, any, any, any>;
}

export function InterviewCompleted({
  startMutation,
  bookmarkMutation,
  batchBookmarkMutation,
}: InterviewCompletedProps) {
  const { t } = useTranslation();

  const interview = useInterviewStore((s) => s.interview);
  const history = useInterviewStore((s) => s.history);
  const topic = useInterviewStore((s) => s.topic);
  const resetInterview = useInterviewStore((s) => s.reset);
  const setTopic = useInterviewStore((s) => s.setTopic);

  const apiKey = useAppStore((s) => s.apiKey);
  const serverHasKey = useAppStore((s) => s.serverHasKey);
  const setMode = useAppStore((s) => s.setMode);

  const [bookmarkedSet, setBookmarkedSet] = useState<Set<string>>(new Set());

  const handleContinue = () => {
    const lastTopic = topic || "Transformer 核心";
    resetInterview();
    setTopic(lastTopic);
    toast.success("正在追加题目...");
    setTimeout(() => {
      if (apiKey || serverHasKey) {
        startMutation.mutate(lastTopic);
      }
    }, 100);
  };

  const handleViewReport = () => {
    const sid = interview?.session_id;
    if (sid) {
      fetch("/api/reports/" + sid + "?user=guest").catch(() => {});
      import("@/stores/reportStore").then((m) =>
        m.useReportStore.getState().setCurrentSession(sid)
      );
    }
    setMode("report");
  };

  return (
    <div
      className="smooth-scroll"
      style={{
        maxWidth: "var(--content-max-width)",
        margin: "0 auto",
        width: "100%",
        padding: "24px 16px",
      }}
    >
      <div className="empty-state animate-fade-in-scale" style={{ padding: "60px 20px" }}>
        <div style={{ fontSize: "3rem", marginBottom: 8 }}>🎉</div>
        <h3 style={{ margin: 0, fontSize: "1.2rem", color: "var(--fg)", fontWeight: 600 }}>
          {t("interview.completed")}
        </h3>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
          {t("interview.completed_desc")}
        </p>
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <button onClick={handleViewReport} className="btn-primary">
            📊 {t("interview.view_report")}
          </button>
          <button
            onClick={handleContinue}
            className="btn-ghost"
            style={{ color: "var(--primary-text)", borderColor: "var(--primary-soft)" }}
          >
            ➕ 追加题目
          </button>
          <button onClick={() => resetInterview()} className="btn-ghost">
            🔄 重新面试
          </button>
        </div>
      </div>

      {history.length > 0 && (
        <div className="card-base animate-fade-in" style={{ padding: 16, marginTop: 8 }}>
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8,
            marginBottom: 10, flexWrap: "wrap",
          }}>
            <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-muted)" }}>
              {t("interview.answered", { count: history.length })}
            </div>
            <button
              onClick={() => batchBookmarkMutation.mutate(history.map((h) => ({ q: h.q, a: h.a })))}
              disabled={batchBookmarkMutation.isPending}
              className="btn-ghost"
              style={{
                padding: "4px 10px", fontSize: "0.75rem",
                color: "var(--warning)", borderColor: "var(--warning-soft)",
              }}
            >
              ⭐ 全部收藏
            </button>
          </div>
          {history.map((h, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "6px 0",
                fontSize: "0.85rem",
                borderBottom: i < history.length - 1 ? "1px solid var(--border)" : "none",
              }}
            >
              <span
                style={{
                  width: 22, height: 22, borderRadius: "50%",
                  background: "var(--card-hover)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "0.65rem", fontWeight: 600,
                  color: "var(--text-muted)", flexShrink: 0,
                }}
              >
                {i + 1}
              </span>
              <span style={{
                color: "var(--text-secondary)", flex: 1,
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
              }}>
                {h.q}
              </span>
              {h.score && <ScoreBadge scoreText={h.score} />}
              <button
                onClick={() => {
                  bookmarkMutation.mutate({ question: h.q, answer: h.a });
                  setBookmarkedSet((prev) => { const n = new Set(prev); n.add(h.q); return n; });
                }}
                disabled={bookmarkMutation.isPending}
                className="btn-ghost"
                style={{
                  padding: "3px 10px", fontSize: "0.72rem", flexShrink: 0,
                  color: bookmarkedSet.has(h.q) ? "var(--warning)" : "var(--text-dim)",
                  borderColor: "transparent",
                }}
                title={bookmarkedSet.has(h.q) ? "已收藏" : "收藏本题"}
              >
                {bookmarkedSet.has(h.q) ? "⭐" : "☆"} 收藏
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
