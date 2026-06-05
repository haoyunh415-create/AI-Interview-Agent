"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import type { UseMutationResult } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { useInterviewStore } from "@/stores/interviewStore";
import { useTranslation } from "@/i18n";
import { ProgressBar } from "@/components/ui/progress-bar";
import { MarkdownRenderer } from "@/components/ui/markdown";
import { ScoreBadge, ScoreMeter } from "@/components/ui/score-display";
import { InterviewTimer, TimerDisplay } from "@/components/ui/timer";
import { createBookmark } from "@/lib/api";

const DEFAULT_TIMER = 120;

interface InterviewSessionProps {
  submitMutation: UseMutationResult<any, any, any, any>;
  hintMutation: UseMutationResult<any, any, any, any>;
}

export function InterviewSession({
  submitMutation,
  hintMutation,
}: InterviewSessionProps) {
  const { t } = useTranslation();

  const interview = useInterviewStore((s) => s.interview);
  const history = useInterviewStore((s) => s.history);
  const answerInput = useInterviewStore((s) => s.answerInput);
  const score = useInterviewStore((s) => s.score);
  const streamingScore = useInterviewStore((s) => s.streamingScore);
  const streaming = useInterviewStore((s) => s.streaming);
  const hint = useInterviewStore((s) => s.hint);
  const timerEnabled = useInterviewStore((s) => s.timerEnabled);
  const timerRemaining = useInterviewStore((s) => s.timerRemaining);
  const timerKey = useInterviewStore((s) => s.timerKey);
  const completed = useInterviewStore((s) => s.completed);
  const setAnswerInput = useInterviewStore((s) => s.setAnswerInput);
  const setTimerRemaining = useInterviewStore((s) => s.setTimerRemaining);
  const incrementTimerKey = useInterviewStore((s) => s.incrementTimerKey);
  const setCompleted = useInterviewStore((s) => s.setCompleted);
  const setInterview = useInterviewStore((s) => s.setInterview);
  const setScore = useInterviewStore((s) => s.setScore);
  const addHistoryItem = useInterviewStore((s) => s.addHistoryItem);
  const appendStreamingScore = useInterviewStore((s) => s.appendStreamingScore);
  const setStreaming = useInterviewStore((s) => s.setStreaming);
  const setStreamingScore = useInterviewStore((s) => s.setStreamingScore);
  const resetInterview = useInterviewStore((s) => s.reset);
  const storeTopic = useInterviewStore((s) => s.topic);

  const [submitError, setSubmitError] = useState<string | null>(null);
  const [pendingAnswer, setPendingAnswer] = useState<string>("");
  const [showPreview, setShowPreview] = useState(false);
  const [bookmarkedSet, setBookmarkedSet] = useState<Set<string>>(new Set());
  const submitBtnRef = useRef<HTMLButtonElement>(null);
  const lastSavedRef = useRef("");

  // ── Bookmark mutation ──
  const bookmarkMutation = useMutation({
    mutationFn: (data: { question: string; answer?: string }) =>
      createBookmark({
        question: data.question,
        answer: data.answer || "",
        topic: storeTopic,
        stage: interview?.stage || "",
      }),
    onSuccess: () => toast.success(t("bookmarks.saved")),
    onError: () => toast.error("收藏失败"),
  });

  // ── Auto-save draft to localStorage ──
  useEffect(() => {
    const draftKey = interview
      ? `draft_${interview.session_id}_${interview.question?.slice(0, 40)}`
      : null;

    // Restore draft on mount or question change
    if (draftKey) {
      try {
        const saved = localStorage.getItem(draftKey);
        if (saved && saved !== answerInput) {
          setAnswerInput(saved);
        }
      } catch { /* ignore */ }
    }

    const interval = setInterval(() => {
      if (!draftKey || !answerInput.trim()) return;
      if (answerInput === lastSavedRef.current) return;
      try {
        localStorage.setItem(draftKey, answerInput);
        lastSavedRef.current = answerInput;
      } catch { /* ignore */ }
    }, 2000);

    return () => {
      clearInterval(interval);
      if (draftKey && !answerInput.trim()) {
        try { localStorage.removeItem(draftKey); } catch { /* ignore */ }
      }
    };
  }, [interview?.session_id, interview?.question]);

  const clearDraft = useCallback(() => {
    if (!interview) return;
    const draftKey = `draft_${interview.session_id}_${interview.question?.slice(0, 40)}`;
    try { localStorage.removeItem(draftKey); } catch { /* ignore */ }
    lastSavedRef.current = "";
  }, [interview]);

  const handleSubmitAction = useCallback(() => {
    const ans = answerInput.trim();
    if (!interview || !ans || submitMutation.isPending) return;
    setAnswerInput("");
    setSubmitError(null);
    setPendingAnswer(ans);
    setStreaming(true);
    setStreamingScore("");
    clearDraft();
    submitMutation.mutate(ans);
  }, [interview, answerInput, submitMutation, setAnswerInput, clearDraft, setStreaming, setStreamingScore]);

  const handleTimerExpire = useCallback(() => {
    const text = answerInput.trim();
    if (text) {
      setAnswerInput("");
      setStreaming(true);
      setStreamingScore("");
      submitMutation.mutate(text);
    } else {
      toast("⏱️ 时间到！", { icon: "⏰" });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [answerInput, submitMutation, setAnswerInput, setStreaming, setStreamingScore]);

  const handleTimerTick = useCallback((remaining: number) => {
    setTimerRemaining(remaining);
  }, [setTimerRemaining]);

  const handleExit = useCallback(() => {
    resetInterview();
    toast.success("已退出面试，会话已保留可恢复");
  }, [resetInterview]);

  const handleRetry = useCallback(() => {
    if (!pendingAnswer) return;
    setSubmitError(null);
    setAnswerInput(pendingAnswer);
    setStreamingScore("");
  }, [pendingAnswer, setAnswerInput, setStreamingScore]);

  if (!interview) return null;

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
      {/* Timer background (runs regardless of UI) */}
      {timerEnabled && (
        <InterviewTimer
          key={timerKey}
          duration={DEFAULT_TIMER}
          running={!!interview && !submitMutation.isPending}
          onExpire={handleTimerExpire}
          onTick={handleTimerTick}
        />
      )}

      {/* Progress + Timer row */}
      <div
        className="animate-fade-in-up"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          padding: "4px 0",
        }}
      >
        <div style={{ flex: 1 }}>
          <ProgressBar
            current={interview.stage_index + 1}
            total={interview.total_stages}
            label={t("interview.progress")}
          />
        </div>
        {timerEnabled && (
          <TimerDisplay
            remaining={timerRemaining}
            duration={DEFAULT_TIMER}
          />
        )}
      </div>

      {/* Exit button row */}
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 4 }}>
        <button
          onClick={handleExit}
          className="btn-ghost"
          style={{
            padding: "4px 10px", fontSize: "0.72rem",
            color: "var(--text-muted)", borderColor: "transparent",
          }}
        >
          ✕ 退出面试
        </button>
      </div>

      {/* Question card */}
      <div
        className="animate-slide-in-up"
        style={{
          background: "var(--card)",
          borderRadius: "var(--radius-lg)",
          padding: "20px 24px",
          border: "1px solid var(--primary)",
          borderLeft: "3px solid var(--primary)",
          boxShadow: "0 0 20px var(--primary-glow)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
          <span className="tag tag-primary" style={{ fontSize: "0.7rem", padding: "2px 8px" }}>
            {interview.is_followup ? t("interview.followup") : t("interview.question")}
          </span>
          <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
            {t("interview.stage", { current: interview.stage_index + 1, total: interview.total_stages })}
          </span>
          <button
            onClick={() =>
              bookmarkMutation.mutate({
                question: interview.question,
                answer: answerInput.trim() || undefined,
              })
            }
            disabled={bookmarkMutation.isPending}
            className="btn-ghost"
            style={{
              marginLeft: "auto",
              padding: "2px 8px",
              fontSize: "0.72rem",
              color: "var(--warning)",
              borderColor: "var(--warning-soft)",
            }}
            title="收藏本题"
          >
            ⭐ 收藏
          </button>
        </div>
        <div style={{ fontSize: "1rem", lineHeight: 1.8, color: "var(--fg)", fontWeight: 450 }}>
          {interview.question}
        </div>
      </div>

      {/* Hint */}
      {hint && (
        <div className="animate-fade-in-up card-base" style={{ padding: "14px 18px", borderLeft: "3px solid var(--warning)" }}>
          <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--warning)", marginBottom: 6 }}>
            💡 {t("interview.hint")}
          </div>
          <div style={{ fontSize: "0.88rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
            {hint}
          </div>
        </div>
      )}

      {/* Score — streaming while evaluating */}
      {streaming && streamingScore && (
        <div className="card-score animate-fade-in" style={{ padding: "14px 18px" }}>
          <div style={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--primary-text)", marginBottom: 6 }}>
            {t("interview.score")}...
          </div>
          <div style={{ fontSize: "0.85rem", lineHeight: 1.6, color: "var(--text-secondary)", whiteSpace: "pre-wrap" }}>
            {streamingScore}
          </div>
        </div>
      )}
      {score && !streaming && (
        <div className="card-score" style={{ padding: "14px 18px" }}>
          <ScoreMeter scoreText={score} />
          <div style={{ marginTop: 10, display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button
              onClick={() =>
                bookmarkMutation.mutate({
                  question: interview.question,
                  answer: history.length > 0 ? history[history.length - 1].a : "",
                })
              }
              disabled={bookmarkMutation.isPending}
              className="btn-ghost"
              style={{
                padding: "6px 14px", fontSize: "0.78rem",
                color: "var(--warning)", borderColor: "var(--warning-soft)",
              }}
            >
              ⭐ 收藏本题及答案
            </button>
          </div>
        </div>
      )}

      {/* Answer input */}
      <div className="animate-fade-in">
        {/* Toolbar */}
        <div
          style={{
            display: "flex",
            gap: 4,
            marginBottom: 6,
            flexWrap: "wrap",
            alignItems: "center",
          }}
        >
          <button
            onClick={() => {
              // Find the textarea to manipulate selection
              const ta = document.querySelector<HTMLTextAreaElement>(
                `[data-answer-textarea="${interview.session_id}"]`
              );
              if (!ta) return;
              const start = ta.selectionStart;
              const end = ta.selectionEnd;
              const text = ta.value;
              const newText = text.slice(0, start) + "```\n" + text.slice(start, end) + "\n```" + text.slice(end);
              setAnswerInput(newText);
              setTimeout(() => { ta.selectionStart = start + 4; ta.selectionEnd = start + 4 + (end - start); ta.focus(); }, 0);
            }}
            className="btn-ghost"
            style={{ padding: "4px 10px", fontSize: "0.75rem" }}
            title="插入代码块"
          >
            {'</>'}
          </button>
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="btn-ghost"
            style={{
              padding: "4px 10px",
              fontSize: "0.75rem",
              background: showPreview ? "var(--primary-soft)" : undefined,
              color: showPreview ? "var(--primary-text)" : undefined,
            }}
          >
            {showPreview ? "✏️ 编辑" : "👁️ 预览"}
          </button>
          <span style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginLeft: "auto" }}>
            Markdown + Ctrl+Enter 提交
          </span>
        </div>

        {showPreview ? (
          <div
            className="card-base"
            style={{
              padding: "14px 18px",
              minHeight: 120,
              fontSize: "0.9rem",
              lineHeight: 1.7,
              color: "var(--fg)",
            }}
          >
            {answerInput.trim() ? (
              <MarkdownRenderer content={answerInput} />
            ) : (
              <span style={{ color: "var(--text-dim)" }}>暂无内容</span>
            )}
          </div>
        ) : (
          <textarea
            data-answer-textarea={interview.session_id}
            value={answerInput}
            onChange={(e) => setAnswerInput(e.target.value)}
            placeholder={t("interview.answer_placeholder")}
            rows={4}
            className="input-base"
            style={{
              width: "100%",
              padding: "14px 18px",
              borderRadius: "var(--radius-lg)",
              lineHeight: 1.6,
              resize: "vertical",
              fontSize: "0.9rem",
            }}
            onKeyDown={(e) => {
              if ((e.key === "Enter" && e.ctrlKey) || (e.key === "Enter" && !e.shiftKey)) {
                e.preventDefault();
                handleSubmitAction();
              }
            }}
          />
        )}
        <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
          <button
            ref={submitBtnRef}
            onClick={handleSubmitAction}
            disabled={submitMutation.isPending || !answerInput.trim()}
            className="btn-primary"
            style={{ flex: 1 }}
          >
            {submitMutation.isPending ? t("interview.submitting") : t("interview.submit")}
          </button>
          <button
            onClick={() => hintMutation.mutate(undefined as any)}
            disabled={hintMutation.isPending}
            className="btn-ghost"
          >
            💡 {t("interview.hint")}
          </button>
        </div>
        {timerEnabled && (
          <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", marginTop: 6, textAlign: "right" }}>
            ⏱️ {t("interview.timer_auto_submit")}
          </div>
        )}
      </div>

      {/* Error banner + retry */}
      {submitError && !streaming && (
        <div className="animate-fade-in" style={{
          padding: "12px 16px",
          background: "var(--danger-soft)",
          border: "1px solid rgba(239, 68, 68, 0.3)",
          borderRadius: "var(--radius-md)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          flexWrap: "wrap",
        }}>
          <span style={{ fontSize: "0.85rem", color: "var(--danger)" }}>
            ⚠️ 提交失败: {submitError}
          </span>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={handleRetry}
              className="btn-ghost"
              style={{ padding: "6px 14px", fontSize: "0.78rem", borderColor: "var(--danger)" }}
            >
              重试
            </button>
          </div>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className="card-base animate-fade-in" style={{ padding: 16 }}>
          <div style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: 10 }}>
            {t("interview.answered", { count: history.length })}
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
                  width: 22,
                  height: 22,
                  borderRadius: "50%",
                  background: "var(--card-hover)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "0.65rem",
                  fontWeight: 600,
                  color: "var(--text-muted)",
                  flexShrink: 0,
                }}
              >
                {i + 1}
              </span>
              <span
                style={{
                  color: "var(--text-secondary)",
                  flex: 1,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
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
                  padding: "3px 10px",
                  fontSize: "0.72rem",
                  color: bookmarkedSet.has(h.q) ? "var(--warning)" : "var(--text-dim)",
                  borderColor: "transparent",
                  flexShrink: 0,
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
