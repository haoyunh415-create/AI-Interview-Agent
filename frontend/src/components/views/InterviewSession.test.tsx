import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { useInterviewStore } from "@/stores/interviewStore";
import { InterviewSession } from "./InterviewSession";

const mockQuestion = "What is the Transformer architecture?";

const mockInterview = {
  session_id: "sess-001",
  question: mockQuestion,
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
  submitMutation: mockMutation(),
  hintMutation: mockMutation(),
};

describe("InterviewSession", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useInterviewStore.setState({
      interview: null,
      history: [],
      answerInput: "",
      score: "",
      streamingScore: "",
      streaming: false,
      hint: "",
      completed: false,
      timerEnabled: true,
      timerRemaining: 120,
      timerKey: 0,
    });
  });

  it("returns null when no interview is active", () => {
    const { container } = renderWithProviders(
      <InterviewSession {...defaultProps} />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders the question when interview is active", () => {
    useInterviewStore.setState({ interview: mockInterview });
    renderWithProviders(<InterviewSession {...defaultProps} />);
    expect(screen.getByText(mockQuestion)).toBeInTheDocument();
  });

  it("shows followup tag for followup questions", () => {
    useInterviewStore.setState({
      interview: { ...mockInterview, is_followup: true },
    });
    renderWithProviders(<InterviewSession {...defaultProps} />);
    expect(screen.getByText("interview.followup")).toBeInTheDocument();
  });

  it("displays hint text when hint is set", () => {
    useInterviewStore.setState({
      interview: mockInterview,
      hint: "Think about the attention mechanism",
    });
    renderWithProviders(<InterviewSession {...defaultProps} />);
    expect(
      screen.getByText("Think about the attention mechanism"),
    ).toBeInTheDocument();
  });

  it("displays score text when score is set and not streaming", () => {
    useInterviewStore.setState({
      interview: mockInterview,
      score: "正确性: 8 | 逻辑: 7",
      streaming: false,
    });
    renderWithProviders(<InterviewSession {...defaultProps} />);
    expect(screen.getByText(/正确性/)).toBeInTheDocument();
  });

  it("shows streaming score during evaluation", () => {
    useInterviewStore.setState({
      interview: mockInterview,
      streamingScore: "正在分析回答...",
      streaming: true,
    });
    renderWithProviders(<InterviewSession {...defaultProps} />);
    expect(screen.getByText("正在分析回答...")).toBeInTheDocument();
  });

  it("renders answer textarea", () => {
    useInterviewStore.setState({ interview: mockInterview });
    renderWithProviders(<InterviewSession {...defaultProps} />);
    expect(
      screen.getByPlaceholderText("interview.answer_placeholder"),
    ).toBeInTheDocument();
  });

  it("updates answer input on textarea change", () => {
    useInterviewStore.setState({ interview: mockInterview, answerInput: "" });
    renderWithProviders(<InterviewSession {...defaultProps} />);
    const textarea = screen.getByPlaceholderText("interview.answer_placeholder");
    fireEvent.change(textarea, { target: { value: "My answer" } });
    expect(useInterviewStore.getState().answerInput).toBe("My answer");
  });

  it("renders history list when history exists", () => {
    useInterviewStore.setState({
      interview: mockInterview,
      history: [
        { q: "Q1", a: "A1", score: "8/10" },
        { q: "Q2", a: "A2" },
      ],
    });
    renderWithProviders(<InterviewSession {...defaultProps} />);
    expect(screen.getByText("Q1")).toBeInTheDocument();
    expect(screen.getByText("Q2")).toBeInTheDocument();
  });

  it("renders preview mode toggle button", () => {
    useInterviewStore.setState({ interview: mockInterview });
    renderWithProviders(<InterviewSession {...defaultProps} />);
    expect(screen.getByText("👁️ 预览")).toBeInTheDocument();
  });

  it("renders submit and hint buttons", () => {
    useInterviewStore.setState({
      interview: mockInterview,
      answerInput: "some answer",
    });
    renderWithProviders(<InterviewSession {...defaultProps} />);
    // The text may include emoji prefix, use getAllByText for partial match
    const submitBtns = screen.getAllByText("interview.submit");
    expect(submitBtns.length).toBeGreaterThanOrEqual(1);
  });

  it("calls hint mutation when hint button is clicked", () => {
    useInterviewStore.setState({ interview: mockInterview, answerInput: "test" });
    const hintMutation = mockMutation();
    renderWithProviders(
      <InterviewSession submitMutation={mockMutation()} hintMutation={hintMutation} />,
    );
    // Find the hint button by role, with accessible name containing hint text
    const buttons = screen.getAllByRole("button");
    const hintBtn = buttons.find((b) => b.textContent?.includes("interview.hint"));
    expect(hintBtn).toBeTruthy();
    if (hintBtn) {
      fireEvent.click(hintBtn);
      expect(hintMutation.mutate).toHaveBeenCalled();
    }
  });

  it("disables submit button when answer is empty", () => {
    useInterviewStore.setState({ interview: mockInterview, answerInput: "" });
    renderWithProviders(<InterviewSession {...defaultProps} />);
    const buttons = screen.getAllByRole("button");
    const submitBtn = buttons.find((b) => b.textContent?.includes("interview.submit"));
    expect(submitBtn).toBeTruthy();
    if (submitBtn) expect(submitBtn).toBeDisabled();
  });

  it("enables submit button when answer is non-empty", () => {
    useInterviewStore.setState({
      interview: mockInterview,
      answerInput: "My answer",
    });
    renderWithProviders(<InterviewSession {...defaultProps} />);
    const buttons = screen.getAllByRole("button");
    const submitBtn = buttons.find((b) => b.textContent?.includes("interview.submit"));
    expect(submitBtn).toBeTruthy();
    if (submitBtn) expect(submitBtn).not.toBeDisabled();
  });
});
