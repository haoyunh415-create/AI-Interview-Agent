# Resume Keyword-Driven Interview — Design Spec

## Overview

当前 AI Interview Copilot 的流程：用户手动选 Topic → 上传简历 → ResumeAnalyst 提取 profile → Interviewer 参考 profile 出题。

目标流程：上传简历 → 自动提取技术关键词 → 用户确认关键词 → 关键词驱动全流程（自动匹配 Topic、自动检索知识库、出题覆盖核心技术栈、评分参考关键词）。

## Architecture

```
Upload Resume
   │
   ▼
ResumeAnalyst (enhanced)
   │  Existing: tech_stack, level, domains, gaps, highlights
   │  New: keywords (5-8 tech terms with weights)
   │
   ▼
UI — Keyword Confirmation Page
   │  Show keyword tags, user can add/delete/modify
   │  Auto-match best interview topic
   │  User clicks confirm
   │
   ▼
Orchestrator (refactored)
   │  Receives keywords, injects into every Agent
   │
   ├─► KnowledgeRetriever  Multi-keyword retrieval, merge + dedup context
   ├─► Interviewer         Generate questions covering high-weight keywords
   ├─► Evaluator           Check if answer covers candidate's claimed tech stack
   └─► ReportWriter        Compare keywords vs actual performance in summary
```

## Change Scope

| File | Change Level |
|------|-------------|
| `agents/resume_analyst.py` | Small — add `keywords` field to prompt and output |
| `agents/knowledge_retriever.py` | Medium — add `get_multi_keyword_context()` |
| `agents/interviewer.py` | Small — inject keywords into question prompt |
| `agents/evaluator.py` | Small — inject keywords into evaluation prompt |
| `agents/orchestrator.py` | Medium — keyword flow management |
| `views/interview.py` | Medium — add keyword confirmation step |
| `views/common.py` | Small — auto-fill topic when keywords confirmed |

**Unchanged:** `core/config.py`, `core/llm.py`, `core/rag_engine.py`, `core/scoring.py`, `core/ingest_knowledge.py`, `core/logging_config.py`, `db/database.py`, `report/`, `views/search.py`, `views/report.py`, `views/knowledge_base.py`

## Data Flow

### ResumeAnalyst — New Output Field

```json
{
  "keywords": [
    {"term": "Transformer", "weight": 0.95},
    {"term": "LoRA", "weight": 0.85},
    {"term": "RAG", "weight": 0.80},
    {"term": "BERT", "weight": 0.75},
    {"term": "PyTorch", "weight": 0.70}
  ]
}
```

- 5-8 keywords, descending by weight
- weight = importance in resume (frequency + project relevance)
- Both English terms and Chinese accepted, prefer original terminology
- Fallback: empty list → degrade to manual topic selection mode

### Keyword Confirmation Page (UI)

```
┌───────────────────────────────────────┐
│  From your resume:                    │
│                                       │
│  [Transformer ×] [LoRA ×] [RAG ×]    │  ← deletable tags
│  [BERT ×] [PyTorch ×]                │
│                                       │
│  + Add keyword: [________] [Add]      │
│                                       │
│  ─────────────────────────────────    │
│                                       │
│  Suggested Topic: RAG Architecture  ▼ │  ← auto-matched, editable
│                                       │
│  [Confirm & Start Interview]          │
└───────────────────────────────────────┘
```

- State gate: `st.session_state.keywords_confirmed == False`
- After confirmation: keywords → session state, topic → session state, flag → True
- Topic auto-match: `keywords ∩ topic_keywords` → highest intersection wins

### Per-Agent Keyword Usage

| Agent | Receives | Purpose |
|-------|---------|---------|
| KnowledgeRetriever | All keywords (top-3 by weight) | Multi-keyword retrieval, merge + dedup context |
| Interviewer | keywords + weights | Generate questions targeting high-weight terms |
| Evaluator | keywords | Check if answer covers claimed tech stack |
| ReportWriter | keywords + stage scores | Compare tech stack vs actual performance |

## Component Details

### 3.1 ResumeAnalyst

New prompt instruction:

```
7. 技术关键词：从简历中提取5-8个核心技术术语，
   按重要性排序并赋权重(0-1)。
   包括：框架、模型、算法、工具名。
   中英文均可，优先保留原名。
```

### 3.2 KnowledgeRetriever

New method `get_multi_keyword_context(keywords, limit=3)`:

- Take top-N keywords by weight (default 3)
- Call `search(term)` for each
- Deduplicate results by content hash
- Join with `\n---\n` separator
- Return merged context string

### 3.3 Interviewer

Append to existing prompt:

```
候选人核心技术栈：{keyword_list}
请优先围绕这些技术出题，确保考察其核心技术能力。
```

`keyword_list` format: `Transformer(核心), LoRA(熟悉), RAG(了解)` — weights as proficiency hints.

### 3.4 Evaluator

Append to evaluation prompt:

```
候选人技术栈：{keyword_list}
请检查回答是否涉及了候选人声称掌握的技术，作为评分参考。
```

Scoring dimensions unchanged (correctness/logic/depth/expression). Keywords only as reference context.

### 3.5 Orchestrator

New state: `self.keywords`. Injected at interview start, passed to each agent call.

### 3.6 Sidebar

- Topic selectbox auto-filled when keywords confirmed
- Not removed (still needed for RAG Search mode)
- Marked `disabled` when keywords are in play

## Key Principles

- **User has final say** — keyword confirmation page lets user correct LLM extraction errors
- **Graceful degradation** — if keyword extraction fails, fall back to manual topic selection
- **Minimal change** — core engines unchanged, only agent prompts and orchestration touched
