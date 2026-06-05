import { describe, it, expect, beforeEach } from "vitest";
import { useChatStore } from "./chatStore";

describe("chatStore", () => {
  beforeEach(() => {
    // Reset the store: clear sessions and create a fresh default session
    const { createSession } = useChatStore.getState();
    useChatStore.setState({ sessions: [], activeSessionId: null, input: "", loading: false });
    createSession(); // creates and sets activeSessionId
  });

  it("starts with a default session", () => {
    const s = useChatStore.getState();
    expect(s.sessions).toHaveLength(1);
    expect(s.activeSessionId).toBe(s.sessions[0].id);
    expect(s.input).toBe("");
    expect(s.loading).toBe(false);
  });

  it("addMessage appends to active session", () => {
    useChatStore.getState().addMessage({ role: "user", content: "hello" });
    const msgs = useChatStore.getState().sessions.find(
      (s) => s.id === useChatStore.getState().activeSessionId,
    )?.messages;
    expect(msgs).toHaveLength(1);
    expect(msgs![0]).toEqual({ role: "user", content: "hello" });
  });

  it("addMessage preserves existing messages", () => {
    useChatStore.getState().addMessage({ role: "user", content: "q1" });
    useChatStore.getState().addMessage({ role: "assistant", content: "a1" });
    const msgs = useChatStore.getState().sessions.find(
      (s) => s.id === useChatStore.getState().activeSessionId,
    )?.messages;
    expect(msgs).toHaveLength(2);
  });

  it("setInput updates input text", () => {
    useChatStore.getState().setInput("What is AI?");
    expect(useChatStore.getState().input).toBe("What is AI?");
  });

  it("setLoading toggles loading state", () => {
    useChatStore.getState().setLoading(true);
    expect(useChatStore.getState().loading).toBe(true);
  });

  it("clearMessages resets messages in active session", () => {
    useChatStore.getState().addMessage({ role: "user", content: "hi" });
    useChatStore.getState().setInput("typing");
    useChatStore.getState().clearMessages();
    const msgs = useChatStore.getState().sessions.find(
      (s) => s.id === useChatStore.getState().activeSessionId,
    )?.messages;
    expect(msgs).toHaveLength(0);
    expect(useChatStore.getState().input).toBe("");
  });

  it("createSession adds a new session and switches to it", () => {
    const origId = useChatStore.getState().activeSessionId;
    const newId = useChatStore.getState().createSession();
    const s = useChatStore.getState();
    expect(s.sessions).toHaveLength(2);
    expect(s.activeSessionId).toBe(newId);
    expect(newId).not.toBe(origId);
  });

  it("deleteSession removes session and switches to another", () => {
    useChatStore.getState().createSession();
    useChatStore.getState().createSession();
    expect(useChatStore.getState().sessions).toHaveLength(3);
    const idToDelete = useChatStore.getState().sessions[1].id;
    useChatStore.getState().deleteSession(idToDelete);
    expect(useChatStore.getState().sessions).toHaveLength(2);
    expect(useChatStore.getState().activeSessionId).toBeTruthy();
  });

  it("deleteSession of the only session creates a new default one", () => {
    const id = useChatStore.getState().activeSessionId!;
    useChatStore.getState().deleteSession(id);
    // Should have auto-created a fresh session
    expect(useChatStore.getState().sessions).toHaveLength(1);
    expect(useChatStore.getState().activeSessionId).not.toBe(id);
  });

  it("switchSession changes active session", () => {
    const origId = useChatStore.getState().activeSessionId!;
    const newId = useChatStore.getState().createSession();
    useChatStore.getState().switchSession(origId);
    expect(useChatStore.getState().activeSessionId).toBe(origId);
    useChatStore.getState().switchSession(newId);
    expect(useChatStore.getState().activeSessionId).toBe(newId);
  });

  it("auto-titles sessions from first user message", () => {
    useChatStore.getState().addMessage({ role: "user", content: "What is a transformer model?" });
    const s = useChatStore.getState().sessions.find(
      (s) => s.id === useChatStore.getState().activeSessionId,
    );
    expect(s!.title).toContain("What is a transformer");
  });

  it("messages are isolated between sessions", () => {
    // First session: add a message
    useChatStore.getState().addMessage({ role: "user", content: "msg in session 1" });

    // Create second session
    useChatStore.getState().createSession();

    // Second session should have empty messages
    const s2 = useChatStore.getState().sessions.find(
      (s) => s.id === useChatStore.getState().activeSessionId,
    );
    expect(s2!.messages).toHaveLength(0);

    // Switch back to first session — messages should still be there
    const s1 = useChatStore.getState().sessions[0];
    useChatStore.getState().switchSession(s1.id);
    expect(useChatStore.getState().activeSessionId).toBe(s1.id);
    expect(s1.messages).toHaveLength(1);
  });
});
