import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock fetch for API tests
const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

// Import after mock
import { chat, getBookmarks, startInterview } from "./api";

describe("API client", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("chat sends POST to /chat", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ reply: "Hello!" }),
    });

    const result = await chat({ message: "Hi", api_key: "sk-test" });
    expect(result.reply).toBe("Hello!");
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/chat"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("startInterview sends POST to /interview/start", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session_id: "abc123",
        question: "What is AI?",
        stage: "基础",
        stage_index: 0,
        total_stages: 5,
        is_followup: false,
      }),
    });

    const result = await startInterview({
      api_key: "sk-test",
      topic: "Transformer 核心",
    });
    expect(result.session_id).toBe("abc123");
    expect(result.stage).toBe("基础");
  });

  it("throws on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      text: async () => "Bad Request",
    });

    await expect(
      chat({ message: "test", api_key: "x" }),
    ).rejects.toThrow("Bad Request");
  });

  it("getBookmarks fetches with query params", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ bookmarks: [] }),
    });

    const result = await getBookmarks("guest");
    expect(result.bookmarks).toEqual([]);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("user=guest");
  });
});
