import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { InterviewSetup } from "./InterviewSetup";

// Mock mutation object — only exposes the properties the component needs
function mockMutation(overrides = {}) {
  return {
    isPending: false,
    mutate: vi.fn(),
    ...overrides,
  } as any;
}

const defaultProps = {
  apiKey: "sk-test",
  serverHasKey: false,
  topic: "Transformer 核心",
  customTopic: "",
  timerEnabled: true,
  availableSessions: [] as any[],
  startMutation: mockMutation(),
  resumeMutation: mockMutation(),
  onTopicChange: vi.fn(),
  onCustomTopicChange: vi.fn(),
  onTimerToggle: vi.fn(),
  onStart: vi.fn(),
};

describe("InterviewSetup", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the topic selection grid", () => {
    renderWithProviders(<InterviewSetup {...defaultProps} />);
    // Should render known topic buttons
    expect(screen.getByText("Transformer 核心")).toBeInTheDocument();
    expect(screen.getByText("深度学习基础")).toBeInTheDocument();
    expect(screen.getByText("自然语言处理")).toBeInTheDocument();
    expect(screen.getByText("自定义")).toBeInTheDocument();
  });

  it("highlights the selected topic", () => {
    renderWithProviders(<InterviewSetup {...defaultProps} topic="深度学习基础" />);
    const btn = screen.getByText("深度学习基础");
    // Selected topic has the "tag-primary" class
    expect(btn.className).toContain("tag-primary");
  });

  it("calls onTopicChange when a topic is clicked", () => {
    const onTopicChange = vi.fn();
    renderWithProviders(
      <InterviewSetup {...defaultProps} onTopicChange={onTopicChange} />,
    );
    fireEvent.click(screen.getByText("计算机视觉"));
    expect(onTopicChange).toHaveBeenCalledWith("计算机视觉");
  });

  it("shows custom topic input when '自定义' is selected", () => {
    renderWithProviders(
      <InterviewSetup {...defaultProps} topic="自定义" />,
    );
    expect(
      screen.getByPlaceholderText("interview.custom_topic"),
    ).toBeInTheDocument();
  });

  it("calls onCustomTopicChange when custom topic input changes", () => {
    const onCustomTopicChange = vi.fn();
    renderWithProviders(
      <InterviewSetup
        {...defaultProps}
        topic="自定义"
        onCustomTopicChange={onCustomTopicChange}
      />,
    );
    const input = screen.getByPlaceholderText("interview.custom_topic");
    fireEvent.change(input, { target: { value: "LLM 推理优化" } });
    expect(onCustomTopicChange).toHaveBeenCalledWith("LLM 推理优化");
  });

  it("renders the start button", () => {
    renderWithProviders(<InterviewSetup {...defaultProps} />);
    expect(screen.getByText("interview.start")).toBeInTheDocument();
  });

  it("calls onStart when start button is clicked", () => {
    const onStart = vi.fn();
    renderWithProviders(
      <InterviewSetup {...defaultProps} onStart={onStart} />,
    );
    fireEvent.click(screen.getByText("interview.start"));
    expect(onStart).toHaveBeenCalledTimes(1);
  });

  it("disables start button when no API key and server has no key", () => {
    renderWithProviders(
      <InterviewSetup {...defaultProps} apiKey="" serverHasKey={false} />,
    );
    expect(screen.getByText("interview.start")).toBeDisabled();
  });

  it("shows 'starting' text when mutation is pending", () => {
    renderWithProviders(
      <InterviewSetup
        {...defaultProps}
        startMutation={mockMutation({ isPending: true })}
      />,
    );
    expect(screen.getByText("interview.starting")).toBeInTheDocument();
  });

  it("renders timer toggle", () => {
    renderWithProviders(<InterviewSetup {...defaultProps} />);
    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeInTheDocument();
    expect(checkbox).toBeChecked();
  });

  it("calls onTimerToggle when checkbox is clicked", () => {
    const onTimerToggle = vi.fn();
    renderWithProviders(
      <InterviewSetup {...defaultProps} onTimerToggle={onTimerToggle} />,
    );
    fireEvent.click(screen.getByRole("checkbox"));
    expect(onTimerToggle).toHaveBeenCalledWith(false);
  });

  it("shows resume session buttons when sessions are available", () => {
    const sessions = [
      { id: 1, topic: "Transformer 核心", stage_index: 1, question_count: 3 },
      { id: 2, topic: "深度学习基础", stage_index: 0, question_count: 5 },
    ];
    renderWithProviders(
      <InterviewSetup
        {...defaultProps}
        availableSessions={sessions}
      />,
    );
    // Both the topic buttons and resume cards contain these texts
    const transformerEls = screen.getAllByText(/Transformer 核心/);
    expect(transformerEls.length).toBeGreaterThanOrEqual(2);
    const deepLearningEls = screen.getAllByText(/深度学习基础/);
    expect(deepLearningEls.length).toBeGreaterThanOrEqual(2);
  });

  it("calls resumeMutation.mutate when resume button is clicked", () => {
    const resumeMutation = mockMutation();
    const sessions = [
      { id: 42, topic: "NLP", stage_index: 2, question_count: 7 },
    ];
    renderWithProviders(
      <InterviewSetup
        {...defaultProps}
        availableSessions={sessions}
        resumeMutation={resumeMutation}
      />,
    );
    fireEvent.click(screen.getByText(/NLP/));
    expect(resumeMutation.mutate).toHaveBeenCalledWith(42);
  });
});
