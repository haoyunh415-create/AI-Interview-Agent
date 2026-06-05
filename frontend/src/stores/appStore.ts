"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Mode = "chat" | "resume" | "interview" | "report" | "bookmarks";

const LLM_PROVIDERS = [
  { value: "deepseek", label: "DeepSeek" },
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "ollama", label: "Ollama (Local)" },
] as const;

const DEFAULT_MODELS: Record<string, string> = {
  deepseek: "deepseek-chat",
  openai: "gpt-4o",
  anthropic: "claude-sonnet-4-20250514",
  ollama: "llama3",
};

export type LlmProvider = (typeof LLM_PROVIDERS)[number]["value"];

interface AppState {
  mode: Mode;
  apiKey: string;
  provider: LlmProvider;
  model: string;
  configOpen: boolean;
  /** Server has an API key configured in .env — frontend doesn't need to send one. */
  serverHasKey: boolean;
  /** True after we've checked /api/config (prevents flash of API key banner). */
  configLoaded: boolean;
  // Auth
  token: string | null;
  username: string;
  isLoggedIn: boolean;
  setMode: (mode: Mode) => void;
  setApiKey: (key: string) => void;
  setProvider: (provider: LlmProvider) => void;
  setModel: (model: string) => void;
  setConfigOpen: (open: boolean) => void;
  setServerHasKey: (has: boolean) => void;
  setConfigLoaded: (loaded: boolean) => void;
  login: (token: string, username: string) => void;
  logout: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      mode: "chat",
      apiKey: "",
      provider: "deepseek" as LlmProvider,
      model: DEFAULT_MODELS.deepseek,
      configOpen: false,
      serverHasKey: false,
      configLoaded: false,
      token: null,
      username: "guest",
      isLoggedIn: false,
      setMode: (mode) => set({ mode }),
      setApiKey: (apiKey) => set({ apiKey }),
      setProvider: (provider) => set({ provider, model: DEFAULT_MODELS[provider] }),
      setModel: (model) => set({ model }),
      setConfigOpen: (configOpen) => set({ configOpen }),
      setServerHasKey: (serverHasKey) => set({ serverHasKey }),
      setConfigLoaded: (configLoaded) => set({ configLoaded }),
      login: (token, username) => {
        set({ token, username, isLoggedIn: true, apiKey: "" });
      },
      logout: () => {
        set({ token: null, username: "guest", isLoggedIn: false });
      },
    }),
    {
      name: "tech-chat-auth",  // localStorage key
      // Only persist auth fields — not transient UI state
      partialize: (state) => ({
        token: state.token,
        username: state.username,
        provider: state.provider,
        model: state.model,
        apiKey: state.apiKey,
      }),
    },
  ),
);

export { LLM_PROVIDERS, DEFAULT_MODELS };
