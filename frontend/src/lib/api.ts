const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765/api";

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export interface ChatMessage { role: string; content: string }
export interface ChatRequest { message: string; api_key?: string; provider?: string; model?: string; history?: ChatMessage[] }
export interface ChatResponse { reply: string }
export const chat = (req: ChatRequest) => apiPost<ChatResponse>("/chat", req);

/** SSE streaming chat — yields tokens as they arrive, returns on done.
 *
 * Automatically retries on network failure with exponential backoff + jitter
 * so transient blips don't kill the conversation.
 */
export interface ChatStreamEvent {
  type: "token" | "done" | "error";
  content?: string;
  message?: string;
}
export async function chatStream(
  req: ChatRequest,
  onToken: (text: string) => void,
  onDone: () => void,
  onError: (err: Error) => void,
  retries = 2,
  onRetrying?: (attempt: number) => void,
): Promise<void> {
  const attempt = async (attemptNum: number): Promise<void> => {
    try {
      const res = await fetch(`${API_BASE}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
      });
      if (!res.ok) {
        const err = await res.text();
        throw new Error(err || `HTTP ${res.status}`);
      }
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const event: ChatStreamEvent = JSON.parse(line.slice(6));
              if (event.type === "token" && event.content) {
                onToken(event.content);
              } else if (event.type === "done") {
                onDone();
                return;
              } else if (event.type === "error") {
                onError(new Error(event.message || "Stream error"));
                return;
              }
            } catch { /* skip malformed */ }
          }
        }
      }
      // Stream ended without "done" event
      throw new Error("Stream ended unexpectedly");
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      if (attemptNum < retries) {
        onRetrying?.(attemptNum + 1);
        // Exponential backoff with jitter: base 1s, 2s, 4s capped at 8s
        const baseDelay = Math.min(1000 * Math.pow(2, attemptNum - 1), 8000);
        const jitter = Math.random() * 0.3 * baseDelay;
        await new Promise((resolve) => setTimeout(resolve, baseDelay + jitter));
        return attempt(attemptNum + 1);
      }
      onError(error);
    }
  };

  return attempt(1);
}

// ── Session-based chat (API key stored server-side) ──
export interface ChatSessionRequest { api_key: string; provider?: string; model?: string }
export interface ChatSessionResponse { session_id: string }
export interface ChatSessionMessageRequest { message: string; history?: ChatMessage[] }

/** Create a chat session — stores API key on the server. */
export const createChatSession = (req: ChatSessionRequest) =>
  apiPost<ChatSessionResponse>("/chat/session", req);

/** Send a message using a previously created chat session. */
export const sendChatMessage = (sessionId: string, req: ChatSessionMessageRequest) =>
  apiPost<ChatResponse>(`/chat/session/${sessionId}`, req);

export interface AnalyzeRequest { resume_text: string; api_key: string; provider?: string; model?: string }
export interface ResumeProfile {
  tech_stack: string[];
  level: string;
  domains: string[];
  gaps: string[];
  highlights: string[];
  years_of_experience: number;
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  learning_path: string[];
  recommended_topics: string[];
  keywords: Array<{ term: string; weight: number }>;
}

export interface AnalyzeResponse { session_id: string; profile: ResumeProfile }
export const analyzeResume = (req: AnalyzeRequest) => apiPost<AnalyzeResponse>("/resume/analyze", req);

/** Upload a PDF resume for server-side text extraction and analysis. */
export interface PdfAnalyzeResponse {
  session_id: string;
  profile: ResumeProfile;
  filename: string;
  text_length: number;
}
export async function analyzeResumePdf(
  file: File,
  apiKey: string,
  provider?: string,
  model?: string,
): Promise<PdfAnalyzeResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("api_key", apiKey);
  if (provider) formData.append("provider", provider);
  if (model) formData.append("model", model);

  const res = await fetch(`${API_BASE}/resume/analyze/pdf`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

export interface StartInterviewRequest { api_key: string; topic: string; resume_text?: string; custom_questions?: string[]; provider?: string; model?: string }
export interface StartInterviewResponse { session_id: string; question: string; stage: string; stage_index: number; total_stages: number; is_followup: boolean }
export const startInterview = (req: StartInterviewRequest) => apiPost<StartInterviewResponse>("/interview/start", req);

export interface AnswerRequest { session_id: string; answer: string }
export interface AnswerResponse { score_text: string; score_json: Record<string, unknown>; needs_followup: boolean; is_followup: boolean; next_question: string | null; stage_index: number; completed: boolean; has_error: boolean }
export const submitAnswer = (req: AnswerRequest) => apiPost<AnswerResponse>("/interview/answer", req);

export interface AnswerStreamEvent {
  type: "token" | "done" | "error";
  content?: string;
  score_text?: string;
  score_json?: Record<string, unknown>;
  needs_followup?: boolean;
  is_followup?: boolean;
  next_question?: string | null;
  stage_index?: number;
  completed?: boolean;
  has_error?: boolean;
  message?: string;
}

export async function submitAnswerStream(
  sessionId: string,
  answer: string,
  onToken: (text: string) => void,
  onDone: (result: AnswerStreamEvent) => void,
  onError: (err: Error) => void,
  retries = 2,
): Promise<void> {
  const attempt = async (attemptNum: number): Promise<void> => {
    try {
      const res = await fetch(`${API_BASE}/interview/answer/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, answer }),
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || `HTTP ${res.status}`);
      }
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events (may contain multiple events in one chunk)
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            try {
              const event: AnswerStreamEvent = JSON.parse(data);
              if (event.type === "token" && event.content) {
                onToken(event.content);
              } else if (event.type === "done") {
                onDone(event);
                return;
              } else if (event.type === "error") {
                onError(new Error(event.message || "Stream error"));
                return;
              }
            } catch {
              // skip malformed events
            }
          }
        }
      }
      // Stream ended without "done" event — treat as error
      throw new Error("Stream ended unexpectedly");
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      if (attemptNum < retries) {
        // Exponential backoff with jitter: 1s, 2s, 4s capped at 8s
        const baseDelay = Math.min(1000 * Math.pow(2, attemptNum - 1), 8000);
        const jitter = Math.random() * 0.3 * baseDelay;
        await new Promise((resolve) => setTimeout(resolve, baseDelay + jitter));
        return attempt(attemptNum + 1);
      }
      onError(error);
    }
  };

  return attempt(1);
}
export interface HintRequest { session_id: string }
export interface HintResponse { hint: string }
export const getHint = (req: HintRequest) => apiPost<HintResponse>("/interview/hint", req);

