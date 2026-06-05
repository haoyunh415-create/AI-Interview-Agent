"use client";

interface WelcomeScreenProps {
  onSuggestionClick: (text: string) => void;
}

const suggestions = [
  { icon: "🤖", text: "什么是 Transformer 的 Self-Attention 机制？" },
  { icon: "🔄", text: "解释一下 Backpropagation 的工作原理" },
  { icon: "⚡", text: "如何优化大模型的推理速度？" },
  { icon: "📊", text: "PyTorch 和 TensorFlow 的主要区别" },
];

export function WelcomeScreen({ onSuggestionClick }: WelcomeScreenProps) {
  return (
    <div
      className="empty-state animate-fade-in"
      style={{ padding: "80px 20px" }}
    >
      {/* Icon with glow */}
      <div
        style={{
          fontSize: "3rem",
          marginBottom: 8,
          position: "relative",
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: -10,
            borderRadius: "50%",
            background: "var(--primary-glow)",
            filter: "blur(20px)",
            opacity: 0.5,
          }}
        />
        <span style={{ position: "relative" }}>💬</span>
      </div>

      <h2
        style={{
          fontSize: "1.2rem",
          fontWeight: 600,
          color: "var(--fg)",
          margin: 0,
        }}
      >
        AI 面试助手
      </h2>
      <p
        style={{
          color: "var(--text-muted)",
          fontSize: "0.88rem",
          margin: "4px 0 24px",
          maxWidth: 360,
          lineHeight: 1.6,
        }}
      >
        可以和我闲聊技术话题、准备面试、分析简历或获取学习报告
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <div
          style={{
            fontSize: "0.78rem",
            color: "var(--text-muted)",
            textAlign: "center",
            marginBottom: 4,
          }}
        >
          试试这些提问 💡
        </div>
        {suggestions.map((s, i) => (
          <button
            key={i}
            onClick={() => onSuggestionClick(s.text)}
            className="animate-slide-in-up"
            style={{
              animationDelay: `${i * 80}ms`,
              animationFillMode: "backwards",
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "10px 16px",
              background: "var(--card)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
              color: "var(--text-secondary)",
              fontSize: "0.88rem",
              cursor: "pointer",
              transition: "all 0.2s ease",
              minWidth: 340,
              textAlign: "left",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--primary)";
              e.currentTarget.style.background = "var(--primary-soft)";
              e.currentTarget.style.color = "var(--fg)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--border)";
              e.currentTarget.style.background = "var(--card)";
              e.currentTarget.style.color = "var(--text-secondary)";
            }}
          >
            <span style={{ fontSize: "1rem" }}>{s.icon}</span>
            <span>{s.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
