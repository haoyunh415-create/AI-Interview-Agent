"use client";

import { create } from "zustand";
import type { ResumeProfile } from "@/lib/api";

interface ResumeState {
  text: string;
  profile: ResumeProfile | null;
  loading: boolean;
  setText: (text: string) => void;
  setProfile: (profile: ResumeProfile | null) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

export const useResumeStore = create<ResumeState>((set) => ({
  text: "",
  profile: null,
  loading: false,
  setText: (text) => set({ text }),
  setProfile: (profile) => set({ profile }),
  setLoading: (loading) => set({ loading }),
  reset: () => set({ text: "", profile: null, loading: false }),
}));
