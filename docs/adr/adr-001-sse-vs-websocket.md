# ADR-001: SSE 而非 WebSocket 用于流式评分

## 状态

✅ 已采纳 (2026-05-28)

## 背景

面试评分需要实时展示 LLM 逐 token 输出，不能等整个响应完成再一次性展示。

## 方案对比

| 维度 | SSE (Server-Sent Events) | WebSocket |
|------|-------------------------|-----------|
| 通信方向 | 服务端→客户端单向 | 双向 |
| 协议 | HTTP 长连接 | 独立 TCP 连接 |
| 自动重连 | 浏览器原生支持 (`EventSource`) | 需手动实现 |
| 负载均衡兼容性 | 完全兼容 (HTTP) | 需特殊配置 (sticky session) |
| 消息格式 | 纯文本 `data:` 行 | 自定义二进制/文本帧 |
| 适用场景 | 推送通知、流式响应 | 实时双向通信 (游戏、IM) |

## 决策

选 **SSE**。

## 理由

1. **面试场景是单向流** — 只有服务端需要向客户端推送 token，客户端不需要实时上行
2. **浏览器原生 SSE** — `EventSource` 自动重连，减少前端代码量
3. **HTTP 兼容** — Nginx/Caddy/CDN 无需特殊配置，适合生产部署
4. **监控友好** — 请求以正常 HTTP 形式出现在日志中，调试方便

## 后果

- 前端用 `fetch + ReadableStream` 消费 SSE（比原生 EventSource 更灵活，支持 POST 请求）
- 不支持 IE（已 EOL，可接受）
- Nginx 需要关闭 `proxy_buffering` 确保实时性（已在 DEPLOYMENT.md 中说明）
