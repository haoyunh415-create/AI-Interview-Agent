
> 多智能体驱动的 AI 面试练习平台 — 支持模拟面试、简历分析、智能评分、聊天问答

---

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 🎙️ **模拟面试** | 5 阶段 AI 面试（基础→原理→进阶→项目→挑战），自动追问，实时流式评分 |
| 📄 **简历分析** | 上传简历（TXT/MD/PDF），AI 提取技术栈、经验级别、专长领域、知识盲区 |
| 💬 **AI 闲聊** | 自由问答，支持图片粘贴/拖拽，上下文窗口自动管理 |
| 📊 **学习报告** | 多维评分趋势雷达图、主题对比、AI 总结报告、PDF 导出 |
| ⭐ **收藏夹** | 收藏/搜索/筛选/笔记/批量删除面试题目 |
| 🏛️ **多模型支持** | DeepSeek / OpenAI / Anthropic / Ollama 一键切换 |
| 🔐 **用户认证** | JWT 注册/登录，数据隔离 |
| 🔄 **会话恢复** | 面试中断后可恢复继续 |
| 🌐 **国际化** | 中文/英文完整界面 |
| 🌙 **双主题** | 深色/浅色模式 |
| 📱 **PWA** | 可安装至桌面，支持离线（部分） |

---

## 🏗️ 架构

```
┌─────────────────────────────────────┐
│         Next.js 16 (port 3000)       │
│  Zustand + React Query + i18n      │
│  recharts (动态导入) + Tailwind CSS │
│  Dark/Light Theme + PWA            │
└──────────────┬──────────────────────┘
               │ HTTP / SSE
┌──────────────▼──────────────────────┐
│        FastAPI (port 8765)          │
│  安全头 + 日志 + 限速 + 异常处理   │
├─────────────────────────────────────┤
│   Session Store (内存, 2h TTL)      │
│   DB 连接池 (线程本地持久化)        │
├──────────┬────────────┬────────────┤
│ Chat API │ Resume API │ Interview │
│          │            │  + SSE    │
├──────────┴────────────┴────────────┤
│       多智能体系统                   │
│  ┌──────┐ ┌─────┐ ┌─────┐ ┌────┐ │
│  │Resume│ │Inter│ │Eval │ │Rpt │ │
│  └──────┘ └─────┘ └─────┘ └────┘ │
│  SharedMemory + MessageBus        │
│  cachetools TTLCache (LLM缓存)    │
├─────────────────────────────────────┤
│         SQLite (WAL + autocommit)   │
"""<span>",
"bookmarks", "sessions", "users"
└─────────────────────────────────────┘
```

### 智能体系统

四个专业 Agent 通过 **SharedMemory** + **MessageBus** 协作：

| Agent | 职责 |
|-------|------|
| **ResumeAnalyst** | 解析简历，提取技术栈/级别/领域/关键词 |
| **Interviewer** | 根据阶段/背景/历史生成面试题和追问 |
| **Evaluator** | 四维度评分（正确性/逻辑/深度/表达）、判断是否需要追问 |
| **ReportWriter** | 综合面试过程，生成结构化总结报告 |

---

## 🚀 快速开始

### 前置要求

- Python ≥ 3.11
- Node.js ≥ 20
- LLM API Key（DeepSeek / OpenAI / Anthropic / Ollama）

### 1. 后端

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 启动 FastAPI
uvicorn backend.main:app --host 0.0.0.0 --port 8765
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

打开 `http://localhost:3000`。

### 3. Docker

```bash
docker compose up -d
```

- 前端: http://localhost:3000
- 后端: http://localhost:8765/api/health

---

## ⚙️ 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_PROVIDER` | `deepseek` | LLM 供应商: deepseek/openai/anthropic/ollama |
| `DEEPSEEK_API_KEY` | — | DeepSeek API 密钥 |
| `OPENAI_API_KEY` | — | OpenAI API 密钥 |
| `ANTHROPIC_API_KEY` | — | Anthropic API 密钥 |
| `LLM_TEMPERATURE` | `0.7` | 采样温度 |
| `LLM_CACHE_TTL` | `300` | LLM 缓存 TTL（秒） |
| `JWT_SECRET` | `change-me-in-production` | JWT 签名密钥 |
| `RATE_LIMIT_LLM` | `10/minute` | LLM 接口限速 |
| `DISABLE_RATE_LIMIT` | — | 设为 `1` 禁限速（测试用） |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `LOG_FORMAT` | `text` | 日志格式: text/json |

