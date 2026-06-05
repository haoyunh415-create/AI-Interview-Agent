"use client";

import { create } from "zustand";

interface ReportData {
  stats: Record<string, unknown>;
  aiSummary: string | null;
}

interface ReportState {
  data: ReportData | null;
  loading: boolean;
  /** Session ID to show when switching from interview to report. */
  currentSessionId: string | null;
  setData: (data: ReportData | null) => void;
  setLoading: (loading: boolean) => void;
  setCurrentSession: (sessionId: string | null) => void;
  reset: () => void;
}

export const useReportStore = create<ReportState>((set) => ({
  data: null,
  loading: false,
  currentSessionId: null,
  setData: (data) => set({ data }),
  setLoading: (loading) => set({ loading }),
  setCurrentSession: (currentSessionId) => set({ currentSessionId }),
  reset: () => set({ data: null, loading: false, currentSessionId: null }),
}));
