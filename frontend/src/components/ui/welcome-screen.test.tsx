import { describe, it, expect, vi } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { WelcomeScreen } from "./welcome-screen";

describe("WelcomeScreen", () => {
  it("renders suggestions", () => {
    const onSuggestion = vi.fn();
    renderWithProviders(
      <WelcomeScreen onSuggestionClick={onSuggestion} />,
    );
    // Should have 4 suggestion buttons
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThanOrEqual(4);
  });

  it("calls onSuggestionClick when suggestion is clicked", () => {
    const onSuggestion = vi.fn();
    renderWithProviders(
      <WelcomeScreen onSuggestionClick={onSuggestion} />,
    );
    // Click the first suggestion button
    const buttons = screen.getAllByRole("button");
    fireEvent.click(buttons[0]);
    expect(onSuggestion).toHaveBeenCalledTimes(1);
    expect(typeof onSuggestion.mock.calls[0][0]).toBe("string");
  });

  it("renders the app title", () => {
    renderWithProviders(
      <WelcomeScreen onSuggestionClick={vi.fn()} />,
    );
    expect(screen.getByText("AI 面试助手")).toBeInTheDocument();
  });
});
