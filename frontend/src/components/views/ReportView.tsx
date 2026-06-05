"use client";

import { useState, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { listReportSessions, getSessionReport } from "@/lib/api";
import type { StageBreakdown, SessionReportItem, SessionReportDetail } from "@/lib/api";
import { useAppStore } from "@/stores/appStore";
import { useReportStore } from "@/stores/reportStore";
import { MarkdownRenderer } from "@/components/ui/markdown";
import { CardSkeleton } from "@/components/ui/skeleton";

function StageCard({ stage }: { stage: StageBreakdown }) {
  const score = stage.score;
  const color = score != null
    ? score >= 80 ? "var(--success)" : score >= 60 ? "var(--primary)" : score >= 40 ? "var(--warning)" : "var(--danger)"
    : "var(--text-dim)";

  return (
    <div className="card-base" style={{ padding: 14, marginBottom: 10 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <div className="section-title" style={{ margin: 0 }}>{stage.stage}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {stage.skipped_count > 0 && (
            <span className="chip chip-warning" style={{ fontSize: "0.7rem" }}>⏭️ {stage.skipped_count}跳过</span>
          )}
          {score != null ? (
            <span style={{ fontSize: "0.85rem", fontWeight: 700, color }}>{score}</span>
          ) : (
            <span style={{ fontSize: "0.78rem", color: "var(--text-dim)" }}>未评分</span>
          )}
        </div>
      </div>
      {stage.questions.map((q, i) => (
        <div key={i} style={{ marginBottom: 6, padding: "6px 10px", background: "var(--bg)", borderRadius: "var(--radius-sm)" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--fg)", fontWeight: 500, marginBottom: 2 }}>Q: {q}</div>
          {stage.answers_summary?.[i] && (
            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>A: {stage.answers_summary[i]}</div>
          )}
        </div>
      ))}
      {stage.skipped_questions.map((q, i) => (
        <div key={`s-${i}`} style={{ marginBottom: 6, padding: "6px 10px", background: "var(--warning-soft)", borderRadius: "var(--radius-sm)", opacity: 0.7 }}>
          <span style={{ fontSize: "0.8rem", color: "var(--warning)" }}>⏭️ {q}</span>
        </div>
      ))}
    </div>
  );
}

export function ReportView() {
  const apiKey = useAppStore((s) => s.apiKey);
  const serverHasKey = useAppStore((s) => s.serverHasKey);
  const currentSessionId = useReportStore((s) => s.currentSessionId);
  const setCurrentSession = useReportStore((s) => s.setCurrentSession);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);

  // Use store's currentSessionId as initial selection (from interview → report)
  const activeSession = selectedSession || currentSessionId;

  // Session list (only when no active session set)
  const { data: sessionsData, isLoading: sessionsLoading } = useQuery({
    queryKey: ["report-sessions"],
    queryFn: () => listReportSessions("guest"),
    select: (res) => res.sessions,
    enabled: !activeSession,
  });

  // Session detail
  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ["report-detail", activeSession],
    queryFn: () => getSessionReport(activeSession!),
    enabled: !!activeSession,
  });

  // Auto-select first when in history view
  useEffect(() => {
    if (!activeSession && sessionsData && sessionsData.length > 0) {
      setSelectedSession(sessionsData[0].session_id);
    }
  }, [activeSession, sessionsData]);

  if (!apiKey && !serverHasKey) {
    return (
      <div className="empty-state" style={{ padding: "60px 20px" }}>
        <div style={{ fontSize: "2.5rem", opacity: 0.4 }}>🔑</div>
        <div>请先配置 API 密钥</div>
      </div>
    );
  }

  return (
    <div className="smooth-scroll" style={{ maxWidth: "var(--content-max-width)", margin: "0 auto", width: "100%", padding: "24px 16px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

        {/* Title */}
        <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--fg)", margin: 0 }}>
          📊 面试报告
        </h2>

        {sessionsLoading && <CardSkeleton lines={2} />}

        {/* No sessions */}
        {!sessionsLoading && (!sessionsData || sessionsData.length === 0) && (
          <div className="empty-state animate-fade-in" style={{ padding: "40px 20px" }}>
            <div style={{ fontSize: "2.5rem", opacity: 0.5 }}>📊</div>
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
              完成一次面试后，这里会生成专属报告
            </p>
          </div>
        )}

        {/* Session list + detail */}
        {sessionsData && sessionsData.length > 0 && (
          <div style={{ display: "flex", gap: 16, flexDirection: window.innerWidth < 768 ? "column" : "row" }}>

            {/* Session sidebar */}
            <div style={{ width: window.innerWidth < 768 ? "100%" : 220, flexShrink: 0 }}>
              <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: 8 }}>
                面试记录 ({sessionsData.length})
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {sessionsData.map((s: SessionReportItem) => (
                  <button
                    key={s.session_id}
                    onClick={() => setSelectedSession(s.session_id)}
                    className={`btn-ghost btn-sm ${selectedSession === s.session_id ? "active" : ""}`}
                    style={{
                      textAlign: "left", width: "100%", justifyContent: "flex-start",
                      background: selectedSession === s.session_id ? "var(--primary-soft)" : undefined,
                      color: selectedSession === s.session_id ? "var(--primary-text)" : undefined,
                    }}
                  >
                    <div style={{ overflow: "hidden" }}>
                      <div style={{ fontSize: "0.8rem", fontWeight: 500, whiteSpace: "nowrap", textOverflow: "ellipsis", overflow: "hidden" }}>
                        {s.topic}
                      </div>
                      <div style={{ fontSize: "0.68rem", color: "var(--text-dim)", marginTop: 1 }}>
                        {s.created_at?.slice(0, 10)}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Detail panel */}
            <div style={{ flex: 1, minWidth: 0 }}>
              {detailLoading && <CardSkeleton lines={4} />}

              {detail && !detailLoading && (
                <div className="animate-fade-in-up" style={{ display: "flex", flexDirection: "column", gap: 16 }}>

                  {/* Header */}
                  <div className="card-base" style={{ padding: 16 }}>
                    <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--fg)", marginBottom: 4 }}>
                      {detail.topic}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
                      {detail.created_at?.slice(0, 10)} · {detail.stats?.total_questions || 0} 题
                      {detail.stats?.skipped_count ? `（跳过 ${detail.stats.skipped_count} 题）` : ""}
                    </div>
                  </div>

                  {/* Stats */}
                  {detail.stats && (
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                      <div className="card-base" style={{ padding: "14px", textAlign: "center" }}>
                        <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--fg)" }}>{detail.stats.total_questions}</div>
                        <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: 2 }}>总题数</div>
                      </div>
                      <div className="card-base" style={{ padding: "14px", textAlign: "center" }}>
                        <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--primary)" }}>{detail.stats.answered_count}</div>
                        <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: 2 }}>已作答</div>
                      </div>
                      <div className="card-base" style={{ padding: "14px", textAlign: "center" }}>
                        <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--warning)" }}>{detail.stats.skipped_count}</div>
                        <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: 2 }}>已跳过</div>
                      </div>
                    </div>
                  )}

                  {/* Per-stage breakdown */}
                  {detail.stage_breakdown && detail.stage_breakdown.length > 0 && (
                    <div>
                      <div className="section-title">📋 各阶段记录</div>
                      {detail.stage_breakdown.map((s, i) => <StageCard key={i} stage={s} />)}
                    </div>
                  )}

                  {/* AI Summary */}
                  {detail.ai_summary && (
                    <div className="card-base" style={{ padding: "18px 20px" }}>
                      <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--primary-text)", marginBottom: 10 }}>
                        🤖 AI 总结报告
                      </div>
                      <MarkdownRenderer content={detail.ai_summary} />
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
