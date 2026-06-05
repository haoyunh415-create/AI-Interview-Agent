"use client";

import { create } from "zustand";
import type { StartInterviewResponse } from "@/lib/api";

interface HistoryItem {
  q: string;
  a: string;
  score?: string;
}

interface InterviewState {
  interview: StartInterviewResponse | null;
  history: HistoryItem[];
  answerInput: string;
  loading: boolean;
  score: string;
  streamingScore: string;
  streaming: boolean;
  hint: string;
  completed: boolean;
  topic: string;
  // Timer state (shared across sub-views)
  timerEnabled: boolean;
  timerRemaining: number;
  timerKey: number;
  setInterview: (interview: StartInterviewResponse | null) => void;
  setHistory: (history: HistoryItem[]) => void;
  addHistoryItem: (item: HistoryItem) => void;
  setAnswerInput: (input: string) => void;
  setLoading: (loading: boolean) => void;
  setScore: (score: string) => void;
  setStreamingScore: (score: string) => void;
  appendStreamingScore: (chunk: string) => void;
  setStreaming: (streaming: boolean) => void;
  setHint: (hint: string) => void;
  setCompleted: (completed: boolean) => void;
  setTopic: (topic: string) => void;
  setTimerEnabled: (enabled: boolean) => void;
  setTimerRemaining: (remaining: number) => void;
  incrementTimerKey: () => void;
  reset: () => void;
}

export const useInterviewStore = create<InterviewState>((set) => ({
  interview: null,
  history: [],
  answerInput: "",
  loading: false,
  score: "",
  streamingScore: "",
  streaming: false,
  hint: "",
  completed: false,
  topic: "Transformer 核心",
  timerEnabled: true,
  timerRemaining: 120,
  timerKey: 0,
  setInterview: (interview) => set({ interview }),
  setHistory: (history) => set({ history }),
  addHistoryItem: (item) =>
    set((state) => ({ history: [...state.history, item] })),
  setAnswerInput: (input) => set({ answerInput: input }),
  setLoading: (loading) => set({ loading }),
  setScore: (score) => set({ score }),
  setStreamingScore: (score) => set({ streamingScore: score }),
  appendStreamingScore: (chunk) =>
    set((state) => ({ streamingScore: state.streamingScore + chunk })),
  setStreaming: (streaming) => set({ streaming }),
  setHint: (hint) => set({ hint }),
  setCompleted: (completed) => set({ completed }),
  setTopic: (topic) => set({ topic }),
  setTimerEnabled: (enabled) => set({ timerEnabled: enabled }),
  setTimerRemaining: (remaining) => set({ timerRemaining: remaining }),
  incrementTimerKey: () =>
    set((state) => ({ timerKey: state.timerKey + 1 })),
  reset: () =>
    set({
      interview: null,
      history: [],
      answerInput: "",
      loading: false,
      score: "",
      streamingScore: "",
      streaming: false,
      hint: "",
      completed: false,
      timerEnabled: true,
      timerRemaining: 120,
      timerKey: 0,
    }),
}));
