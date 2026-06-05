"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import toast from "react-hot-toast";
import { chatStream } from "@/lib/api";
import { useAppStore } from "@/stores/appStore";
import { useChatStore, useActiveMessages, useActiveSession } from "@/stores/chatStore";
import { ChatMessage } from "@/components/ui/chat-message";
import { WelcomeScreen } from "@/components/ui/welcome-screen";
import { VirtualList } from "@/components/ui/virtual-list";
import { useTranslation } from "@/i18n";

interface ImageAttachment {
  id: string;
  dataUrl: string;
  name: string;
}

const VIRTUAL_THRESHOLD = 40;
const SIDEBAR_WIDTH = 280;

export function ChatView() {
  const apiKey = useAppStore((s) => s.apiKey);
  const provider = useAppStore((s) => s.provider);
  const model = useAppStore((s) => s.model);
  const { t } = useTranslation();

  // Sessions
  const sessions = useChatStore((s) => s.sessions);
  const activeSessionId = useChatStore((s) => s.activeSessionId);
  const createSession = useChatStore((s) => s.createSession);
  const deleteSession = useChatStore((s) => s.deleteSession);
  const switchSession = useChatStore((s) => s.switchSession);
  const activeSession = useActiveSession();
  const messages = useActiveMessages();

  const input = useChatStore((s) => s.input);
  const loading = useChatStore((s) => s.loading);
  const streamingContent = useChatStore((s) => s.streamingContent);
  const setInput = useChatStore((s) => s.setInput);
  const addMessage = useChatStore((s) => s.addMessage);
  const appendToLastMessage = useChatStore((s) => s.appendToLastMessage);
  const popLastMessage = useChatStore((s) => s.popLastMessage);
  const setLoading = useChatStore((s) => s.setLoading);

  const [isStreaming, setIsStreaming] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);

  const chatInputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const scrollAnchorRef = useRef<HTMLDivElement>(null);
  const prevCountRef = useRef(messages.length);

  const [images, setImages] = useState<ImageAttachment[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [dragCounter, setDragCounter] = useState(0);
  const [atBottom, setAtBottom] = useState(true);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);

  // Detect mobile on mount + resize
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    addEventListener("resize", check);
    return () => removeEventListener("resize", check);
  }, []);

  // Auto-close sidebar on mobile, open on desktop
  useEffect(() => {
    setSidebarOpen(!isMobile);
  }, [isMobile]);

  // Auto-scroll to bottom when new messages arrive (only if already at bottom)
  useEffect(() => {
    if (messages.length > prevCountRef.current && atBottom) {
      scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
    }
    prevCountRef.current = messages.length;
  }, [messages, atBottom]);

  // Track scroll position
  useEffect(() => {
    const el = scrollContainerRef.current;
    if (!el) return;
    const handleScroll = () => {
      const threshold = 100;
      setAtBottom(el.scrollHeight - el.scrollTop - el.clientHeight < threshold);
    };
    el.addEventListener("scroll", handleScroll, { passive: true });
    return () => el.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const el = chatInputRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 160) + "px";
    }
  }, [input]);

  /* ── Streaming send ── */
  const sendStreamMessage = useCallback(
    (userMsg: string) => {
      setIsStreaming(true);
      setLoading(true);

      const currentMessages = useChatStore.getState().sessions
        .find((s) => s.id === useChatStore.getState().activeSessionId)
        ?.messages ?? [];

      chatStream(
        {
          message: userMsg,
          api_key: apiKey,
          provider,
          model,
          history: currentMessages.slice(-10).map((m) => ({ role: m.role, content: m.content })),
        },
        (chunk) => appendToLastMessage(chunk),
        () => { setIsStreaming(false); setReconnecting(false); setLoading(false); },
        (err) => {
          setIsStreaming(false);
          setReconnecting(false);
          setLoading(false);
          popLastMessage();
          addMessage({ role: "assistant", content: `请求失败: ${err.message}` });
          toast.error(t("chat.request_failed", { message: err.message }));
        },
        2,
        (attempt) => setReconnecting(true),
      );
    },
    [apiKey, provider, model, addMessage, appendToLastMessage, popLastMessage, setLoading, t],
  );

  const handleRetry = useCallback(() => {
    const lastMsg = messages[messages.length - 1];
    if (!lastMsg || lastMsg.role !== "assistant") return;
    popLastMessage();
    const userMsgs = messages.filter((m) => m.role === "user");
    if (userMsgs.length > 0) setInput(userMsgs[userMsgs.length - 1].content);
  }, [messages, popLastMessage, setInput]);

  const handleCopy = useCallback((text: string) => {
    navigator.clipboard.writeText(text).catch(() => {});
  }, []);

  const handleSend = useCallback(() => {
    if ((!input.trim() && images.length === 0) || isStreaming) return;
    let msg = input.trim();
    if (images.length > 0) {
      const imgInfo = images.map((img) => `[图片: ${img.name}]`).join("\n");
      msg = msg ? `${imgInfo}\n\n${msg}` : imgInfo;
    }
    setInput("");
    setImages([]);
    addMessage({ role: "user", content: msg || "(图片)" });
    sendStreamMessage(msg || "请描述我发送的图片");
  }, [input, images, isStreaming, setInput, addMessage, sendStreamMessage]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
    }, [handleSend],
  );

  const handleSuggestionClick = useCallback(
    (text: string) => {
      setInput(text);
      setTimeout(() => chatInputRef.current?.focus(), 100);
    }, [setInput],
  );

  const handleNewChat = useCallback(() => {
    createSession();
    // Close sidebar on mobile after creating
    if (isMobile) setSidebarOpen(false);
    setTimeout(() => chatInputRef.current?.focus(), 50);
  }, [createSession, isMobile]);

  const handleDeleteSession = useCallback(
    (e: React.MouseEvent, id: string) => {
      e.stopPropagation();
      const s = sessions.find((s) => s.id === id);
      const label = s?.title || t("chat.new_chat");
      if (!confirm(t("chat.delete_confirm", { title: label }))) return;
      deleteSession(id);
      toast.success(t("chat.deleted"));
    }, [sessions, deleteSession, t],
  );

  /* ── Image handling ── */
  const addImagesFromFileList = useCallback((files: FileList | File[]) => {
    const valid: ImageAttachment[] = [];
    for (const file of Array.from(files)) {
      if (!file.type.startsWith("image/")) {
        toast.error(t("chat.file_type_unsupported", { name: file.name })); continue;
      }
      if (file.size > 10 * 1024 * 1024) {
        toast.error(t("chat.file_too_large", { name: file.name })); continue;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        valid.push({ id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`, dataUrl: e.target?.result as string, name: file.name });
        if (valid.length === 1 || valid.length === Array.from(files).filter(f => f.type.startsWith("image/") && f.size <= 10 * 1024 * 1024).length) {
          setImages((prev) => [...prev, ...valid]);
        }
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    const imageFiles: File[] = [];
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.startsWith("image/")) {
        const file = items[i].getAsFile();
        if (file) imageFiles.push(file);
      }
    }
    if (imageFiles.length > 0) {
      e.preventDefault();
      addImagesFromFileList(imageFiles);
      toast.success(t("chat.image_paste", { count: imageFiles.length }));
    }
  }, [addImagesFromFileList, t]);

  const handleDragEnter = useCallback((e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setDragCounter((c) => c + 1); setIsDragging(true); }, []);
  const handleDragLeave = useCallback((e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setDragCounter((c) => c - 1); if (dragCounter <= 1) setIsDragging(false); }, [dragCounter]);
  const handleDragOver = useCallback((e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); }, []);
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation(); setIsDragging(false); setDragCounter(0);
    if (e.dataTransfer.files.length > 0) {
      addImagesFromFileList(e.dataTransfer.files);
      toast.success(t("chat.image_added", { count: e.dataTransfer.files.length }));
    }
  }, [addImagesFromFileList, t]);
  const removeImage = useCallback((id: string) => setImages((prev) => prev.filter((img) => img.id !== id)), []);

  const isSessionEmpty = !activeSession || activeSession.messages.length === 0;

  return (
    <div style={{ display: "flex", height: "100%", width: "100%", position: "relative" }}>
      {/* ── Session Sidebar ── */}
      <div
        className="animate-slide-in-left"
        style={{
          width: sidebarOpen ? SIDEBAR_WIDTH : 0,
          minWidth: sidebarOpen ? SIDEBAR_WIDTH : 0,
          overflow: "hidden",
          background: "var(--sidebar)",
          borderRight: sidebarOpen ? "1px solid var(--border)" : "none",
          display: "flex",
          flexDirection: "column",
          transition: "width 0.2s ease, min-width 0.2s ease, border 0.2s ease",
          flexShrink: 0,
          zIndex: 20,
          position: isMobile ? "absolute" as const : "relative",
          left: 0,
          top: 0,
          bottom: 0,
          boxShadow: isMobile && sidebarOpen ? "var(--shadow-lg)" : "none",
        }}
      >
        {/* New Chat button */}
        <div style={{ padding: "12px 12px 8px" }}>
          <button
            onClick={handleNewChat}
            style={{
              width: "100%",
              padding: "10px 0",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--border)",
              background: "transparent",
              color: "var(--fg)",
              cursor: "pointer",
              fontSize: "0.85rem",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 6,
              transition: "background 0.15s",
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = "var(--card-hover)"}
            onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
          >
            <span style={{ fontSize: "1.1rem", lineHeight: 1 }}>+</span>
            <span>{t("chat.new_chat")}</span>
          </button>
        </div>

        {/* Session list */}
        <div
          className="smooth-scroll"
          style={{ flex: 1, overflow: "auto", padding: "4px 8px" }}
        >
          {[...sessions].reverse().map((s) => {
            const isActive = s.id === activeSessionId;
            return (
              <div
                key={s.id}
                onClick={() => {
                  switchSession(s.id);
                  if (isMobile) setSidebarOpen(false);
                }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "8px 10px",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  marginBottom: 2,
                  background: isActive ? "var(--card-hover)" : "transparent",
                  transition: "background 0.12s",
                }}
                onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = "var(--card-hover)"; }}
                onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = "transparent"; }}
              >
                <span style={{ fontSize: "0.75rem", flexShrink: 0, opacity: 0.5 }}>💬</span>
                <span
                  style={{
                    flex: 1,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    fontSize: "0.82rem",
                    color: isActive ? "var(--fg)" : "var(--text-secondary)",
                    fontWeight: isActive ? 500 : 400,
                  }}
                >
                  {s.title}
                </span>
                {/* Delete — show on hover via opacity */}
                <span
                  onClick={(e) => handleDeleteSession(e, s.id)}
                  style={{
                    fontSize: "0.65rem",
                    opacity: 0,
                    cursor: "pointer",
                    padding: "2px 6px",
                    borderRadius: "var(--radius-sm)",
                    color: "var(--text-dim)",
                    flexShrink: 0,
                    transition: "opacity 0.12s, background 0.12s",
                  }}
                  className="delete-btn"
                  title={t("chat.delete_tooltip")}
                >
                  ✕
                </span>
              </div>
            );
          })}
        </div>

        {/* Bottom hint */}
        <div style={{ padding: "8px 12px", borderTop: "1px solid var(--border)" }}>
          <div style={{ fontSize: "0.68rem", color: "var(--text-dim)", textAlign: "center" }}>
            {sessions.length} 个对话
          </div>
        </div>
      </div>

      {/* ── Chat Area ── */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
          position: "relative",
        }}
        onDragEnter={handleDragEnter}
      >
        {/* Top bar */}
        {sidebarOpen && isMobile && (
          <div
            onClick={() => setSidebarOpen(false)}
            style={{
              position: "fixed", inset: 0, zIndex: 19, background: "rgba(0,0,0,0.3)",
            }}
          />
        )}

        {/* Header with hamburger */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "8px 16px",
            borderBottom: "1px solid var(--border)",
            flexShrink: 0,
          }}
        >
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            style={{
              width: 34, height: 34,
              borderRadius: "var(--radius-md)",
              border: "none",
              background: "transparent",
              color: "var(--text-secondary)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.2rem",
              flexShrink: 0,
              transition: "background 0.12s",
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = "var(--card-hover)"}
            onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
            title={sidebarOpen ? "收起侧栏" : "展开侧栏"}
          >
            {sidebarOpen ? "◁" : "☰"}
          </button>
          {activeSession && (
            <span
              style={{
                fontSize: "0.82rem",
                color: "var(--text-muted)",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {activeSession.title}
            </span>
          )}
        </div>

        {/* Drag overlay */}
        {isDragging && (
          <div
            onDragEnter={handleDragEnter} onDragLeave={handleDragLeave}
            onDragOver={handleDragOver} onDrop={handleDrop}
            style={{
              position: "absolute", inset: 0, zIndex: 200,
              display: "flex", alignItems: "center", justifyContent: "center",
              background: "rgba(16, 163, 127, 0.08)", backdropFilter: "blur(8px)",
              border: "2px dashed var(--primary)", borderRadius: "var(--radius-lg)",
              margin: 8, pointerEvents: "auto",
            }}
          >
            <div style={{ textAlign: "center", color: "var(--primary-text)", fontSize: "1rem", fontWeight: 500 }}>
              <div style={{ fontSize: "2.5rem", marginBottom: 8 }}>📁</div>
              释放以上传图片
            </div>
          </div>
        )}

        {/* Messages */}
        <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
          {isSessionEmpty && !isStreaming ? (
            <div className="smooth-scroll" style={{ flex: 1, padding: "8px 0" }}>
              <WelcomeScreen onSuggestionClick={handleSuggestionClick} />
            </div>
          ) : (
            <div
              ref={(el) => { scrollContainerRef.current = el; }}
              className="smooth-scroll"
              style={{ flex: 1, overflow: "auto", padding: "8px 0" }}
            >
              {messages.map((msg, i) => {
                const isLast = i === messages.length - 1;
                return (
                  <ChatMessage
                    key={i}
                    role={msg.role}
                    content={msg.content}
                    isLast={isLast && msg.role === "assistant"}
                    onRetry={isLast ? handleRetry : undefined}
                    onCopy={() => handleCopy(msg.content)}
                  />
                );
              })}
              {isStreaming && <ChatMessage role="assistant" content="" isLoading />}
              {reconnecting && (
                <div
                  className="animate-fade-in"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 8,
                    padding: "8px 16px",
                    fontSize: "0.78rem",
                    color: "var(--warning)",
                    background: "var(--warning-soft)",
                    borderRadius: "var(--radius-md)",
                    margin: "8px 0",
                  }}
                >
                  <span style={{
                    display: "inline-block",
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: "var(--warning)",
                    animation: "pulse 0.6s ease-in-out infinite",
                  }} />
                  连接中断，正在重连...
                </div>
              )}
              <div ref={scrollAnchorRef} />
            </div>
          )}
        </div>

        {/* Scroll to bottom button */}
        {messages.length >= VIRTUAL_THRESHOLD && !atBottom && (
          <button
            onClick={() => {
              const el = document.querySelector(".smooth-scroll");
              el?.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
              setAtBottom(true);
            }}
            style={{
              position: "absolute", bottom: 160, right: 24,
              width: 40, height: 40, borderRadius: "50%",
              border: "1px solid var(--border)", background: "var(--card)",
              color: "var(--text-secondary)", cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "1rem", boxShadow: "var(--shadow-md)", zIndex: 50,
            }}
            title={t("chat.scroll_to_bottom")}
          >
            ⬇
          </button>
        )}

        {/* Image preview strip */}
        {images.length > 0 && (
          <div style={{
            display: "flex", gap: 8, padding: "8px 16px", overflow: "auto",
            background: "var(--bg)", borderTop: "1px solid var(--border)",
          }}>
            {images.map((img) => (
              <div key={img.id} style={{
                position: "relative", width: 64, height: 64,
                borderRadius: "var(--radius-sm)", overflow: "hidden",
                border: "1px solid var(--border)", flexShrink: 0,
              }}>
                <img src={img.dataUrl} alt={img.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                <button onClick={() => removeImage(img.id)} style={{
                  position: "absolute", top: 2, right: 2, width: 18, height: 18,
                  borderRadius: "50%", border: "none", background: "rgba(0,0,0,0.7)",
                  color: "#fff", fontSize: "0.6rem", cursor: "pointer",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>✕</button>
              </div>
            ))}
            <span style={{ fontSize: "0.72rem", color: "var(--text-dim)", alignSelf: "center", whiteSpace: "nowrap" }}>
              {t("chat.images_count", { count: images.length })}
            </span>
          </div>
        )}

        {/* Input */}
        <div
          onDragEnter={handleDragEnter} onDragLeave={handleDragLeave}
          onDragOver={handleDragOver} onDrop={handleDrop}
          style={{ padding: "12px 16px 20px", borderTop: "1px solid var(--border)", background: "var(--bg)" }}
        >
          <div style={{ maxWidth: "var(--content-max-width)", margin: "0 auto", width: "100%", display: "flex", gap: 8, alignItems: "flex-end" }}>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="btn-ghost"
              style={{ width: 44, height: 44, padding: 0, borderRadius: "var(--radius-md)", fontSize: "1.1rem", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center" }}
              title={t("chat.attach_image")}
            >📎</button>
            <input ref={fileInputRef} type="file" accept="image/*" multiple style={{ display: "none" }}
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  addImagesFromFileList(e.target.files);
                  toast.success(t("chat.images_selected", { count: e.target.files.length }));
                  e.target.value = "";
                }
              }}
            />
            <textarea
              ref={chatInputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              placeholder={t("chat.placeholder.with_image")}
              rows={1}
              className="input-base"
              style={{ flex: 1, padding: "12px 16px", borderRadius: "var(--radius-lg)", minHeight: 48, maxHeight: 160, lineHeight: 1.5, resize: "none", fontSize: "0.9rem" }}
            />
            <button
              onClick={handleSend}
              disabled={isStreaming || (!input.trim() && images.length === 0)}
              className="btn-primary"
              style={{ width: 48, height: 48, padding: 0, borderRadius: "var(--radius-md)", fontSize: "1.2rem", flexShrink: 0 }}
            >➤</button>
          </div>
          <div style={{ maxWidth: "var(--content-max-width)", margin: "4px auto 0", fontSize: "0.7rem", color: "var(--text-dim)", textAlign: "right" }}>
            {t("chat.image_hint")}
          </div>
        </div>
      </div>

      {/* Hover-delete styles */}
      <style>{`
        .delete-btn {
          opacity: 0 !important;
        }
        div:hover > .delete-btn {
          opacity: 0.4 !important;
        }
        .delete-btn:hover {
          opacity: 1 !important;
          background: rgba(239,68,68,0.15) !important;
          color: rgb(239,68,68) !important;
        }
      `}</style>
    </div>
  );
}
