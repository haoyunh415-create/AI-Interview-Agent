"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

/**
 * Stores an active chat session ID so subsequent messages don't need
 * to send the API key.  The session is persisted across page reloads
 * so a long chat isn't interrupted by a refresh.
 */
interface ChatSessionState {
  sessionId: string | null;
  provider: string | null;
  model: string | null;
  setSession: (sessionId: string, provider?: string | null, model?: string | null) => void;
  clearSession: () => void;
}

export const useChatSessionStore = create<ChatSessionState>()(
  persist(
    (set) => ({
      sessionId: null,
      provider: null,
      model: null,
      setSession: (sessionId, provider = null, model = null) =>
        set({ sessionId, provider, model }),
      clearSession: () => set({ sessionId: null, provider: null, model: null }),
    }),
    {
      name: "tech-chat-session",
      partialize: (state) => ({
        sessionId: state.sessionId,
        provider: state.provider,
        model: state.model,
      }),
    },
  ),
);
