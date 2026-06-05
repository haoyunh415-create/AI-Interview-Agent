"use client";

import { useState, useCallback } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  startInterview,
  submitAnswerStream,
  getHint,
  listSessions,
  resumeInterview,
  createBookmark,
} from "@/lib/api";
import { useAppStore } from "@/stores/appStore";
import { useInterviewStore } from "@/stores/interviewStore";
import { useResumeStore } from "@/stores/resumeStore";
import { useTranslation } from "@/i18n";
import { InterviewSetup } from "./InterviewSetup";
import { InterviewSession } from "./InterviewSession";
import { InterviewCompleted } from "./InterviewCompleted";

export function InterviewView() {
  const apiKey = useAppStore((s) => s.apiKey);
  const serverHasKey = useAppStore((s) => s.serverHasKey);
  const provider = useAppStore((s) => s.provider);
  const model = useAppStore((s) => s.model);
  const setMode = useAppStore((s) => s.setMode);
  const resumeText = useResumeStore((s) => s.text);

  const interview = useInterviewStore((s) => s.interview);
  const completed = useInterviewStore((s) => s.completed);
  const topic = useInterviewStore((s) => s.topic);
  const timerEnabled = useInterviewStore((s) => s.timerEnabled);
  const history = useInterviewStore((s) => s.history);
  const setInterview = useInterviewStore((s) => s.setInterview);
  const addHistoryItem = useInterviewStore((s) => s.addHistoryItem);
  const setScore = useInterviewStore((s) => s.setScore);
  const setStreaming = useInterviewStore((s) => s.setStreaming);
  const setStreamingScore = useInterviewStore((s) => s.setStreamingScore);
  const appendStreamingScore = useInterviewStore((s) => s.appendStreamingScore);
  const setCompleted = useInterviewStore((s) => s.setCompleted);
  const setTopic = useInterviewStore((s) => s.setTopic);
  const setHint = useInterviewStore((s) => s.setHint);
  const setTimerEnabled = useInterviewStore((s) => s.setTimerEnabled);
  const incrementTimerKey = useInterviewStore((s) => s.incrementTimerKey);
  const resetInterview = useInterviewStore((s) => s.reset);

  const [customTopic, setCustomTopic] = useState("");

  const { t } = useTranslation();

  // ── Session resume query ──
  const { data: sessionsData } = useQuery({
    queryKey: ["sessions"],
    queryFn: () => listSessions("guest"),
    enabled: !interview && !completed && (!!apiKey || serverHasKey),
    refetchInterval: 30_000,
  });
  const availableSessions =
    sessionsData?.sessions?.filter((s: { question_count: number }) => s.question_count > 0) || [];

  // ── Start mutation ──
  const startMutation = useMutation({
    mutationFn: (topicText: string) =>
      startInterview({
        api_key: apiKey,
        topic: topicText,
        resume_text: resumeText,
        provider,
        model,
      }),
    onSuccess: (res) => {
      setInterview(res);
      incrementTimerKey();
      toast.success(t("interview.start"));
    },
    onError: (e: Error) => {
      toast.error(`启动失败: ${e.message}`);
    },
  });

  // ── Resume mutation ──
  const resumeMutation = useMutation({
    mutationFn: (sessionId: number) =>
      resumeInterview({
        api_key: apiKey,
        session_id: sessionId,
        resume_text: resumeText,
      }),
    onSuccess: (res) => {
      setInterview({
        session_id: res.session_id,
        question: res.question || "",
        stage: res.stage,
        stage_index: res.stage_index,
        total_stages: res.total_stages,
        is_followup: false,
      });
      incrementTimerKey();
      toast.success("已恢复面试");
    },
    onError: (e: Error) => {
      toast.error(`恢复失败: ${e.message}`);
    },
  });

  // ── Submit mutation ──
  const submitMutation = useMutation({
    mutationFn: async (answer: string) => {
      const currentQuestion = interview?.question || "";
      await submitAnswerStream(
        interview!.session_id,
        answer,
        // onToken
        (chunk) => appendStreamingScore(chunk),
        // onDone
        (result) => {
          setStreaming(false);
          addHistoryItem({
            q: currentQuestion,
            a: answer,
            score: result.score_text || "",
          });
          setScore(result.score_text || "");
          if (result.completed) {
            setCompleted(true);
            setInterview(null);
            toast.success(t("interview.completed"));
          } else if (result.next_question) {
            setInterview({
              ...interview!,
              question: result.next_question as string,
              is_followup: result.is_followup || false,
              stage_index: result.stage_index || 0,
            });
            incrementTimerKey();
          }
        },
        // onError
        (err) => {
          setStreaming(false);
          toast.error(`提交失败: ${err.message}`);
        },
      );
    },
    onError: (e: Error) => {
      setStreaming(false);
      toast.error(`提交失败: ${e.message}`);
    },
  });

  // ── Hint mutation ──
  const hintMutation = useMutation({
    mutationFn: () => getHint({ session_id: interview!.session_id }),
    onSuccess: (res) => setHint(res.hint),
    onError: () => toast.error("获取提示失败"),
  });

  // ── Bookmark mutations ──
  const bookmarkMutation = useMutation({
    mutationFn: (data: { question: string; answer?: string }) =>
      createBookmark({
        question: data.question,
        answer: data.answer || "",
        topic: topic,
        stage: interview?.stage || "",
      }),
    onSuccess: () => toast.success(t("bookmarks.saved")),
    onError: () => toast.error("收藏失败"),
  });

  const [bookmarkedSet, setBookmarkedSet] = useState<Set<string>>(new Set());

  const batchBookmarkMutation = useMutation({
    mutationFn: async (items: Array<{ q: string; a: string }>) => {
      const newItems = items.filter((h) => !bookmarkedSet.has(h.q));
      if (newItems.length === 0) return 0;
      let count = 0;
      for (const h of newItems) {
        try {
          await createBookmark({
            question: h.q,
            answer: h.a || "",
            topic: topic || "",
            stage: interview?.stage || "",
          });
          count++;
        } catch { /* skip duplicates */ }
      }
      return count;
    },
    onSuccess: (count) => {
      if (count === 0) {
        toast.success("已全部收藏");
        return;
      }
      toast.success(`已收藏 ${count} 题`);
      setBookmarkedSet((prev) => {
        const next = new Set(prev);
        history.forEach((h) => next.add(h.q));
        return next;
      });
    },
    onError: () => toast.error("批量收藏失败"),
  });

  // ── Shared handlers ──
  const handleStart = useCallback(() => {
    if (!apiKey && !serverHasKey) return;
    resetInterview();
    const topicText = topic === "自定义" ? customTopic : topic;
    startMutation.mutate(topicText || "Transformer 核心");
  }, [apiKey, serverHasKey, topic, customTopic, startMutation, resetInterview]);

  // ── Routing ──
  if (!interview && !completed) {
    return (
      <InterviewSetup
        apiKey={apiKey}
        serverHasKey={serverHasKey}
        topic={topic}
        customTopic={customTopic}
        timerEnabled={timerEnabled}
        availableSessions={availableSessions}
        startMutation={startMutation}
        resumeMutation={resumeMutation}
        onTopicChange={setTopic}
        onCustomTopicChange={setCustomTopic}
        onTimerToggle={setTimerEnabled}
        onStart={handleStart}
      />
    );
  }

  if (completed) {
    return (
      <InterviewCompleted
        startMutation={startMutation}
        bookmarkMutation={bookmarkMutation}
        batchBookmarkMutation={batchBookmarkMutation}
      />
    );
  }

  return <InterviewSession submitMutation={submitMutation} hintMutation={hintMutation} />;
}
