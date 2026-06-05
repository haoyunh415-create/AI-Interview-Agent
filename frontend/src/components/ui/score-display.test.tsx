import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { ScoreBadge, ScoreMeter } from "./score-display";

describe("ScoreBadge", () => {
  it("renders fraction score like 8/10", () => {
    const { container } = renderWithProviders(<ScoreBadge scoreText="8/10" />);
    expect(container.textContent).toContain("8/10");
  });

  it("renders percentage score", () => {
    const { container } = renderWithProviders(<ScoreBadge scoreText="85%" />);
    expect(container.textContent).toContain("85%");
  });

  it("renders raw text when no pattern matched", () => {
    const { container } = renderWithProviders(
      <ScoreBadge scoreText="Excellent answer!" />,
    );
    expect(container.textContent).toContain("Excellent answer!");
  });

  it("shows star emoji for high score (>=80)", () => {
    const { container } = renderWithProviders(<ScoreBadge scoreText="9/10" />);
    expect(container.textContent).toContain("🌟");
  });

  it("shows pencil emoji for low score (<60)", () => {
    const { container } = renderWithProviders(<ScoreBadge scoreText="4/10" />);
    expect(container.textContent).toContain("📝");
  });
});

describe("ScoreMeter", () => {
  it("renders fraction with bar visualization", () => {
    const { container } = renderWithProviders(<ScoreMeter scoreText="8/10" />);
    expect(screen.getByText("得分")).toBeInTheDocument();
    expect(container.textContent).toContain("8/10");
  });

  it("renders raw text without bar when no pattern matched", () => {
    renderWithProviders(<ScoreMeter scoreText="Incomplete" />);
    expect(screen.getByText("Incomplete")).toBeInTheDocument();
  });
});
