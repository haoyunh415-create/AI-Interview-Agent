import os
from html import escape

import streamlit as st
from dotenv import load_dotenv
from core.config import RETRIEVAL_SCORE_THRESHOLD
from core.rag_engine import retrieve, retrieve_with_metadata, rag_query
from core.interview_engine import step, STAGES, get_topic_keywords, get_hints, generate_summary
from agents.orchestrator import InterviewOrchestrator
from db.database import init_db, load_user
from report.report_generator import generate_pdf

load_dotenv()
init_db()

# ── Page config ──
st.set_page_config(
    page_title="AI Interview Copilot",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──
st.markdown("""
<style>
:root {
    --bg: #0c111d;
    --panel: rgba(17, 24, 39, 0.78);
    --panel-strong: rgba(15, 23, 42, 0.92);
    --line: rgba(148, 163, 184, 0.18);
    --text: #e5e7eb;
    --muted: #94a3b8;
    --accent: #38bdf8;
    --accent-2: #a3e635;
    --warn: #f59e0b;
    --danger: #fb7185;
}

html, body, [class*="css"] {
    font-family: "Inter", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 12% 4%, rgba(56, 189, 248, 0.12), transparent 28%),
        linear-gradient(145deg, #0c111d 0%, #111827 58%, #08111f 100%);
    color: var(--text);
}

.block-container {
    padding-top: 1.4rem;
    max-width: 1180px;
}

.main-header {
    color: #f8fafc;
    font-size: 2.35rem;
    font-weight: 760;
    letter-spacing: 0;
    line-height: 1.12;
    margin-top: 0.4rem;
}

.subtitle {
    color: var(--muted);
    font-size: 0.95rem;
    margin: 0.35rem 0 1.6rem 0;
}

.section-title {
    color: #f8fafc;
    font-size: 1.35rem;
    font-weight: 720;
    margin: 0.25rem 0 0.85rem 0;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
    border-right: 1px solid var(--line);
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #f8fafc !important;
}

.card,
.question-card,
.hint-box {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
    box-shadow: 0 18px 46px rgba(2, 6, 23, 0.24);
}

.card {
    padding: 1rem 1.1rem;
    margin: 0.75rem 0;
}

.card-header,
.question-card .label {
    color: #bae6fd;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0;
    margin-bottom: 0.45rem;
}

.card-content,
.question-card .text {
    color: var(--text);
    line-height: 1.72;
    overflow-wrap: anywhere;
}

.card-source {
    color: var(--muted);
    font-size: 0.8rem;
    margin-top: 0.7rem;
}

.question-card {
    border-color: rgba(56, 189, 248, 0.35);
    padding: 1.25rem;
    margin: 0.8rem 0 1rem 0;
}

.question-card .text {
    font-size: 1.1rem;
}

.hint-box {
    border-color: rgba(245, 158, 11, 0.38);
    color: #fde68a;
    padding: 0.95rem 1rem;
    margin: 0.55rem 0 0.85rem 0;
}

.score-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.55rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.78rem;
    margin-left: 0.35rem;
}
.score-green { background: rgba(34, 197, 94, 0.14); color: #86efac; border: 1px solid rgba(34, 197, 94, 0.32); }
.score-yellow { background: rgba(245, 158, 11, 0.14); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.32); }
.score-red { background: rgba(251, 113, 133, 0.14); color: #fda4af; border: 1px solid rgba(251, 113, 133, 0.32); }

.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    border-radius: 8px !important;
    font-weight: 700 !important;
    border: 1px solid var(--line) !important;
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #0284c7, #2563eb) !important;
    color: white !important;
    border: 0 !important;
}

.stTextInput input,
.stTextArea textarea {
    background: rgba(15, 23, 42, 0.72) !important;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}

.stProgress > div > div > div {
    background: linear-gradient(90deg, #38bdf8, #a3e635);
}

[data-testid="stMetric"] {
    background: var(--panel-strong);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 0.85rem 1rem;
}

[data-testid="stMetricValue"] {
    color: #f8fafc;
    font-weight: 760;
}

.streamlit-expanderHeader {
    background: rgba(15, 23, 42, 0.68);
    border-radius: 8px;
    border: 1px solid var(--line);
}

.stRadio > div {
    gap: 0.45rem;
}

.stRadio > div > label {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 0.55rem 0.85rem;
}

hr {
    border-color: var(--line);
}

.footer {
    text-align: center;
    padding: 1.6rem 0 0.6rem 0;
    color: #64748b;
    font-size: 0.78rem;
}

::-webkit-scrollbar { width: 7px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.38); border-radius: 8px; }

@media (max-width: 720px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .main-header { font-size: 1.8rem; }
    .question-card { padding: 1rem; }
}
</style>
""", unsafe_allow_html=True)

# ── Title ──
st.markdown('<div class="main-header">AI Interview Copilot</div>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">'
    'Focused interview practice, knowledge retrieval, and progress reporting with '
    '<a href="https://platform.deepseek.com/" target="_blank" style="color:#38bdf8">DeepSeek</a>'
    '</p>',
    unsafe_allow_html=True,
)

# ── Sidebar ──
with st.sidebar:
    st.title("Control Panel")

    user = st.text_input("Username", value="guest", help="Enter your name to track interview history")

    st.divider()

    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        st.subheader("API Key")
        api_key = st.text_input(
            "DeepSeek API Key",
            type="password",
            placeholder="sk-...",
            help="Get your key at https://platform.deepseek.com/",
            label_visibility="collapsed",
        )
    else:
        st.success("API Key configured")

    st.divider()

    st.subheader("Resume (optional)")
    uploaded_file = st.file_uploader("Upload resume", type=["txt", "md", "pdf"], label_visibility="collapsed")
    resume_content = ""
    resume_manual = ""
    if uploaded_file:
        if uploaded_file.type == "text/plain" or uploaded_file.name.endswith((".txt", ".md")):
            resume_content = uploaded_file.read().decode("utf-8", errors="ignore")
            st.success(f"Loaded: {uploaded_file.name}")
        else:
            st.info("PDF support coming soon. Please paste resume below.")
            resume_manual = st.text_area("Paste resume content", height=100, label_visibility="collapsed")

    full_resume = resume_content + "\n" + resume_manual

    st.divider()

    interview_target = st.selectbox(
        "Interview Topic",
        ["Transformer Core", "RAG Architecture", "Model Fine-tuning", "LLM Evaluation", "Custom Job"],
    )

    mode = st.radio(
        "Mode",
        ["RAG Search", "AI Interview", "Report", "Knowledge Base"],
        label_visibility="collapsed",
    )

    st.divider()

    with st.expander("Agent Status", expanded=False):
        from core.interview_engine import _get_orchestrator
        orch = _get_orchestrator(api_key if api_key else None)
        if resume_content or resume_manual:
            orch.analyze_resume(full_resume)
        for agent_name, state in orch.agent_status():
            color = "#86efac" if state == "ready" else "#fcd34d" if "待" in state else "#94a3b8"
            st.markdown(
                f'<span style="color:{color};font-size:0.82rem;">{agent_name}: {state}</span>',
                unsafe_allow_html=True,
            )

    if st.button("Reset Progress", use_container_width=True):
        from core.interview_engine import reset_orchestrator
        reset_orchestrator()
        for key in ["current_q", "stage_index", "last_score", "history", "show_hint", "is_followup", "followup_count"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.divider()

    st.markdown(
        '<p style="color:#475569;font-size:0.75rem;text-align:center;">'
        'Built with Streamlit + DeepSeek + ChromaDB<br>'
        '</p>',
        unsafe_allow_html=True,
    )

# ── Topic mapping (display -> internal) ──
TOPIC_MAP = {
    "Transformer Core": "Transformer核心原理",
    "RAG Architecture": "RAG检索增强生成",
    "Model Fine-tuning": "模型微调技术",
    "LLM Evaluation": "大模型综合评估",
    "Custom Job": "自定义岗位",
}
internal_topic = TOPIC_MAP.get(interview_target, interview_target)

# ── Session state init ──
if "current_q" not in st.session_state:
    st.session_state.current_q = None
if "stage_index" not in st.session_state:
    st.session_state.stage_index = 0
if "history" not in st.session_state:
    st.session_state.history = []
if "show_hint" not in st.session_state:
    st.session_state.show_hint = False
if "is_followup" not in st.session_state:
    st.session_state.is_followup = False
if "followup_count" not in st.session_state:
    st.session_state.followup_count = 0


def _safe_retrieve(target):
    try:
        return retrieve(target)
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()


def _html(text):
    return escape("" if text is None else str(text))


def _load_user_stats(user_name, rows):
    try:
        from db.database import load_user_stats

        stats = load_user_stats(user_name)
        if stats:
            return {
                "total_questions": stats["total_questions"],
                "topics_covered": stats["topics_covered"],
                "stages_covered": stats["stages_covered"],
                "last_time": stats["last_time"],
            }
    except ImportError:
        pass
    except (KeyError, TypeError, AttributeError):
        return {
            "total_questions": len(rows),
            "topics_covered": len(set(row[2] for row in rows)),
            "stages_covered": len(set(row[6] for row in rows)),
            "last_time": rows[-1][7] if rows else None,
        }

    return {
        "total_questions": len(rows),
        "topics_covered": len(set(row[2] for row in rows)),
        "stages_covered": len(set(row[6] for row in rows)),
        "last_time": rows[-1][7] if rows else None,
    }


# ═══════════════════════════════════════
# MODE: AI Interview
# ═══════════════════════════════════════
if mode == "AI Interview":
    st.markdown(f'<div class="section-title">{_html(interview_target)}</div>', unsafe_allow_html=True)

    if not api_key:
        st.warning("Configure your DeepSeek API Key in the sidebar.")
    else:
        # ── Custom job ──
        if interview_target == "Custom Job":
            with st.expander("Job Description", expanded=True):
                custom_job_desc = st.text_area(
                    "Describe the position requirements",
                    height=120,
                    placeholder="e.g. Proficiency in Transformer architecture, RAG development experience...",
                    label_visibility="collapsed",
                )
                if custom_job_desc and st.button("Generate Custom Questions", use_container_width=True):
                    with st.spinner("AI generating questions..."):
                        from core.interview_engine import generate_custom_questions
                        custom_questions = generate_custom_questions(custom_job_desc, api_key)
                        st.session_state.custom_questions = custom_questions
                        st.success("5 custom questions generated!")
                if "custom_questions" in st.session_state and st.session_state.custom_questions:
                    with st.expander("Generated Questions"):
                        for i, q in enumerate(st.session_state.custom_questions):
                            st.write(f"**{i+1}.** {q}")

        # ── Keywords ──
        keywords = get_topic_keywords(internal_topic)
        with st.expander("Knowledge Points"):
            st.markdown(" ".join([f'<code style="background:rgba(56,189,248,0.12);color:#bae6fd;padding:0.22rem 0.55rem;border-radius:6px;margin:0.18rem;display:inline-block;">{_html(k)}</code>' for k in keywords]) or "No keywords configured.", unsafe_allow_html=True)

        # ── Progress ──
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            followup_tag = f" <span style='color:#f59e0b;font-size:0.85rem;'>(追问中)</span>" if st.session_state.is_followup else ""
            st.markdown(
                f'<p style="font-size:1.05rem;color:#e5e7eb;">'
                f'Stage {st.session_state.stage_index + 1}/{len(STAGES)}: '
                f'<strong>{_html(STAGES[st.session_state.stage_index])}</strong>{followup_tag}</p>',
                unsafe_allow_html=True,
            )
        with col_b:
            pct = (st.session_state.stage_index + 1) / len(STAGES)
            st.progress(pct)
        with col_c:
            st.metric("Progress", f"{int(pct * 100)}%")

        # ── Start interview ──
        if st.session_state.current_q is None:
            if st.button("Start Interview", type="primary", use_container_width=True):
                with st.spinner("Preparing your interview..."):
                    context = _safe_retrieve(internal_topic) if interview_target != "Custom Job" else ""
                    custom_qs = st.session_state.get("custom_questions", None)
                    result = step(
                        user, internal_topic, context,
                        st.session_state.stage_index,
                        resume=full_resume if full_resume.strip() else None,
                        custom_questions=custom_qs,
                        api_key=api_key,
                    )
                    st.session_state.current_q = result["question"]
                    st.session_state.is_followup = result.get("is_followup", False)
                    st.rerun()
        else:
            # ── Question card ──
            label = "Follow-up Question" if st.session_state.is_followup else "Interviewer Asks"
            card_class = "question-card" if not st.session_state.is_followup else "question-card"
            followup_style = (
                'border-color:rgba(245,158,11,0.5);border-left:3px solid #f59e0b;'
                if st.session_state.is_followup else ''
            )
            st.markdown(f"""
            <div class="{card_class}" style="{followup_style}">
                <div class="label">{label}</div>
                <div class="text">{_html(st.session_state.current_q)}</div>
            </div>
            """, unsafe_allow_html=True)

            col_h1, col_h2, _ = st.columns([1, 1, 3])
            with col_h1:
                if st.button("Get Hint", use_container_width=True):
                    st.session_state.show_hint = True
            with col_h2:
                if st.button("Hide Hint", use_container_width=True):
                    st.session_state.show_hint = False

            if st.session_state.show_hint:
                hint = get_hints(st.session_state.current_q, api_key)
                st.markdown(f'<div class="hint-box">{_html(hint)}</div>', unsafe_allow_html=True)

            # ── Answer form ──
            with st.form(key="ans_form", clear_on_submit=True):
                answer = st.text_area("Your answer:", height=180, placeholder="Type your detailed response here...", label_visibility="collapsed")
                btn_label = "Submit Follow-up" if st.session_state.is_followup else "Submit & Next"
                submit = st.form_submit_button(btn_label, type="primary")

            if submit:
                if answer.strip():
                    with st.spinner("AI evaluating your answer..."):
                        context = _safe_retrieve(internal_topic) if interview_target != "Custom Job" else ""
                        result = step(
                            user, internal_topic, context,
                            st.session_state.stage_index,
                            st.session_state.current_q,
                            answer,
                            st.session_state.history,
                            resume=full_resume if full_resume.strip() else None,
                            custom_questions=st.session_state.get("custom_questions", None),
                            api_key=api_key,
                        )
                        st.session_state.history.append({"q": st.session_state.current_q, "a": answer})
                        st.session_state.last_score = result["report"]
                        st.session_state.show_hint = False

                        if result.get("all_completed"):
                            st.session_state.current_q = "All stages completed. View your report."
                            st.session_state.is_followup = False
                            st.balloons()
                        elif result.get("is_followup"):
                            st.session_state.current_q = result["next_q"]
                            st.session_state.is_followup = True
                        else:
                            st.session_state.current_q = result["next_q"]
                            st.session_state.stage_index = result["next_idx"]
                            st.session_state.is_followup = False
                        st.rerun()
                else:
                    st.warning("Please provide an answer.")

            # ── Last score ──
            if "last_score" in st.session_state:
                st.divider()
                st.success("Last Score Report")
                st.markdown(st.session_state.last_score)

            # ── History ──
            with st.expander(f"Interview Progress ({len(st.session_state.history)} answered)"):
                for i, h in enumerate(st.session_state.history):
                    st.markdown(f"**Q{i+1}:** {h['q']}")
                    preview = h["a"][:120] + "..." if len(h["a"]) > 120 else h["a"]
                    st.caption(f"A: {preview}")
                    st.markdown("---")

# ═══════════════════════════════════════
# MODE: Report
# ═══════════════════════════════════════
elif mode == "Report":
    st.markdown('<div class="section-title">Interview Report</div>', unsafe_allow_html=True)

    data = load_user(user)
    if data:
        stats = _load_user_stats(user, data)
        questions = [row[3] for row in data]
        answers = [row[4] for row in data]
        scores = [row[5] for row in data]

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Total Questions", stats["total_questions"] or len(data))
        with col_m2:
            st.metric("Topics Covered", stats["topics_covered"] or len(set(row[2] for row in data)))
        with col_m3:
            st.metric("Stages Covered", stats["stages_covered"] or len(set(row[6] for row in data)))

        if stats["last_time"]:
            st.caption(f"Last saved: {stats['last_time']}")

        if api_key:
            with st.spinner("Generating AI summary..."):
                summary = generate_summary(questions, answers, scores, api_key)
            with st.expander("AI Summary", expanded=True):
                st.markdown(summary)
        else:
            st.warning("Configure your API Key to generate AI summaries.")

        col_a1, col_a2 = st.columns(2)
        with col_a1:
            if st.button("Generate PDF Report", use_container_width=True):
                safe_user = "".join(ch for ch in user if ch.isalnum() or ch in ("-", "_")) or "guest"
                path = f"outputs/reports/{safe_user}_report.pdf"
                generate_pdf(data, path)
                st.success(f"Report saved: {path}")
        with col_a2:
            safe_user = "".join(ch for ch in user if ch.isalnum() or ch in ("-", "_")) or "guest"
            pdf_path = f"outputs/reports/{safe_user}_report.pdf"
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "Download PDF",
                        f,
                        file_name=f"{safe_user}_report.pdf",
                        use_container_width=True,
                    )
    else:
        st.info("No interview records yet. Take an interview first!")

# ═══════════════════════════════════════
# MODE: RAG Search
# ═══════════════════════════════════════
elif mode == "RAG Search":
    st.markdown('<div class="section-title">Knowledge Base Search</div>', unsafe_allow_html=True)

    answer_mode = st.radio(
        "Mode:",
        [" Quick (direct answer)", " Full (AI-generated answer)"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if not api_key and "Full" in answer_mode:
        st.warning("Configure your DeepSeek API Key for AI-generated answers.")
    else:
        q = st.text_input("", placeholder="Ask anything about Transformer, RAG, LoRA, LLM...", label_visibility="collapsed")

        if st.button("Search", type="primary", use_container_width=True) and q:
            if "Quick" in answer_mode:
                with st.spinner("Searching..."):
                    try:
                        result = retrieve_with_metadata(q)
                    except FileNotFoundError as e:
                        st.error(str(e))
                        st.stop()

                if not result:
                    st.warning("No matching content found in the knowledge base.")
                else:
                    score = result["score"]
                    if score <= 80:
                        badge = '<span class="score-badge score-green">High Confidence</span>'
                    elif score <= 150:
                        badge = '<span class="score-badge score-yellow">Medium Confidence</span>'
                    else:
                        badge = '<span class="score-badge score-red">Low Confidence</span>'

                    st.divider()
                    st.markdown(f"""
                    <div class="card" style="border-color:rgba(99,102,241,0.4);">
                        <div class="card-header">Best Match {badge}</div>
                        <div class="card-content" style="font-size:1.05rem;line-height:1.8;">{_html(result["content"])}</div>
                        <div class="card-source">Relevance score: {_html(score)} (0=best, 250=worst)</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                with st.spinner("Searching & generating answer..."):
                    try:
                        answer, sources = rag_query(q, api_key)
                    except FileNotFoundError as e:
                        st.error(str(e))
                        st.stop()

                st.divider()
                st.markdown(f"""
                <div class="card" style="border-color:rgba(34,197,94,0.4);">
                    <div class="card-header">AI Generated Answer</div>
                    <div class="card-content" style="font-size:1.05rem;line-height:1.8;">{_html(answer)}</div>
                </div>
                """, unsafe_allow_html=True)

# ═══════════════════════════════════════
# MODE: Knowledge Base Management
# ═══════════════════════════════════════
elif mode == "Knowledge Base":
    st.markdown('<div class="section-title">Knowledge Base Management</div>', unsafe_allow_html=True)

    kb_files = {
        "llm_pro_knowledge.txt": "LLM Professional Knowledge",
        "auto_kb.txt": "Extended Knowledge Base",
    }

    selected_kb = st.selectbox(
        "Select file:",
        options=list(kb_files.keys()),
        format_func=lambda x: f"{kb_files[x]} ({x})",
        label_visibility="collapsed",
    )

    with st.expander(" Preview Content", expanded=True):
        try:
            with open(f"data/{selected_kb}", "r", encoding="utf-8") as f:
                content = f.read()
                preview = content[:3000] + "..." if len(content) > 3000 else content
                st.text_area("Content", preview, height=300, disabled=True, label_visibility="collapsed")
                st.caption(f"Total {len(content):,} characters")
        except Exception as e:
            st.error(f"Read error: {e}")

    with st.expander(" Add Content"):
        new_content = st.text_area("New content (Markdown):", height=150, label_visibility="collapsed")
        if st.button("Append to Knowledge Base", use_container_width=True):
            if new_content.strip():
                try:
                    with open(f"data/{selected_kb}", "a", encoding="utf-8") as f:
                        f.write(f"\n\n---\n\n{new_content}")
                    st.success("Appended! Please rebuild the index.")
                except Exception as e:
                    st.error(f"Failed: {e}")
            else:
                st.warning("Content cannot be empty.")

    st.divider()

    col_k1, col_k2 = st.columns(2)
    with col_k1:
        st.subheader("Rebuild Index")
        st.warning("Required after modifying the knowledge base.")
        if st.button("Rebuild Vector Index", use_container_width=True):
            with st.spinner("Rebuilding index..."):
                try:
                    from core.ingest_knowledge import reset_knowledge_base
                    reset_knowledge_base()
                    st.success("Index rebuilt successfully!")
                except Exception as e:
                    st.error(f"Rebuild failed: {e}")
    with col_k2:
        st.subheader("Index Status")
        if os.path.exists("chroma_db"):
            size = sum(
                os.path.getsize(os.path.join(dirpath, fn))
                for dirpath, _, files in os.walk("chroma_db")
                for fn in files
            )
            st.metric("Index Size", f"{size / 1024:.1f} KB")
            st.info("Index is ready.")
        else:
            st.warning("Index not found. Please build it first.")

# ── Footer ──
st.markdown('<div class="footer">AI Interview Copilot &copy; 2026 &middot; Powered by DeepSeek + ChromaDB</div>', unsafe_allow_html=True)
