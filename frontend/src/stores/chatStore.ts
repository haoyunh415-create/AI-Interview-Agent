"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

/** Generate a unique session ID. */
function uid(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

const TITLE_TRUNCATE = 36;

interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  input: string;
  loading: boolean;
  streamingContent: string;

  // Session management
  createSession: (firstMessage?: string) => string;
  deleteSession: (id: string) => void;
  switchSession: (id: string) => void;
  renameSession: (id: string, title: string) => void;

  // Message actions (operate on active session)
  addMessage: (msg: ChatMessage) => void;
  appendToLastMessage: (chunk: string) => void;
  popLastMessage: () => void;
  clearMessages: () => void;

  // UI state
  setInput: (input: string) => void;
  setLoading: (loading: boolean) => void;
}

function makeSession(firstMessage?: string): ChatSession {
  const now = Date.now();
  return {
    id: uid(),
    title: firstMessage
      ? firstMessage.slice(0, TITLE_TRUNCATE) + (firstMessage.length > TITLE_TRUNCATE ? "…" : "")
      : "新对话",
    messages: [],
    createdAt: now,
    updatedAt: now,
  };
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      sessions: [],
      activeSessionId: null,
      input: "",
      loading: false,
      streamingContent: "",

      /* ── Session management ── */

      createSession: (firstMessage?: string) => {
        const session = makeSession(firstMessage);
        set((state) => ({
          sessions: [...state.sessions, session],
          activeSessionId: session.id,
          input: "",
          streamingContent: "",
        }));
        return session.id;
      },

      deleteSession: (id: string) => {
        const { sessions, activeSessionId } = get();
        const remaining = sessions.filter((s) => s.id !== id);
        // If we deleted the active session, switch to the most recent one (or create one)
        let nextActive = activeSessionId === id ? null : activeSessionId;
        if (!nextActive && remaining.length > 0) {
          nextActive = remaining[remaining.length - 1].id;
        }
        set({
          sessions: remaining,
          activeSessionId: nextActive,
          input: "",
          streamingContent: "",
        });
        // If no sessions left, create a fresh one
        if (remaining.length === 0) {
          get().createSession();
        }
      },

      switchSession: (id: string) => {
        set({ activeSessionId: id, input: "", streamingContent: "" });
      },

      renameSession: (id: string, title: string) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === id ? { ...s, title: title.trim() || "新对话" } : s,
          ),
        }));
      },

      /* ── Message actions ── */

      addMessage: (msg: ChatMessage) => {
        const { sessions, activeSessionId } = get();
        if (!activeSessionId) return;
        set((state) => ({
          sessions: state.sessions.map((s) => {
            if (s.id !== activeSessionId) return s;
            const updated = {
              ...s,
              messages: [...s.messages, msg],
              updatedAt: Date.now(),
            };
            // Auto-title from first user message
            if (msg.role === "user" && s.title === "新对话" && s.messages.length === 0) {
              const title = msg.content
                .replace(/\[.*?\]/g, "")   // strip markdown links / image tags
                .replace(/\n/g, " ")
                .trim()
                .slice(0, TITLE_TRUNCATE);
              updated.title = title + (title.length >= TITLE_TRUNCATE ? "…" : "");
            }
            return updated;
          }),
          streamingContent: "",
        }));
      },

      appendToLastMessage: (chunk: string) => {
        const { sessions, activeSessionId } = get();
        if (!activeSessionId) return;
        set((state) => ({
          sessions: state.sessions.map((s) => {
            if (s.id !== activeSessionId) return s;
            const msgs = [...s.messages];
            if (msgs.length === 0) {
              msgs.push({ role: "assistant", content: chunk });
            } else {
              const last = msgs[msgs.length - 1];
              if (last.role === "assistant") {
                msgs[msgs.length - 1] = { ...last, content: last.content + chunk };
              } else {
                msgs.push({ role: "assistant", content: chunk });
              }
            }
            return { ...s, messages: msgs, updatedAt: Date.now() };
          }),
          streamingContent: (get().streamingContent + chunk).slice(-200),
        }));
      },

      popLastMessage: () => {
        const { sessions, activeSessionId } = get();
        if (!activeSessionId) return;
        set((state) => ({
          sessions: state.sessions.map((s) => {
            if (s.id !== activeSessionId) return s;
            return { ...s, messages: s.messages.slice(0, -1), updatedAt: Date.now() };
          }),
        }));
      },

      clearMessages: () => {
        const { sessions, activeSessionId } = get();
        if (!activeSessionId) return;
        set((state) => ({
          sessions: state.sessions.map((s) => {
            if (s.id !== activeSessionId) return s;
            return { ...s, messages: [], updatedAt: Date.now() };
          }),
          input: "",
          streamingContent: "",
        }));
      },

      /* ── UI state ── */

      setInput: (input) => set({ input }),
      setLoading: (loading) => set({ loading }),
    }),
    {
      name: "tech-chat-sessions",
      partialize: (state) => ({
        sessions: state.sessions,
        activeSessionId: state.activeSessionId,
      }),
      // On rehydrate, ensure at least one session exists
      onRehydrateStorage: () => (state) => {
        if (state && state.sessions.length === 0) {
          const session = makeSession();
          state.sessions = [session];
          state.activeSessionId = session.id;
        }
      },
    },
  ),
);

/** Convenience: get the active session's messages. */
export function useActiveMessages(): ChatMessage[] {
  const sessions = useChatStore((s) => s.sessions);
  const activeId = useChatStore((s) => s.activeSessionId);
  const session = sessions.find((s) => s.id === activeId);
  return session?.messages ?? [];
}

/** Convenience: get the active session. */
export function useActiveSession(): ChatSession | null {
  const sessions = useChatStore((s) => s.sessions);
  const activeId = useChatStore((s) => s.activeSessionId);
  return sessions.find((s) => s.id === activeId) ?? null;
}
