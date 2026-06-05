import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { Skeleton, MessageSkeleton, CardSkeleton } from "./skeleton";

describe("Skeleton", () => {
  it("renders with default props", () => {
    const { container } = renderWithProviders(<Skeleton />);
    const el = container.firstChild as HTMLElement;
    expect(el).toBeInTheDocument();
    expect(el.className).toContain("skeleton");
  });

  it("renders with custom dimensions", () => {
    const { container } = renderWithProviders(
      <Skeleton width={200} height={20} />,
    );
    const el = container.firstChild as HTMLElement;
    expect(el.style.width).toBe("200px");
    expect(el.style.height).toBe("20px");
  });
});

describe("MessageSkeleton", () => {
  it("renders multiple skeleton lines", () => {
    const { container } = renderWithProviders(<MessageSkeleton />);
    const skeletons = container.querySelectorAll(".skeleton");
    expect(skeletons.length).toBeGreaterThanOrEqual(4);
  });
});

describe("CardSkeleton", () => {
  it("renders specified number of lines", () => {
    const { container } = renderWithProviders(<CardSkeleton lines={5} />);
    const skeletons = container.querySelectorAll(".skeleton");
    expect(skeletons.length).toBe(6); // 1 title + 5 lines
  });
});
