# ADR-002: LangChain 作为 LLM 抽象层

## 状态

✅ 已采纳 (2026-05-28)

## 背景

项目需要支持多个 LLM 供应商（DeepSeek、OpenAI、Anthropic、Ollama）。

## 方案对比

| 维度 | LangChain | 自定义抽象 | 直接 SDK |
|------|-----------|-----------|----------|
| 多供应商支持 | 内置 | 需手写 | 各 SDK 不同 |
| 学习成本 | 中等 | 低 | 低 |
| 接口稳定性 | 中 (API 变更) | 完全可控 | 供应商控制 |
| Streaming | 统一接口 | 需适配 | 各家不同 |

## 决策

选 **LangChain**，但加一层自己的 Agent 抽象。

## 理由

1. `ChatOpenAI` 统一了 OpenAI 兼容 API（DeepSeek/OpenAI/任何自定义 endpoint）
2. `invoke()` / `stream()` 统一接口让 Agent 无需关心底层供应商
3. 自己的 `BaseAgent` 作为第二层抽象，隔离 LangChain 依赖

## 后果

- 依赖 LangChain 版本（锁定了 `>=0.3.0`）
- 如果 LangChain 大版本变更，只需要改 `agents/base.py` 中的 `_raw_invoke()` 和 `_raw_stream()` 方法
- `core/llm.py` 作为底层工厂，更换框架只需修改这一个文件
