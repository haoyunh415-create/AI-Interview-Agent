import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { useInterviewStore } from "@/stores/interviewStore";
import { useAppStore } from "@/stores/appStore";
import { InterviewCompleted } from "./InterviewCompleted";

const mockInterview = {
  session_id: "sess-001",
  question: "What is Transformer?",
  stage: "基础",
  stage_index: 0,
  total_stages: 5,
  is_followup: false,
};

function mockMutation(overrides = {}) {
  return {
    isPending: false,
    mutate: vi.fn(),
    ...overrides,
  } as any;
}

const defaultProps = {
  startMutation: mockMutation(),
  bookmarkMutation: mockMutation(),
  batchBookmarkMutation: mockMutation(),
};

describe("InterviewCompleted", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve()));
    useInterviewStore.setState({
      interview: mockInterview,
      history: [],
      completed: true,
      topic: "Transformer 核心",
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the completed celebration", () => {
    renderWithProviders(<InterviewCompleted {...defaultProps} />);
    expect(screen.getByText("interview.completed")).toBeInTheDocument();
  });

  it("renders action buttons", () => {
    const { container } = renderWithProviders(<InterviewCompleted {...defaultProps} />);
    // Check buttons exist by text content
    expect(container.textContent).toContain("interview.view_report");
    expect(container.textContent).toContain("追加题目");
    expect(container.textContent).toContain("重新面试");
  });

  it("renders history items when present", () => {
    useInterviewStore.setState({
      interview: mockInterview,
      history: [
        { q: "What is RAG?", a: "Retrieval Augmented Generation", score: "9/10" },
        { q: "Explain attention", a: "Query, Key, Value mechanism" },
      ],
    });
    renderWithProviders(<InterviewCompleted {...defaultProps} />);
    expect(screen.getByText("What is RAG?")).toBeInTheDocument();
    expect(screen.getByText("Explain attention")).toBeInTheDocument();
  });

  it("renders batch bookmark button when history exists", () => {
    useInterviewStore.setState({
      interview: mockInterview,
      history: [{ q: "Q1", a: "A1" }],
    });
    renderWithProviders(<InterviewCompleted {...defaultProps} />);
    expect(screen.getByText("⭐ 全部收藏")).toBeInTheDocument();
  });

  it("calls batchBookmarkMutation when '全部收藏' is clicked", () => {
    const batchBookmarkMutation = mockMutation();
    useInterviewStore.setState({
      interview: mockInterview,
      history: [
        { q: "Q1", a: "A1" },
        { q: "Q2", a: "A2" },
      ],
    });
    renderWithProviders(
      <InterviewCompleted
        {...defaultProps}
        batchBookmarkMutation={batchBookmarkMutation}
      />,
    );
    fireEvent.click(screen.getByText("⭐ 全部收藏"));
    expect(batchBookmarkMutation.mutate).toHaveBeenCalledWith([
      { q: "Q1", a: "A1" },
      { q: "Q2", a: "A2" },
    ]);
  });

  it("calls startMutation when '追加题目' is clicked", () => {
    vi.useFakeTimers();
    useAppStore.setState({ apiKey: "sk-test" });
    const startMutation = mockMutation();
    renderWithProviders(
      <InterviewCompleted {...defaultProps} startMutation={startMutation} />,
    );
    fireEvent.click(screen.getByText("➕ 追加题目"));
    vi.advanceTimersByTime(200);
    expect(startMutation.mutate).toHaveBeenCalledWith("Transformer 核心");
    vi.useRealTimers();
  });

  it("resets interview state when '重新面试' is clicked", () => {
    renderWithProviders(<InterviewCompleted {...defaultProps} />);
    fireEvent.click(screen.getByText("🔄 重新面试"));
    expect(useInterviewStore.getState().interview).toBeNull();
    expect(useInterviewStore.getState().history).toHaveLength(0);
    expect(useInterviewStore.getState().completed).toBe(false);
  });
});
