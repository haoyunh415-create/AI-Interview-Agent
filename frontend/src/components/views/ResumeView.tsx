"use client";

import { useCallback, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { analyzeResume, analyzeResumePdf, startInterview } from "@/lib/api";
import type { ResumeProfile } from "@/lib/api";
import { useAppStore } from "@/stores/appStore";
import { useResumeStore } from "@/stores/resumeStore";
import { useInterviewStore } from "@/stores/interviewStore";
import { CardSkeleton } from "@/components/ui/skeleton";

function ScoreCircle({ score }: { score: number }) {
  const color = score >= 80 ? "var(--success)" : score >= 60 ? "var(--primary)" : score >= 40 ? "var(--warning)" : "var(--danger)";
  return (
    <div className="card-base" style={{ padding: "20px 24px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minWidth: 140 }}>
      <div style={{ width: 72, height: 72, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", border: `4px solid ${color}`, fontSize: "1.4rem", fontWeight: 700, color }}>
        {score}
      </div>
      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: 6 }}>综合评分</div>
    </div>
  );
}

function InfoCard({ profile }: { profile: ResumeProfile }) {
  return (
    <div className="card-base" style={{ flex: 1, padding: 16, minWidth: 180 }}>
      <div className="section-title">基本信息</div>
      <div style={{ fontSize: "0.9rem", lineHeight: 2, color: "var(--fg)" }}>
        <div><span style={{ color: "var(--text-muted)" }}>级别：</span><strong>{profile.level || "未知"}</strong></div>
        <div><span style={{ color: "var(--text-muted)" }}>经验：</span><strong>{profile.years_of_experience || 0} 年</strong></div>
      </div>
      {profile.tech_stack.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 8 }}>
          {profile.tech_stack.map((t, i) => <span key={i} className="tag tag-primary">{t}</span>)}
        </div>
      )}
    </div>
  );
}

function SectionCard({ title, icon, items, color }: { title: string; icon: string; items: string[]; color?: string }) {
  if (items.length === 0) return null;
  return (
    <div className="card-base" style={{ padding: 16, borderLeft: color ? `3px solid ${color}` : undefined }}>
      <div className="section-title" style={{ color }}>{icon} {title}</div>
      <ul style={{ margin: 0, paddingLeft: 16, fontSize: "0.85rem", lineHeight: 2, color: "var(--fg)" }}>
        {items.map((item, i) => <li key={i}>{item}</li>)}
      </ul>
    </div>
  );
}

function TagList({ title, items, variant }: { title: string; items: string[]; variant: "primary" | "warning" }) {
  if (items.length === 0) return null;
  const cls = variant === "primary" ? "tag tag-primary" : "chip chip-warning";
  return (
    <div className="card-base" style={{ padding: 16 }}>
      <div className="section-title">{title}</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
        {items.map((item, i) => <span key={i} className={cls}>{item}</span>)}
      </div>
    </div>
  );
}

