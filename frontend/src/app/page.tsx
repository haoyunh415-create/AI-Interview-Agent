"use client";

import { useState, useEffect } from "react";
import { useAppStore, LLM_PROVIDERS, type Mode } from "@/stores/appStore";
import { useChatStore } from "@/stores/chatStore";
import { useResumeStore } from "@/stores/resumeStore";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { useTheme } from "@/lib/theme";
import { useTranslation } from "@/i18n";
import { useKeyboardShortcuts } from "@/lib/useKeyboard";
import { ShortcutsModal } from "@/components/ui/shortcuts-modal";
import { ChatView } from "@/components/views/ChatView";
import { ResumeView } from "@/components/views/ResumeView";
import { InterviewView } from "@/components/views/InterviewView";
import { ReportView } from "@/components/views/ReportView";
import { BookmarksView } from "@/components/views/BookmarksView";
import { LoginView } from "@/components/views/LoginView";

/* ════════════════════════════════════════════
   Constants
   ════════════════════════════════════════════ */
interface SidebarItem {
  id: Mode;
  icon: string;
  label: string;
}

const SIDEBAR_ITEMS: SidebarItem[] = [
  { id: "chat", icon: "💬", label: "闲聊" },
  { id: "resume", icon: "📄", label: "简历" },
  { id: "interview", icon: "🎙️", label: "面试" },
  { id: "report", icon: "📊", label: "报告" },
  { id: "bookmarks", icon: "⭐", label: "收藏" },
];

const MODES: Mode[] = ["chat", "resume", "interview", "report", "bookmarks"];
const MODES_REQUIRING_KEY: Mode[] = ["chat", "resume", "interview", "report"];

/* ════════════════════════════════════════════
   Sidebar Component
   ════════════════════════════════════════════ */
function Sidebar({ onShowShortcuts }: { onShowShortcuts: () => void }) {
  const mode = useAppStore((s) => s.mode);
  const setMode = useAppStore((s) => s.setMode);
  const configOpen = useAppStore((s) => s.configOpen);
  const setConfigOpen = useAppStore((s) => s.setConfigOpen);
  const apiKey = useAppStore((s) => s.apiKey);
  const setApiKey = useAppStore((s) => s.setApiKey);
  const provider = useAppStore((s) => s.provider);
  const setProvider = useAppStore((s) => s.setProvider);
  const model = useAppStore((s) => s.model);
  const setModel = useAppStore((s) => s.setModel);
  const serverHasKey = useAppStore((s) => s.serverHasKey);
  const configLoaded = useAppStore((s) => s.configLoaded);
  const username = useAppStore((s) => s.username);
  const logout = useAppStore((s) => s.logout);
  const setText = useResumeStore((s) => s.setText);
  const resumeText = useResumeStore((s) => s.text);
  const { theme, toggle } = useTheme();
  const { t, locale, setLocale } = useTranslation();

  return (
    <aside
      className="sidebar-desktop flex-col"
      style={{
        width: "var(--sidebar-width)",
        background: "var(--sidebar)",
        borderRight: "1px solid var(--border)",
        flexShrink: 0,
        zIndex: 10,
      }}
    >
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-title">AI 面试助手</div>
        <div className="logo-sub">
          由 {LLM_PROVIDERS.find(p => p.value === provider)?.label || provider} 驱动
        </div>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        {SIDEBAR_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => setMode(item.id)}
            className={`sidebar-link ${mode === item.id ? "active" : ""}`}
          >
            <div className="indicator" />
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Theme toggle */}
      <div className="sidebar-section">
        <button
          onClick={toggle}
          className="btn-ghost btn-ghost-full"
          title={theme === "dark" ? t("common.switch_theme_light") : t("common.switch_theme_dark")}
        >
          <span>{theme === "dark" ? "☀️" : "🌙"}</span>
          <span>{theme === "dark" ? t("common.theme_light") : t("common.theme_dark")}</span>
        </button>
      </div>

      {/* Language toggle */}
      <div className="sidebar-section">
        <button
          onClick={() => setLocale(locale === "zh-CN" ? "en-US" : "zh-CN")}
          className="btn-ghost btn-ghost-full"
          style={{ fontSize: "0.82rem" }}
        >
          <span>🌐</span>
          <span>{locale === "zh-CN" ? "英文" : "中文"}</span>
        </button>
      </div>

      {/* User + Logout */}
      <div className="sidebar-section">
        <button
          onClick={() => logout()}
          className="btn-ghost btn-ghost-full"
          style={{ fontSize: "0.82rem" }}
        >
          <span>👤</span>
          <span>{username}</span>
          <span className="text-muted" style={{ marginLeft: "auto", fontSize: "0.7rem" }}>
            退出
          </span>
        </button>
      </div>

      {/* Settings */}
      <div style={{ padding: "8px", borderTop: "1px solid var(--border)" }}>
        <button
          onClick={() => setConfigOpen(!configOpen)}
          className="btn-ghost"
          style={{ width: "100%", justifyContent: "flex-start" }}
        >
          <span>⚙️</span>
          <span>设置</span>
        </button>

        {configOpen && (
          <div className="animate-fade-in" style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 8, padding: "4px 0" }}>
            {!configLoaded ? (
              <div style={{ fontSize: "0.78rem", color: "var(--text-dim)", padding: "4px 0" }}>
                正在获取服务器配置...
              </div>
            ) : !serverHasKey ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                <label style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: 500 }}>
                  API 密钥
                </label>
                <input
                  placeholder="sk-..."
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="input-base"
                  style={{ padding: "8px 10px", fontSize: "0.82rem" }}
                />
              </div>
            ) : (
              <div style={{ fontSize: "0.78rem", color: "var(--primary-text)", padding: "4px 0" }}>
                🔑 服务端已配置 API 密钥，无需手动填写
              </div>
            )}
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <label style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: 500 }}>
                LLM 供应商
              </label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value as any)}
                className="input-base"
                style={{ padding: "8px 10px", fontSize: "0.82rem", cursor: "pointer" }}
              >
                {LLM_PROVIDERS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <label style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: 500 }}>
                模型名称
              </label>
              <input
                placeholder="deepseek-chat"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="input-base"
                style={{ padding: "8px 10px", fontSize: "0.82rem" }}
              />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <label style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: 500 }}>
                简历文本
              </label>
              <textarea
                placeholder="粘贴简历文本..."
                value={resumeText}
                onChange={(e) => setText(e.target.value)}
                rows={4}
                className="input-base"
                style={{ padding: "8px 10px", fontSize: "0.82rem", resize: "vertical" }}
              />
            </div>
          </div>
        )}

        {/* Keyboard shortcuts hint */}
        <button
          onClick={onShowShortcuts}
          className="btn-ghost"
          style={{ width: "100%", justifyContent: "flex-start", marginTop: 4, fontSize: "0.78rem" }}
        >
          <span>⌨️</span>
          <span>快捷键</span>
        </button>
      </div>
    </aside>
  );
}

