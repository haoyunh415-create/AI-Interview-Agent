# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [2.2.0] — 2026-06-02

### Added

- **用户认证系统** — JWT 注册/登录/个人信息 API，密码 SHA-256 + salt 哈希
- **LLM 供应商切换** — 前端设置面板支持 DeepSeek / OpenAI / Anthropic / Ollama 切换
- **流式评分 (SSE)** — 提交答案后实时逐 token 展示评分过程
- **会话恢复** — 面试中断后可恢复继续
- **面试历史全文搜索** — `GET /api/interviews/search?q=...`
- **API 速率限制** — slowapi 三层限速（通用/认证/LLM）
- **Chat 上下文管理** — 滑动窗口 + 自动截断，防止 LLM 超窗
- **PWA 缓存策略** — Service Worker 三层缓存（静态/导航/API）
- **前端代码分割** — recharts + react-markdown 动态导入，首屏 JS 减 ~140KB
- **错误恢复** — 面试提交失败时显示重试按钮

### Changed

- 统一前端为 Next.js，移除 Streamlit 代码
- 数据库连接改为线程级持久连接 + 自动重连
- 多智能体 LLM 缓存（cachetools TTLCache, 5min TTL）
- FastAPI 升级到 lifespan 生命周期模式
- 安全头中间件（X-Frame-Options, CSP, etc.）

### Fixed

- KnowledgeRetriever 未初始化导致的崩溃
- 前/后端面试主题列表对齐（12 个主题）
- SSE StreamingResponse JSON 格式调整

## [2.1.0] — 2026-05-31

### Added

- FastAPI 全局异常处理 + 请求日志中间件
- 收藏夹搜索/筛选/批量删除
- PDF 报告导出端点
- 前端国际化 (zh-CN + en-US)

### Changed

- 聊天 API 支持历史上下文
- 报告 API 返回 topic_scores / stage_scores 图表数据

## [2.0.0] — 2026-05-27

### Added

- Next.js 16 前端（双主题、i18n、PWA、虚拟滚动）
- Zustand + TanStack Query 状态管理
- 面试多阶段流程（基础/原理/进阶/项目/挑战）
- 智能评分四维度（正确性/逻辑/深度/表达）
- 简历分析（提取技术栈/级别/关键词）
- 收藏夹 CRUD

### Changed

- 重构为 FastAPI + Next.js 架构
- 多智能体系统（SharedMemory + MessageBus）

## [1.1.0] — 2026-05-01

### Added

- Streamlit 原型界面
- 基础面试功能
- LangChain 多供应商支持

## [1.0.0] — 2026-04-10

### Added

- 初始版本
- DeepSeek LLM 集成
- SQLite 数据持久化