export function ResumeView() {
  const apiKey = useAppStore((s) => s.apiKey);
  const serverHasKey = useAppStore((s) => s.serverHasKey);
  const provider = useAppStore((s) => s.provider);
  const model = useAppStore((s) => s.model);
  const setMode = useAppStore((s) => s.setMode);
  const profile = useResumeStore((s) => s.profile);
  const loading = useResumeStore((s) => s.loading);
  const setProfile = useResumeStore((s) => s.setProfile);
  const setLoading = useResumeStore((s) => s.setLoading);
  const setResumeText = useResumeStore((s) => s.setText);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const analyzeMutation = useMutation({
    mutationFn: (text: string) => analyzeResume({ resume_text: text, api_key: apiKey, provider, model }),
    onMutate: () => setLoading(true),
    onSuccess: (res) => { setProfile(res.profile); toast.success("简历分析完成"); },
    onError: (e: Error) => toast.error(`分析失败: ${e.message}`),
    onSettled: () => setLoading(false),
  });

  const handleTextSubmit = useCallback((text: string) => {
    if (!text.trim() || (!apiKey && !serverHasKey)) return;
    setResumeText(text.trim());  // Save for interview use
    setProfile(null);
    analyzeMutation.mutate(text);
  }, [apiKey, serverHasKey, analyzeMutation, setProfile, setResumeText]);

  const pdfMutate = useMutation({
    mutationFn: (file: File) => analyzeResumePdf(file, apiKey, provider, model),
    onMutate: () => setLoading(true),
    onSuccess: (res) => { setProfile(res.profile); toast.success(`PDF 分析完成 (${res.filename}, ${res.text_length} 字符)`); },
    onError: (e: Error) => toast.error(`PDF 分析失败: ${e.message}`),
    onSettled: () => setLoading(false),
  });

  const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!ext || !["txt", "md", "pdf"].includes(ext)) { toast.error("仅支持 TXT、Markdown 和 PDF 文件"); return; }
    if (ext === "pdf") {
      if (!apiKey && !serverHasKey) { toast.error("请先配置 API 密钥"); return; }
      pdfMutate.mutate(file); return;
    }
    const reader = new FileReader();
    reader.onload = (ev) => { const text = ev.target?.result as string; if (text) handleTextSubmit(text); };
    reader.readAsText(file);
  }, [handleTextSubmit, apiKey, provider, model, pdfMutate]);

  const startInterviewMutation = useMutation({
    mutationFn: (params: { text: string; topic: string }) =>
      startInterview({ api_key: apiKey, resume_text: params.text, topic: params.topic, provider, model }),
    onSuccess: (res) => {
      toast.success("面试已就绪，开始答题！");
      // Store interview session and navigate
      useInterviewStore.getState().setInterview(res);
      setMode("interview");
    },
    onError: (e: Error) => toast.error(`面试启动失败: ${e.message}`),
  });

  const handleStartInterview = useCallback(() => {
    // Use text saved during analysis (preferred), or textarea as fallback
    const savedText = useResumeStore.getState().text;
    const text = savedText || textAreaRef.current?.value || "";
    if (text.trim()) setResumeText(text.trim());
    const topics = profile?.recommended_topics || [];
    const targetTopic = topics.length > 0 ? topics[0] : "Transformer 核心";

    startInterviewMutation.mutate({ text: text.trim(), topic: targetTopic });
  }, [profile, setResumeText, startInterviewMutation]);

  // ── Empty state ──
  if (!profile && !loading) {
    return (
      <div className="smooth-scroll" style={{ maxWidth: "var(--content-max-width)", margin: "0 auto", width: "100%", padding: "24px 16px" }}>
        <div className="empty-state animate-fade-in" style={{ padding: "60px 20px" }}>
          <div style={{ fontSize: "2.5rem", opacity: 0.5 }}>📄</div>
          <h3 style={{ margin: 0, fontSize: "1rem", color: "var(--fg)" }}>简历分析</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", maxWidth: 360, textAlign: "center" }}>
            上传简历文件或粘贴文本，AI 将进行深度分析并生成个性化面试建议
          </p>
          <input ref={fileInputRef} type="file" accept=".txt,.md,.pdf" onChange={handleFileUpload} style={{ display: "none" }} />
          <button onClick={() => fileInputRef.current?.click()} className="btn-ghost" style={{ marginTop: 4 }}>📁 上传文件（TXT/MD/PDF）</button>
          <div style={{ width: "100%", maxWidth: 480, display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
            <textarea ref={textAreaRef} placeholder="或直接粘贴简历文本..." className="input-base" rows={6} style={{ width: "100%", padding: "12px 14px", fontSize: "0.85rem", lineHeight: 1.6, resize: "vertical" }} />
            <button onClick={() => { if (textAreaRef.current) handleTextSubmit(textAreaRef.current.value); }} disabled={!apiKey && !serverHasKey} className="btn-primary">
              📄 深度分析简历
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Loading ──
  if (loading) {
    return (
      <div className="smooth-scroll" style={{ maxWidth: "var(--content-max-width)", margin: "0 auto", width: "100%", padding: "24px 16px" }}>
        <CardSkeleton lines={2} />
        <CardSkeleton lines={3} />
        <CardSkeleton lines={4} />
      </div>
    );
  }

  // ── Rich Analysis Display ──
  if (!profile) return null;
  // Safe defaults for fields that may not exist in older analysis data
  const p: ResumeProfile = {
    tech_stack: profile.tech_stack || [],
    level: profile.level || "未知",
    domains: profile.domains || [],
    gaps: profile.gaps || [],
    highlights: profile.highlights || [],
    years_of_experience: profile.years_of_experience || 0,
    overall_score: profile.overall_score || 0,
    strengths: profile.strengths || [],
    weaknesses: profile.weaknesses || [],
    learning_path: profile.learning_path || [],
    recommended_topics: profile.recommended_topics || [],
    keywords: profile.keywords || [],
  };

  return (
    <div className="smooth-scroll" style={{ maxWidth: "var(--content-max-width)", margin: "0 auto", width: "100%", padding: "24px 16px" }}>
      <div className="animate-fade-in-up" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Header: Score + Info */}
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          {p.overall_score > 0 && <ScoreCircle score={p.overall_score} />}
          <InfoCard profile={p} />
        </div>

        {/* Strengths & Weaknesses */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <SectionCard title="主要优势" icon="✅" items={p.strengths} color="var(--success)" />
          <SectionCard title="待加强" icon="📈" items={p.weaknesses} color="var(--warning)" />
        </div>

        {/* Domains & Gaps */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <TagList title="🎯 专长领域" items={p.domains} variant="primary" />
          <TagList title="🕳️ 知识盲区" items={p.gaps} variant="warning" />
        </div>

        {/* Highlights */}
        <SectionCard title="项目亮点" icon="🌟" items={p.highlights} />

        {/* Learning Path */}
        <SectionCard title="学习建议" icon="📚" items={p.learning_path} color="var(--info)" />

        {/* Keywords */}
        {p.keywords.length > 0 && (
          <div className="card-base" style={{ padding: 16 }}>
            <div className="section-title">🔑 核心技术关键词</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {p.keywords.map((kw, i) => (
                <span key={i} className="tag" style={{ background: kw.weight > 0.7 ? "var(--primary-soft)" : "var(--card-hover)", color: kw.weight > 0.7 ? "var(--primary-text)" : "var(--text-secondary)" }}>
                  {kw.term}
                  <span style={{ fontSize: "0.65rem", marginLeft: 4, opacity: 0.6 }}>({Math.round(kw.weight * 100)}%)</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Start Interview CTA */}
        <div className="card-base" style={{ padding: 20, border: "2px dashed var(--primary)", background: "var(--primary-soft)", textAlign: "center" }}>
          <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--primary-text)", marginBottom: 6 }}>🎯 准备面试</div>
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", margin: "0 0 12px" }}>
            基于简历分析结果，开启一场个性化的多 Agent 模拟面试
            {p.recommended_topics.length > 0 && `（推荐主题：${p.recommended_topics.slice(0, 2).join("、")}）`}
          </p>
          <button onClick={handleStartInterview} disabled={startInterviewMutation.isPending} className="btn-primary" style={{ padding: "12px 28px", fontSize: "0.95rem" }}>
            {startInterviewMutation.isPending ? "⏳ 面试准备中..." : "🎙️ 开始模拟面试"}
          </button>
        </div>

        {/* Raw data */}
        <details className="card-base" style={{ padding: 16 }}>
          <summary style={{ cursor: "pointer", fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 500 }}>📋 查看原始数据</summary>
          <pre style={{ marginTop: 12, fontSize: "0.78rem", color: "var(--text-secondary)", overflow: "auto", maxHeight: 300, lineHeight: 1.5 }}>{JSON.stringify(p, null, 2)}</pre>
        </details>
      </div>
    </div>
  );
}
