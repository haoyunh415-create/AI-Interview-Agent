import { describe, it, expect, beforeEach } from "vitest";
import { useReportStore } from "./reportStore";
import { useBookmarkStore } from "./bookmarkStore";
import { useResumeStore } from "./resumeStore";

describe("reportStore", () => {
  beforeEach(() => {
    useReportStore.setState({ data: null, loading: false });
  });

  it("starts empty", () => {
    expect(useReportStore.getState().data).toBeNull();
    expect(useReportStore.getState().loading).toBe(false);
  });

  it("setData stores report data", () => {
    const d = { stats: { total_questions: 5 }, aiSummary: "Good job" };
    useReportStore.getState().setData(d);
    expect(useReportStore.getState().data).toEqual(d);
  });
});

describe("bookmarkStore", () => {
  beforeEach(() => {
    useBookmarkStore.setState({ bookmarks: [], loading: false });
  });

  it("starts empty", () => {
    expect(useBookmarkStore.getState().bookmarks).toHaveLength(0);
  });

  it("setBookmarks replaces bookmarks", () => {
    const bm = [
      { id: 1, question: "Q1", answer: "A1", topic: "AI", stage: "基础", notes: "", tags: [], created_at: "" },
    ];
    useBookmarkStore.getState().setBookmarks(bm);
    expect(useBookmarkStore.getState().bookmarks).toHaveLength(1);
  });
});

describe("resumeStore", () => {
  beforeEach(() => {
    useResumeStore.setState({ text: "", profile: null, loading: false });
  });

  it("starts empty", () => {
    expect(useResumeStore.getState().text).toBe("");
    expect(useResumeStore.getState().profile).toBeNull();
  });

  it("setText updates resume text", () => {
    useResumeStore.getState().setText("Senior Engineer...");
    expect(useResumeStore.getState().text).toBe("Senior Engineer...");
  });

  it("setProfile stores parsed profile", () => {
    const p = {
      level: "Senior", tech_stack: ["Python", "PyTorch"], domains: [],
      gaps: [], highlights: [], years_of_experience: 5,
      overall_score: 0, strengths: [], weaknesses: [],
      learning_path: [], recommended_topics: [], keywords: [],
    };
    useResumeStore.getState().setProfile(p);
    expect(useResumeStore.getState().profile).toEqual(p);
  });
});
