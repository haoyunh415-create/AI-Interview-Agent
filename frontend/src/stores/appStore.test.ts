import { describe, it, expect, beforeEach } from "vitest";
import { useAppStore } from "./appStore";

describe("appStore", () => {
  beforeEach(() => {
    useAppStore.setState({ mode: "chat", apiKey: "", configOpen: false });
  });

  it("starts in chat mode with empty api key", () => {
    const s = useAppStore.getState();
    expect(s.mode).toBe("chat");
    expect(s.apiKey).toBe("");
    expect(s.configOpen).toBe(false);
  });

  it("setMode switches mode", () => {
    useAppStore.getState().setMode("interview");
    expect(useAppStore.getState().mode).toBe("interview");

    useAppStore.getState().setMode("bookmarks");
    expect(useAppStore.getState().mode).toBe("bookmarks");
  });

  it("setApiKey saves the key", () => {
    useAppStore.getState().setApiKey("sk-test-key");
    expect(useAppStore.getState().apiKey).toBe("sk-test-key");
  });

  it("setConfigOpen toggles settings panel", () => {
    useAppStore.getState().setConfigOpen(true);
    expect(useAppStore.getState().configOpen).toBe(true);

    useAppStore.getState().setConfigOpen(false);
    expect(useAppStore.getState().configOpen).toBe(false);
  });

  it("has default provider deepseek", () => {
    expect(useAppStore.getState().provider).toBe("deepseek");
    expect(useAppStore.getState().model).toBe("deepseek-chat");
  });

  it("setProvider changes provider and resets model", () => {
    useAppStore.getState().setProvider("openai");
    expect(useAppStore.getState().provider).toBe("openai");
    expect(useAppStore.getState().model).toBe("gpt-4o");
  });

  it("setModel allows custom model name", () => {
    useAppStore.getState().setModel("gpt-4-turbo");
    expect(useAppStore.getState().model).toBe("gpt-4-turbo");
  });

  it("login sets token and marks as logged in", () => {
    // Reset from localStorage side effects
    useAppStore.setState({ token: null, username: "guest", isLoggedIn: false });
    useAppStore.getState().login("jwt-token-abc", "testuser");
    const s = useAppStore.getState();
    expect(s.token).toBe("jwt-token-abc");
    expect(s.username).toBe("testuser");
    expect(s.isLoggedIn).toBe(true);
  });

  it("logout clears auth state", () => {
    useAppStore.setState({ token: "some-token", username: "user", isLoggedIn: true });
    useAppStore.getState().logout();
    const s = useAppStore.getState();
    expect(s.token).toBeNull();
    expect(s.username).toBe("guest");
    expect(s.isLoggedIn).toBe(false);
  });
});