/* ════════════════════════════════════════════
   Mobile Nav
   ════════════════════════════════════════════ */
function MobileNav() {
  const mode = useAppStore((s) => s.mode);
  const setMode = useAppStore((s) => s.setMode);
  const configOpen = useAppStore((s) => s.configOpen);
  const setConfigOpen = useAppStore((s) => s.setConfigOpen);
  const { theme, toggle } = useTheme();
  const { t, locale, setLocale } = useTranslation();
  const logout = useAppStore((s) => s.logout);
  const username = useAppStore((s) => s.username);

  const [showExtra, setShowExtra] = useState(false);

  return (
    <nav
      className="mobile-nav"
      style={{
        position: "fixed",
        bottom: 0,
        left: 0,
        right: 0,
        background: "var(--sidebar)",
        borderTop: "1px solid var(--border)",
        display: "none",
        justifyContent: "space-around",
        padding: "6px 0 env(safe-area-inset-bottom)",
        zIndex: 100,
      }}
    >
      {SIDEBAR_ITEMS.map((item) => (
        <button
          key={item.id}
          onClick={() => setMode(item.id)}
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 2,
            padding: "6px 12px",
            border: "none",
            background: "transparent",
            color: mode === item.id ? "var(--primary-text)" : "var(--text-muted)",
            fontSize: "0.65rem",
            cursor: "pointer",
            fontWeight: mode === item.id ? 600 : 400,
            transition: "color 0.15s",
          }}
        >
          <span style={{ fontSize: "1.2rem" }}>{item.icon}</span>
          <span>{item.label}</span>
        </button>
      ))}

      {/* More button: opens extra options */}
      <button
        onClick={() => setShowExtra(!showExtra)}
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 2,
          padding: "6px 12px",
          border: "none",
          background: "transparent",
          color: showExtra ? "var(--primary-text)" : "var(--text-muted)",
          fontSize: "0.65rem",
          cursor: "pointer",
        }}
      >
        <span style={{ fontSize: "1.2rem" }}>⚙️</span>
        <span>更多</span>
      </button>

      {/* Extra settings panel */}
      {showExtra && (
        <div
          style={{
            position: "absolute",
            bottom: "100%",
            left: 0,
            right: 0,
            background: "var(--sidebar)",
            borderTop: "1px solid var(--border)",
            borderBottom: "1px solid var(--border)",
            padding: "8px 12px",
            display: "flex",
            flexWrap: "wrap",
            gap: 6,
            justifyContent: "center",
          }}
        >
          <button onClick={toggle} className="btn-ghost btn-sm">
            {theme === "dark" ? "☀️" : "🌙"} {theme === "dark" ? t("common.theme_light") : t("common.theme_dark")}
          </button>
          <button onClick={() => setLocale(locale === "zh-CN" ? "en-US" : "zh-CN")} className="btn-ghost btn-sm">
            🌐 {locale === "zh-CN" ? "英文" : "中文"}
          </button>
          <button onClick={() => { setConfigOpen(!configOpen); setShowExtra(false); }} className="btn-ghost btn-sm">
            ⚙️ 设置
          </button>
          <button onClick={() => logout()} className="btn-danger btn-sm">
            👤 {username} · 退出
          </button>
          <button onClick={() => setShowExtra(false)} className="btn-ghost btn-sm">
            ✕ 关闭
          </button>
        </div>
      )}
    </nav>
  );
}

