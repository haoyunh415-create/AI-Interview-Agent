# ADR-006: Next.js 而非 Streamlit 作为主前端

## 状态

✅ 已采纳 (2026-06-01)

## 背景

项目最初存在两套前端（Streamlit + Next.js），需要统一。

## 方案对比

| 维度 | Next.js 16 | Streamlit |
|------|-----------|-----------|
| UI 定制能力 | 完全可控 | 受限的组件库 |
| 主题支持 | CSS 变量 + 双主题 | 仅暗色 |
| 国际化 | 完整 i18n | 不原生支持 |
| PWA/离线 | 支持 | 不支持 |
| 测试 | Jest/Vitest | 困难 |
| 学习成本 | 中 | 低 |

## 决策

选 **Next.js**，移除 Streamlit。

## 理由

1. **设计系统** — Tailwind + CSS 变量 + 动画体系远优于 Streamlit 默认样式
2. **PWA** — 支持离线访问和桌面安装
3. **测试** — 标准 React 测试工具链
4. **性能** — Next.js 静态导出 + 动态导入优于 Streamlit 的 Python 渲染循环

## 后果

- 流式评分需要额外开发（Streamlit 原生支持，Next.js 需 SSE）
- 功能增加需要前后端同步开发
