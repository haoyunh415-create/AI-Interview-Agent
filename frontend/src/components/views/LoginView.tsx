"use client";

import { useState, useCallback } from "react";
import toast from "react-hot-toast";
import { useMutation } from "@tanstack/react-query";
import { login, register } from "@/lib/api";
import { useAppStore } from "@/stores/appStore";

export function LoginView() {
  const loginFn = useAppStore((s) => s.login);

  const [tab, setTab] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");

  const loginMutation = useMutation({
    mutationFn: () => login({ username, password }),
    onSuccess: (res) => {
      loginFn(res.access_token, res.username);
      toast.success(`欢迎回来, ${res.display_name}!`);
    },
    onError: (e: Error) => toast.error(`登录失败: ${e.message}`),
  });

  const registerMutation = useMutation({
    mutationFn: () => register({ username, password, display_name: displayName || username }),
    onSuccess: (res) => {
      loginFn(res.access_token, res.username);
      toast.success(`注册成功! 欢迎, ${res.display_name}!`);
    },
    onError: (e: Error) => toast.error(`注册失败: ${e.message}`),
  });

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (!username.trim() || !password.trim()) return;
      if (tab === "login") loginMutation.mutate();
      else registerMutation.mutate();
    },
    [tab, username, password, loginMutation, registerMutation],
  );

  const isPending = loginMutation.isPending || registerMutation.isPending;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        background: "var(--bg)",
        padding: 24,
      }}
    >
      <div
        className="card-base animate-fade-in-up"
        style={{
          width: "100%",
          maxWidth: 400,
          padding: "32px 28px",
        }}
      >
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div style={{ fontSize: "2rem", marginBottom: 8 }}>🎯</div>
          <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--fg)" }}>
            AI 面试助手
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: 4 }}>
            登录以同步你的面试数据
          </div>
        </div>

        {/* Tab */}
        <div
          style={{
            display: "flex",
            gap: 0,
            marginBottom: 24,
            borderRadius: "var(--radius-sm)",
            overflow: "hidden",
            border: "1px solid var(--border)",
          }}
        >
          <button
            onClick={() => setTab("login")}
            style={{
              flex: 1,
              padding: "10px 0",
              border: "none",
              cursor: "pointer",
              fontSize: "0.9rem",
              fontWeight: tab === "login" ? 600 : 400,
              background: tab === "login" ? "var(--primary)" : "transparent",
              color: tab === "login" ? "#fff" : "var(--text-secondary)",
              transition: "all 0.15s",
            }}
          >
            登录
          </button>
          <button
            onClick={() => setTab("register")}
            style={{
              flex: 1,
              padding: "10px 0",
              border: "none",
              cursor: "pointer",
              fontSize: "0.9rem",
              fontWeight: tab === "register" ? 600 : 400,
              background: tab === "register" ? "var(--primary)" : "transparent",
              color: tab === "register" ? "#fff" : "var(--text-secondary)",
              transition: "all 0.15s",
            }}
          >
            注册
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <input
              placeholder="用户名（至少3个字符）"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-base"
              style={{ padding: "12px 14px", fontSize: "0.9rem" }}
              autoFocus
            />
            {tab === "register" && username.length > 0 && username.length < 3 && (
              <div style={{ fontSize: "0.72rem", color: "var(--warning)", marginTop: 4, paddingLeft: 2 }}>
                用户名至少 3 个字符
              </div>
            )}
          </div>
          {tab === "register" && (
            <input
              placeholder="显示名称（可选）"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="input-base"
              style={{ padding: "12px 14px", fontSize: "0.9rem" }}
            />
          )}
          <div>
            <input
              type="password"
              placeholder={tab === "register" ? "密码（至少6个字符）" : "密码"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-base"
              style={{ padding: "12px 14px", fontSize: "0.9rem" }}
            />
            {tab === "register" && password.length > 0 && password.length < 6 && (
              <div style={{ fontSize: "0.72rem", color: "var(--warning)", marginTop: 4, paddingLeft: 2 }}>
                密码至少 6 个字符
              </div>
            )}
          </div>
          <button
            type="submit"
            disabled={isPending || !username.trim() || !password.trim()}
            className="btn-primary"
            style={{ padding: "12px 0", fontSize: "0.95rem" }}
          >
            {isPending ? "处理中..." : tab === "login" ? "登录" : "注册并登录"}
          </button>
        </form>

        {/* Skip */}
        <div style={{ textAlign: "center", marginTop: 20 }}>
          <button
            onClick={() => loginFn("", "guest")}
            className="btn-ghost"
            style={{ fontSize: "0.8rem", padding: "6px 14px" }}
          >
            跳过，以游客身份使用
          </button>
        </div>
      </div>
    </div>
  );
}