/* ════════════════════════════════════════════
   Loading / API Key Required Banners
   ════════════════════════════════════════════ */
function LoadingBanner() {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        gap: 12,
        color: "var(--text-muted)",
        fontSize: "0.9rem",
      }}
    >
      <div className="typing-dots" style={{ fontSize: "2rem" }}>
        <span>.</span><span>.</span><span>.</span>
      </div>
      <div>正在连接服务器...</div>
    </div>
  );
}

function ApiKeyBanner() {
  return (
    <div
      className="animate-fade-in"
      style={{
        textAlign: "center",
        padding: "40px 16px",
        color: "var(--text-muted)",
        fontSize: "0.9rem",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
        justifyContent: "center",
        height: "100%",
      }}
    >
      <div style={{ fontSize: "2.5rem", opacity: 0.4 }}>🔑</div>
      <div>请先点击左下角 ⚙️ 配置 API 密钥</div>
    </div>
  );
}

/* ════════════════════════════════════════════
   Main Content Router
   ════════════════════════════════════════════ */
function MainContent() {
  const mode = useAppStore((s) => s.mode);
  const apiKey = useAppStore((s) => s.apiKey);
  const serverHasKey = useAppStore((s) => s.serverHasKey);
  const configLoaded = useAppStore((s) => s.configLoaded);

  // Still checking server config — show loading instead of API key banner
  if (!configLoaded) {
    return <LoadingBanner />;
  }

  // Only require API key when the server doesn't have one configured
  if (!serverHasKey && !apiKey && MODES_REQUIRING_KEY.includes(mode)) {
    return <ApiKeyBanner />;
  }

  // Wrap each view in its own ErrorBoundary so one crash
  // doesn't take down the entire main content area.
  switch (mode) {
    case "chat":
      return <ErrorBoundary><ChatView /></ErrorBoundary>;
    case "resume":
      return <ErrorBoundary><ResumeView /></ErrorBoundary>;
    case "interview":
      return <ErrorBoundary><InterviewView /></ErrorBoundary>;
    case "report":
      return <ErrorBoundary><ReportView /></ErrorBoundary>;
    case "bookmarks":
      return <ErrorBoundary><BookmarksView /></ErrorBoundary>;
    default:
      return null;
  }
}

/* ════════════════════════════════════════════
   Home — App Shell
   ════════════════════════════════════════════ */
export default function Home() {
  const isLoggedIn = useAppStore((s) => s.isLoggedIn);
  const serverHasKey = useAppStore((s) => s.serverHasKey);
  const setServerHasKey = useAppStore((s) => s.setServerHasKey);
  const setApiKey = useAppStore((s) => s.setApiKey);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const setMode = useAppStore((s) => s.setMode);
  const setConfigOpen = useAppStore((s) => s.setConfigOpen);
  const setConfigLoaded = useAppStore((s) => s.setConfigLoaded);

  // Fetch server config on mount — retry if backend isn't ready yet
  useEffect(() => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765/api";
    let cancelled = false;

    const fetchConfig = (retries: number) => {
      fetch(`${API_BASE}/config`)
        .then((r) => r.json())
        .then((cfg) => {
          if (cancelled) return;
          if (cfg.server_has_key) {
            setServerHasKey(true);
            setApiKey("");
          }
          setConfigLoaded(true);
        })
        .catch(() => {
          if (cancelled) return;
          if (retries > 0) {
            // Backend may still be starting — retry after 1s
            setTimeout(() => fetchConfig(retries - 1), 1000);
          } else {
            // Backend unreachable — let user provide key manually
            setConfigLoaded(true);
          }
        });
    };

    fetchConfig(5); // retry up to 5 times (5 seconds)

    return () => { cancelled = true; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Keyboard shortcuts (must be called before any early return — Rules of Hooks)
  useKeyboardShortcuts([
    // Ctrl+1..5 → switch modes
    ...MODES.map((m, i) => ({
      key: String(i + 1),
      ctrl: true,
      handler: () => setMode(m),
      label: `切换${SIDEBAR_ITEMS[i].label}模式`,
    })),
    // Escape → close settings
    {
      key: "Escape",
      handler: () => setConfigOpen(false),
      label: "关闭设置",
    },
    // ? → show shortcuts help
    {
      key: "?",
      handler: () => setShowShortcuts(true),
      label: "显示快捷键帮助",
    },
  ]);

  // Auth gate
  if (!isLoggedIn) {
    return <LoginView />;
  }

  return (
    <>
      <ShortcutsModal
        open={showShortcuts}
        onClose={() => setShowShortcuts(false)}
      />
      <div
        style={{
          display: "flex",
          height: "100vh",
          background: "var(--bg)",
          overflow: "hidden",
        }}
      >
        <Sidebar onShowShortcuts={() => setShowShortcuts(true)} />
        <MobileNav />
        <main
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            background: "var(--bg)",
            paddingBottom: "env(safe-area-inset-bottom)",
          }}
        >
          <MainContent />
        </main>
      </div>
    </>
  );
}