export interface StageBreakdown {
  stage: string;
  total: number;
  answered_count: number;
  skipped_count: number;
  score: number | null;
  questions: string[];
  answers: string[];
  answers_summary?: string[];
  scores: string[];
  skipped_questions: string[];
}
export interface ReportRequest { api_key: string; user?: string }
export interface ReportResponse { stats: Record<string, unknown>; questions: string[]; answers: string[]; scores: string[]; ai_summary: string | null }
export const getReport = (req: ReportRequest) => apiPost<ReportResponse>("/report", req);

// ── Per-session report history ──

export interface SessionReportItem {
  id: number;
  session_id: string;
  topic: string;
  created_at: string | null;
}
export interface SessionReportDetail {
  session_id: string;
  topic: string;
  created_at: string;
  ai_summary: string | null;
  stats: { total_questions: number; answered_count: number; skipped_count: number } | null;
  stage_breakdown: StageBreakdown[] | null;
}
export const listReportSessions = (user = "guest", limit = 20) =>
  apiGet<{ sessions: SessionReportItem[] }>(`/reports?user=${user}&limit=${limit}`);

export const getSessionReport = (sessionId: string, user = "guest") =>
  apiGet<SessionReportDetail>(`/reports/${sessionId}?user=${user}`);

export interface Bookmark { id: number; question: string; answer: string; topic: string; stage: string; notes: string; tags: string[]; created_at: string }
export const getBookmarks = (user = "guest", topic?: string) => {
  const params = new URLSearchParams({ user });
  if (topic) params.set("topic", topic);
  return apiGet<{ bookmarks: Bookmark[] }>(`/bookmarks?${params}`);
};
export const createBookmark = (data: { user?: string; question: string; answer?: string; topic?: string; stage?: string }) =>
  apiPost<{ id: number }>("/bookmarks", data);
export const deleteBookmark = async (id: number, user = "guest") => {
  const res = await fetch(`${API_BASE}/bookmarks/${id}?user=${user}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<{ ok: boolean }>;
};

// ── Auth ──

export interface RegisterRequest { username: string; password: string; display_name?: string }
export interface AuthResponse { access_token: string; token_type: string; username: string; display_name: string }
export interface UserInfo { id: number; username: string; display_name: string; created_at: string }

export const register = (req: RegisterRequest) => apiPost<AuthResponse>("/auth/register", req);
export const login = (req: { username: string; password: string }) => apiPost<AuthResponse>("/auth/login", req);
export const getMe = (token: string) => {
  return fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  }).then((r) => { if (!r.ok) throw new Error("Auth failed"); return r.json() as Promise<UserInfo>; });
};

// Get auth header helper
export function authHeader(token: string | null): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── Session resume ──

export interface SessionItem {
  id: number;
  topic: string;
  stage_index: number;
  question_count: number;
  updated_at: string | null;
}

export interface ResumeRequest {
  api_key: string;
  session_id: number;
  resume_text?: string;
}

export interface ResumeResponse {
  session_id: string;
  question: string | null;
  stage: string;
  stage_index: number;
  total_stages: number;
  is_followup: boolean;
  history: Array<{ q: string; a: string }>;
  completed: boolean;
}

export const listSessions = (user = "guest", limit = 10) =>
  apiGet<{ sessions: SessionItem[] }>(`/sessions?user=${user}&limit=${limit}`);

export const resumeInterview = (req: ResumeRequest) =>
  apiPost<ResumeResponse>("/interview/resume", req);

// ── PDF Report ──

export function downloadPdfReport(apiKey: string, user = "guest") {
  const url = `${API_BASE}/report/pdf`;
  // Use a form POST to send the api_key (FileResponse doesn't accept JSON body via GET)
  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey, user }),
  })
    .then((res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.blob();
    })
    .then((blob) => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `${user}_report.pdf`;
      a.click();
      URL.revokeObjectURL(a.href);
    })
    .catch((err) => console.error("PDF download failed:", err));
}
