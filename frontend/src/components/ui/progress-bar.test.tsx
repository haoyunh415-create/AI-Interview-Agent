import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { ProgressBar, StepIndicator } from "./progress-bar";

describe("ProgressBar", () => {
  it("renders progress text", () => {
    renderWithProviders(<ProgressBar current={2} total={5} />);
    expect(screen.getByText("2/5")).toBeInTheDocument();
  });

  it("renders with custom label", () => {
    renderWithProviders(
      <ProgressBar current={1} total={4} label="面试进度" />,
    );
    expect(screen.getByText("面试进度")).toBeInTheDocument();
  });

  it("handles zero total gracefully (no label shown)", () => {
    const { container } = renderWithProviders(
      <ProgressBar current={0} total={0} />,
    );
    // With 0 total, the label "0/0" won't be shown (conditional render)
    // But the component should still render without error
    expect(container.firstChild).toBeInTheDocument();
  });

  it("handles current=0", () => {
    renderWithProviders(<ProgressBar current={0} total={5} />);
    expect(screen.getByText("0/5")).toBeInTheDocument();
  });

  it("handles completion (current=total)", () => {
    renderWithProviders(<ProgressBar current={5} total={5} />);
    expect(screen.getByText("5/5")).toBeInTheDocument();
  });
});

describe("StepIndicator", () => {
  it("renders correct number of steps", () => {
    const steps = ["基础", "原理", "进阶", "项目", "挑战"];
    renderWithProviders(
      <StepIndicator steps={steps} currentIndex={2} />,
    );
    // All step numbers should be rendered
    steps.forEach((_, i) => {
      expect(screen.getByText(String(i + 1))).toBeInTheDocument();
    });
  });
});
