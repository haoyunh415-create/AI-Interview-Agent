import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { ErrorBoundary, ErrorFallback } from "./ErrorBoundary";

describe("ErrorFallback", () => {
  it("renders error message", () => {
    renderWithProviders(
      <ErrorFallback error={new Error("Something broke")} />,
    );
    expect(screen.getByText("页面出现异常")).toBeInTheDocument();
  });

  it("shows error details when expanded", () => {
    renderWithProviders(
      <ErrorFallback error={new Error("Test error message")} />,
    );
    const details = screen.getByText("错误详情");
    expect(details).toBeInTheDocument();
  });

  it("renders retry button when onReset provided", () => {
    const onReset = vi.fn();
    renderWithProviders(
      <ErrorFallback error={new Error("Boom")} onReset={onReset} />,
    );
    const retryBtn = screen.getByText("重试");
    expect(retryBtn).toBeInTheDocument();
  });

  it("renders refresh button", () => {
    renderWithProviders(
      <ErrorFallback error={new Error("Boom")} />,
    );
    expect(screen.getByText("刷新页面")).toBeInTheDocument();
  });
});

describe("ErrorBoundary", () => {
  function Bomb({ shouldThrow }: { shouldThrow: boolean }) {
    if (shouldThrow) {
      throw new Error("Kaboom!");
    }
    return <div>Safe content</div>;
  }

  it("renders children when no error", () => {
    renderWithProviders(
      <ErrorBoundary>
        <div>All good</div>
      </ErrorBoundary>,
    );
    expect(screen.getByText("All good")).toBeInTheDocument();
  });

  it("renders fallback on error", () => {
    // Suppress console.error from React error logging
    const origError = console.error;
    console.error = vi.fn();

    renderWithProviders(
      <ErrorBoundary>
        <Bomb shouldThrow={true} />
      </ErrorBoundary>,
    );
    expect(screen.getByText("页面出现异常")).toBeInTheDocument();

    console.error = origError;
  });

  it("accepts custom fallback", () => {
    const origError = console.error;
    console.error = vi.fn();

    renderWithProviders(
      <ErrorBoundary fallback={<div>Custom error UI</div>}>
        <Bomb shouldThrow={true} />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Custom error UI")).toBeInTheDocument();

    console.error = origError;
  });
});