---

## 📡 API 端点

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| GET | `/api/auth/me` | 当前用户信息 [需 Bearer Token] |

### 面试

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/interview/start` | 开始面试 |
| POST | `/api/interview/answer` | 提交答案 |
| POST | `/api/interview/answer/stream` | **SSE 流式**提交答案 |
| POST | `/api/interview/hint` | 获取提示 |
| POST | `/api/interview/report` | 生成报告 |
| POST | `/api/interview/resume` | 恢复面试会话 |

### 其他

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 聊天（支持 history 上下文） |
| POST | `/api/resume/analyze` | 简历分析 |
| POST | `/api/report` | 面试统计 + AI 总结 |
| POST | `/api/report/pdf` | 下载 PDF 报告 |
| GET/POST/DELETE | `/api/bookmarks` | 收藏 CRUD |
| GET/DELETE | `/api/sessions` | 会话管理 |
| GET | `/api/interviews/search` | 全文搜索面试记录 |
| GET | `/api/health` | 健康检查 |

---

## 🧪 测试

```bash
# Python 后端测试 (138 tests)
python -m pytest tests/ -v

# 前端测试 (59 tests)
cd frontend && npm test
```

GitHub Actions 自动运行两部分测试：

- **`.github/workflows/test.yml`** — Python lint + 测试（py3.11/3.12/3.13）
- **`.github/workflows/ci.yml`** — 前端 type-check + 测试 + build

---

## 📦 技术栈

| 层 | 技术 |
|------|--------|
| **前端** | Next.js 16, React 18, Zustand, TanStack Query, recharts, Tailwind CSS |
| **后端** | FastAPI, Uvicorn, LangChain, SQLite |
| **智能体** | SharedMemory + MessageBus 事件驱动架构 |
| **认证** | JWT (HS256), SHA-256 + salt 密码哈希 |
| **缓存** | cachetools TTLCache (LLM 响应) |
| **限速** | slowapi (三层速率控制) |
| **基础设施** | Docker, Docker Compose, GitHub Actions |

---

## 📁 项目结构

```
├── agents/            # 多智能体系统
│   ├── base.py        # BaseAgent (LLM invoke/cache/telemetry)
│   ├── orchestrator.py # InterviewOrchestrator (总调度)
│   ├── interviewer.py  # 出题 Agent
│   ├── evaluator.py    # 评分 Agent
│   ├── report_writer.py # 报告 Agent
│   └── resume_analyst.py # 简历 Agent
├── backend/           # FastAPI 后端
│   ├── main.py        # 入口 + 中间件 + 异常处理
│   ├── limiter.py     # 速率限制
│   ├── session_store.py # 面试会话存储
│   └── api/           # 路由模块
│       ├── auth.py    # 认证
│       ├── chat.py    # 聊天
│       ├── interview.py # 面试
│       ├── report.py  # 报告
│       ├── resume.py  # 简历
│       ├── bookmarks.py # 收藏
│       └── sessions.py # 会话
├── core/              # 核心配置与工具
│   ├── config.py      # 集中配置
│   ├── constants.py   # 常量 & 主题映射
│   ├── llm.py         # LLM 工厂 (多供应商)
│   ├── memory.py      # SharedMemory + MessageBus
│   ├── chat_context.py # 上下文窗口管理
│   ├── telemetry.py   # LLM 调用追踪
│   └── logging_config.py # 日志配置
├── db/                # 数据库层
│   └── database.py    # SQLite (WAL, 连接池)
├── frontend/          # Next.js 前端
│   └── src/
│       ├── app/       # 页面 & 布局
│       ├── components/ # UI 组件
│       ├── stores/    # Zustand 状态
│       ├── lib/       # API 客户端 & 工具
│       └── i18n/      # 国际化
├── tests/             # Python 测试 (138 个)
└── report/            # PDF 报告生成
```

---

## 📊 代码质量

| 指标 | 数值 |
|------|------|
| Python 测试 | **138** ✅ |
| 前端测试 | **59** ✅ |
| TypeScript | **0 errors** ✅ |
| Ruff lint | **0 errors** ✅ |
| Python 代码 | ~5,900 行 |
| TypeScript/React | ~5,400 行 |

---

## 📄 License

MIT
