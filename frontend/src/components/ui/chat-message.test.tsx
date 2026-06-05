import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { ChatMessage } from "./chat-message";

// Mock dynamic MarkdownRenderer — vitest can't resolve next/dynamic
vi.mock("./markdown", () => ({
  MarkdownRenderer: ({ content }: { content: string }) =>
    content ? <div data-testid="markdown">{content}</div> : null,
}));

describe("ChatMessage", () => {
  it("renders user message with U avatar", () => {
    renderWithProviders(
      <ChatMessage role="user" content="Hello world" />,
    );
    expect(screen.getByText("Hello world")).toBeInTheDocument();
    expect(screen.getByText("U")).toBeInTheDocument();
  });

  it("renders assistant message with AI avatar", () => {
    renderWithProviders(
      <ChatMessage role="assistant" content="Hi there!" />,
    );
    expect(screen.getByText("Hi there!")).toBeInTheDocument();
    expect(screen.getByText("AI")).toBeInTheDocument();
  });

  it("shows typing dots when loading", () => {
    renderWithProviders(
      <ChatMessage role="assistant" content="" isLoading />,
    );
    // Text is split across spans (思考中 + . + . + .)
    const container = screen.getByText((content) =>
      content.includes("思考中"),
    );
    expect(container).toBeInTheDocument();
    // Should have 3 dot spans
    const dots = container.querySelectorAll("span");
    expect(dots.length).toBe(3);
  });

  it("renders multi-line content", () => {
    const multiLine = "Line 1\nLine 2\nLine 3";
    renderWithProviders(
      <ChatMessage role="user" content={multiLine} />,
    );
    expect(screen.getByText(/Line 1/)).toBeInTheDocument();
    expect(screen.getByText(/Line 2/)).toBeInTheDocument();
    expect(screen.getByText(/Line 3/)).toBeInTheDocument();
  });
});
