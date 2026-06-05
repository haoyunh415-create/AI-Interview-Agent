import { describe, it, expect, beforeEach } from "vitest";
import { useInterviewStore } from "./interviewStore";

const mockInterview = {
  session_id: "sess-1",
  question: "What is Transformer?",
  stage: "基础",
  stage_index: 0,
  total_stages: 5,
  is_followup: false,
};

describe("interviewStore", () => {
  beforeEach(() => {
    useInterviewStore.setState({
      interview: null,
      history: [],
      answerInput: "",
      loading: false,
      score: "",
      hint: "",
      completed: false,
      topic: "Transformer 核心",
    });
  });

  it("starts with default state", () => {
    const s = useInterviewStore.getState();
    expect(s.interview).toBeNull();
    expect(s.history).toHaveLength(0);
    expect(s.completed).toBe(false);
    expect(s.topic).toBe("Transformer 核心");
  });

  it("setInterview sets active interview", () => {
    useInterviewStore.getState().setInterview(mockInterview);
    expect(useInterviewStore.getState().interview).toEqual(mockInterview);
  });

  it("addHistoryItem appends to history", () => {
    useInterviewStore.getState().addHistoryItem({
      q: "Q1",
      a: "A1",
      score: "8/10",
    });
    expect(useInterviewStore.getState().history).toHaveLength(1);
    expect(useInterviewStore.getState().history[0].score).toBe("8/10");
  });

  it("setTopic changes the topic", () => {
    useInterviewStore.getState().setTopic("深度学习基础");
    expect(useInterviewStore.getState().topic).toBe("深度学习基础");
  });

  it("setScore and setHint save evaluation data", () => {
    useInterviewStore.getState().setScore("9/10");
    useInterviewStore.getState().setHint("Try thinking about attention");
    expect(useInterviewStore.getState().score).toBe("9/10");
    expect(useInterviewStore.getState().hint).toBe(
      "Try thinking about attention",
    );
  });

  it("setCompleted marks interview as finished", () => {
    useInterviewStore.getState().setCompleted(true);
    expect(useInterviewStore.getState().completed).toBe(true);
  });

  it("reset clears everything", () => {
    useInterviewStore.getState().setInterview(mockInterview);
    useInterviewStore.getState().addHistoryItem({ q: "Q1", a: "A1" });
    useInterviewStore.getState().reset();
    const s = useInterviewStore.getState();
    expect(s.interview).toBeNull();
    expect(s.history).toHaveLength(0);
    expect(s.answerInput).toBe("");
    expect(s.completed).toBe(false);
  });

  // ── Streaming state tests ──

  it("starts with empty streaming state", () => {
    const s = useInterviewStore.getState();
    expect(s.streamingScore).toBe("");
    expect(s.streaming).toBe(false);
  });

  it("setStreamingScore sets full score text", () => {
    useInterviewStore.getState().setStreamingScore("正在评分...");
    expect(useInterviewStore.getState().streamingScore).toBe("正在评分...");
  });

  it("appendStreamingScore concatenates chunks", () => {
    useInterviewStore.getState().setStreamingScore("正确性: 8");
    useInterviewStore.getState().appendStreamingScore(" | 逻辑: 7");
    expect(useInterviewStore.getState().streamingScore).toBe(
      "正确性: 8 | 逻辑: 7",
    );
  });

  it("setStreaming toggles streaming flag", () => {
    useInterviewStore.getState().setStreaming(true);
    expect(useInterviewStore.getState().streaming).toBe(true);
    useInterviewStore.getState().setStreaming(false);
    expect(useInterviewStore.getState().streaming).toBe(false);
  });

  it("reset clears streaming state too", () => {
    useInterviewStore.getState().setStreamingScore("some scores");
    useInterviewStore.getState().setStreaming(true);
    useInterviewStore.getState().reset();
    const s = useInterviewStore.getState();
    expect(s.streamingScore).toBe("");
    expect(s.streaming).toBe(false);
  });

  // ── Timer state tests ──

  it("starts with default timer state", () => {
    const s = useInterviewStore.getState();
    expect(s.timerEnabled).toBe(true);
    expect(s.timerRemaining).toBe(120);
    expect(s.timerKey).toBe(0);
  });

  it("setTimerEnabled toggles timer", () => {
    useInterviewStore.getState().setTimerEnabled(false);
    expect(useInterviewStore.getState().timerEnabled).toBe(false);
    useInterviewStore.getState().setTimerEnabled(true);
    expect(useInterviewStore.getState().timerEnabled).toBe(true);
  });

  it("setTimerRemaining updates remaining time", () => {
    useInterviewStore.getState().setTimerRemaining(45);
    expect(useInterviewStore.getState().timerRemaining).toBe(45);
  });

  it("incrementTimerKey increments key", () => {
    useInterviewStore.getState().incrementTimerKey();
    expect(useInterviewStore.getState().timerKey).toBe(1);
    useInterviewStore.getState().incrementTimerKey();
    expect(useInterviewStore.getState().timerKey).toBe(2);
  });

  it("reset keeps timer defaults", () => {
    useInterviewStore.getState().setTimerEnabled(false);
    useInterviewStore.getState().setTimerRemaining(99);
    useInterviewStore.getState().reset();
    const s = useInterviewStore.getState();
    expect(s.timerEnabled).toBe(true);
    expect(s.timerRemaining).toBe(120);
    expect(s.timerKey).toBe(0);
  });
});
