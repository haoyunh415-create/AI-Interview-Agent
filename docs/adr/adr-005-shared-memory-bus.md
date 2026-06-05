# ADR-005: SharedMemory + MessageBus 而非直接耦合

## 状态

✅ 已采纳 (2026-05-29)

## 背景

多智能体之间需要共享数据（简历分析结果、评分结果）和事件通知。

## 方案对比

| 维度 | SharedMemory + Bus | Orchestrator 传参 | Redis/消息队列 |
|------|-------------------|------------------|---------------|
| 实现复杂度 | 低 | 低 | 高 |
| Agent 耦合 | 松 | 紧 | 松 |
| 调试难度 | 中（可追踪事件） | 容易 | 难 |
| 外部依赖 | 无 | 无 | Redis |

## 决策

选 **SharedMemory + MessageBus**。

## 理由

1. **进程内通信** — 所有 Agent 在同一进程中运行，不需要网络消息队列
2. **事件溯源** — MessageBus 保留历史事件，Orchestrator 可以回放
3. **无外部依赖** — 内存存储，无额外运维成本
4. **可测试** — 单元测试可以直接检查 SharedMemory 状态

## 后果

- 状态不持久化（Orchestrator 崩溃丢失），已通过 `save_memory_data()` 定期持久化到 SQLite 缓解
- 不适合分布式部署（Agent 必须在同一进程）
