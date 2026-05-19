"""
app.py — WorkBridge AI
Main Streamlit application.
Orchestrates the multi-agent pipeline and renders the UI.
"""

import html
import streamlit as st

# Agent imports
from agents import guardrail_agent, planner_agent, retriever_agent, analyst_agent, critic_agent, response_agent

# ---------------------------------------------------------------------------
# Page configuration (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="WorkBridge AI",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — clean enterprise look
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ---------- Base ---------- */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* ---------- Header strip ---------- */
.pilot-header {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    border-radius: 10px;
    padding: 28px 36px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.pilot-header h1 {
    color: #ffffff;
    font-size: 2rem;
    font-weight: 600;
    margin: 0;
    letter-spacing: -0.5px;
}
.pilot-header p {
    color: #a8c8e8;
    margin: 4px 0 0 0;
    font-size: 0.95rem;
    font-weight: 300;
}

/* ---------- Agent step cards ---------- */
.agent-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #3b82f6;
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 10px;
    font-size: 0.9rem;
}
.agent-card.success { border-left-color: #10b981; }
.agent-card.warning { border-left-color: #f59e0b; }
.agent-card.error   { border-left-color: #ef4444; }

/* ---------- Status badge ---------- */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 0.5px;
    margin-left: 8px;
}
.badge-ok      { background: #d1fae5; color: #065f46; }
.badge-warn    { background: #fef3c7; color: #92400e; }
.badge-block   { background: #fee2e2; color: #991b1b; }
.badge-running { background: #dbeafe; color: #1e40af; }

/* ---------- Final answer box ---------- */
.final-answer {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-left: 5px solid #16a34a;
    border-radius: 8px;
    padding: 24px 28px;
    font-size: 1rem;
    line-height: 1.7;
    color: #14532d;
}

/* ---------- Source snippet ---------- */
.source-snippet {
    background: #f8f8f8;
    border: 1px solid #e5e5e5;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 10px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: #374151;
    line-height: 1.5;
}
.source-label {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    color: #6b7280;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ---------- Critic table ---------- */
.critic-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #f3f4f6;
    font-size: 0.88rem;
}
.critic-label { color: #6b7280; font-weight: 500; }
.critic-value { color: #111827; font-weight: 600; }

/* ---------- Sidebar ---------- */
.sidebar-section {
    background: #f1f5f9;
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 14px;
    font-size: 0.85rem;
}
.sidebar-section h4 {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #475569;
    margin: 0 0 10px 0;
}

/* ---------- Misc ---------- */
.stButton>button {
    background: #1e40af;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 28px;
    font-size: 0.95rem;
    font-weight: 500;
    width: 100%;
    transition: background 0.2s;
}
.stButton>button:hover {
    background: #1d4ed8;
}
.stTextArea textarea {
    border-radius: 6px;
    border: 1px solid #d1d5db;
    font-family: 'IBM Plex Sans', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-section">
        <h4>🔗 About WorkBridge AI</h4>
<p>WorkBridge AI is a guardrailed multi-agent assistant that helps employees answer policy and compliance questions using internal policy documents.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-section">
        <h4>📋 Agents in Pipeline</h4>
        <ol style="margin:0; padding-left:18px; line-height:1.9">
            <li><b>Guardrail</b> — Safety check</li>
            <li><b>Planner</b> — Break down query</li>
            <li><b>Retriever</b> — Find policy sections</li>
            <li><b>Analyst</b> — Generate answer</li>
            <li><b>Critic</b> — Validate answer</li>
            <li><b>Response</b> — Format final output</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-section">
        <h4>💡 Sample Questions</h4>
    </div>
    """, unsafe_allow_html=True)

    sample_questions = [
        "Can I approve a refund over $500?",
        "Can customer SSNs be stored in support tickets?",
        "When should a case be escalated to compliance?",
        "What information is considered PII?",
        "What happens if I suspect a data breach?",
        "How long does a standard refund take?",
        "What if a customer threatens legal action?",
        "A customer sent their SSN in a support ticket. What should I do?",
    ]

    for q in sample_questions:
        if st.button(q, key=f"sample_{q[:20]}", use_container_width=True):
            st.session_state["prefill_query"] = q

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.75rem; color:#94a3b8; text-align:center">
        WorkBridge AI · Enterprise Prototype<br>
        Powered by GPT-4o-mini + controlled multi-agent orchestration
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="pilot-header">
    <div>
        <h1>🔗 WorkBridge AI</h1>
        <p>Guardrailed Multi-Agent Enterprise Workflow Assistant — answers policy questions using retrieved internal documents</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Query input
# ---------------------------------------------------------------------------
col1, col2 = st.columns([3, 1])

prefill = st.session_state.pop("prefill_query", "")

with col1:
    user_query = st.text_area(
        "Ask a policy question",
        value=prefill,
        height=100,
        placeholder="e.g. Can I approve a refund over $500? / What counts as PII?",
        label_visibility="collapsed",
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    run_button = st.button("▶ Run Analysis", use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------
if run_button:
    if not user_query.strip():
        st.warning("Please enter a policy question before running the analysis.")
        st.stop()

    # ---- containers for live updates ----
    status_placeholder = st.empty()
    results_container  = st.container()

    with results_container:
        left_col, right_col = st.columns([2, 1])

    # =========================================================
    # STEP 1 — GUARDRAIL
    # =========================================================
    status_placeholder.info("🔒 **Step 1/6 — Guardrail Agent** running safety check…")

    guardrail = guardrail_agent.run(user_query)

    with results_container:
        with left_col:
            with st.expander("🔒 Guardrail Agent", expanded=True):
                badge = '<span class="badge badge-ok">PASSED</span>' if guardrail.is_safe else '<span class="badge badge-block">BLOCKED</span>'
                card_class = "success" if guardrail.is_safe else "error"
                st.markdown(
                    f'<div class="agent-card {card_class}">'
                    f'<b>Result:</b> {badge}<br><br>{guardrail.reason}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    if not guardrail.is_safe:
        status_placeholder.error("🚫 Request blocked by Guardrail Agent. No further processing.")
        st.stop()

    # =========================================================
    # STEP 2 — PLANNER
    # =========================================================
    status_placeholder.info("📋 **Step 2/6 — Planner Agent** building retrieval plan…")

    planner = planner_agent.run(user_query)

    with results_container:
        with left_col:
            with st.expander("📋 Planner Agent", expanded=True):
                if planner.error:
                    st.markdown(f'<div class="agent-card error">❌ {planner.error}</div>', unsafe_allow_html=True)
                else:
                    steps_html = "".join(
                        f"<div style='margin-bottom:6px'><b>{i}.</b> {step}</div>"
                        for i, step in enumerate(planner.steps, 1)
                    )
                    st.markdown(
                        f'<div class="agent-card success">'
                        f'<b>Plan</b> <span class="badge badge-ok">{len(planner.steps)} steps</span><br><br>'
                        f'{steps_html}</div>',
                        unsafe_allow_html=True,
                    )

    # =========================================================
    # STEP 3 — RETRIEVER
    # =========================================================
    status_placeholder.info("🔍 **Step 3/6 — Retriever Agent** searching policy documents…")

    retriever = retriever_agent.run(user_query)

    with results_container:
        with left_col:
            with st.expander("🔍 Retriever Agent", expanded=True):
                if retriever.error:
                    st.markdown(f'<div class="agent-card error">❌ {retriever.error}</div>', unsafe_allow_html=True)
                else:
                    files_str = ", ".join(retriever.files_searched)
                    st.markdown(
                        f'<div class="agent-card success">'
                        f'<b>Files searched:</b> <code>{files_str}</code><br>'
                        f'<b>Chunks retrieved:</b> {len(retriever.chunks)}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    if retriever.error:
        status_placeholder.error("❌ Retrieval failed. Cannot generate answer without policy context.")
        st.stop()

    # Show source snippets in right column
    with results_container:
        with right_col:
            st.markdown("#### 📄 Retrieved Policy Sections")
            for i, chunk in enumerate(retriever.chunks, 1):
                source_display = chunk.source_file.replace("_", " ").replace(".txt", "").title()
                st.markdown(
                    f'<div class="source-label">Source {i} · {source_display} · Score: {chunk.score}</div>'
                    f'<div class="source-snippet">{chunk.content[:420]}{"…" if len(chunk.content) > 420 else ""}</div>',
                    unsafe_allow_html=True,
                )

    # =========================================================
    # STEP 4 — ANALYST
    # =========================================================
    status_placeholder.info("🧠 **Step 4/6 — Analyst Agent** generating grounded answer…")

    analyst = analyst_agent.run(user_query, retriever.chunks)

    with results_container:
        with left_col:
            with st.expander("🧠 Analyst Agent", expanded=True):
                if analyst.error:
                    st.markdown(f'<div class="agent-card error">❌ {analyst.error}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<div class="agent-card success">'
                        f'<b>Draft answer generated</b> <span class="badge badge-ok">GROUNDED</span><br><br>'
                        f'{html.escape(analyst.answer)}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    if analyst.error:
        status_placeholder.error("❌ Analyst failed. Cannot proceed.")
        st.stop()

    # =========================================================
    # STEP 5 — CRITIC
    # =========================================================
    status_placeholder.info("🔎 **Step 5/6 — Critic Agent** validating answer quality…")

    critic = critic_agent.run(user_query, analyst.answer, analyst.context_used)

    with results_container:
        with left_col:
            with st.expander("🔎 Critic Agent", expanded=True):
                if critic.error:
                    st.markdown(f'<div class="agent-card error">❌ {critic.error}</div>', unsafe_allow_html=True)
                else:
                    rec_badge = "badge-ok" if critic.approved else "badge-block"
                    conf_badge = {
                        "HIGH": "badge-ok",
                        "MEDIUM": "badge-warn",
                        "LOW": "badge-block",
                    }.get(critic.confidence.upper(), "badge-running")

                    st.markdown(f"""
                    <div class="agent-card {'success' if critic.approved else 'warning'}">
                        <div class="critic-row">
                            <span class="critic-label">Grounding</span>
                            <span class="critic-value">{critic.grounding}</span>
                        </div>
                        <div class="critic-row">
                            <span class="critic-label">Accuracy</span>
                            <span class="critic-value">{critic.accuracy}</span>
                        </div>
                        <div class="critic-row">
                            <span class="critic-label">Completeness</span>
                            <span class="critic-value">{critic.completeness}</span>
                        </div>
                        <div class="critic-row">
                            <span class="critic-label">Confidence</span>
                            <span class="critic-value">
                                <span class="badge {conf_badge}">{critic.confidence}</span>
                            </span>
                        </div>
                        <div class="critic-row" style="border:none">
                            <span class="critic-label">Issues</span>
                            <span class="critic-value">{critic.issues}</span>
                        </div>
                        <br>
                        <b>Recommendation:</b>
                        <span class="badge {rec_badge}">{critic.recommendation}</span>
                    </div>
                    """, unsafe_allow_html=True)

    # =========================================================
    # STEP 6 — RESPONSE FORMATTER
    # =========================================================
    status_placeholder.info("✅ **Step 6/6 — Response Agent** formatting final answer…")

    response = response_agent.run(
        user_query=user_query,
        draft_answer=analyst.answer,
        critic_result=critic,
        source_files=retriever.files_searched,
    )

    with results_container:
        with left_col:
            with st.expander("✅ Response Agent", expanded=True):
                if response.error:
                    st.markdown(f'<div class="agent-card error">❌ {response.error}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<div class="agent-card success">'
                        f'Final answer formatted and ready.'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    # =========================================================
    # FINAL ANSWER
    # =========================================================
    status_placeholder.success("✅ Analysis complete.")

    st.markdown("---")
    st.markdown("### 💬 Final Answer")

    if response.error:
        st.error(f"Could not format final answer: {response.error}")
        st.markdown("**Draft answer (unformatted):**")
        st.write(analyst.answer)
    else:
        st.markdown(
            f'<div class="final-answer">{html.escape(response.final_answer).replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )

        confidence = critic.confidence.upper() if not critic.error else "UNKNOWN"

        if confidence == "HIGH":
            st.success("🟢 System Confidence: High — answer is strongly supported by retrieved policy context.")
        elif confidence == "MEDIUM":
            st.warning("🟡 System Confidence: Medium — answer is mostly supported, but review may be helpful.")
        else:
            st.error("🔴 System Confidence: Review Recommended — retrieved context may not fully support the answer.")

        with st.expander("Why this answer was generated"):
            st.write(f"Relevant policy files searched: {', '.join(retriever.files_searched)}")
            st.write(f"Policy sections retrieved: {len(retriever.chunks)}")
            st.write(f"Critic recommendation: {critic.recommendation}")
            st.write(f"Critic confidence: {critic.confidence}")
            st.write(
                "The answer was generated only after the Guardrail, Planner, Retriever, Analyst, "
                "Critic, and Response agents completed the controlled workflow."
            )

    # Confidence warning banner
    if not critic.error and critic.confidence.upper() == "LOW":
        st.warning(
            "⚠️ **Low Confidence Warning**: The retrieved policy sections may not fully address "
            "your question. Please consult the relevant policy owner or your manager directly."
        )
    elif not critic.error and not critic.approved:
        st.warning(
            "⚠️ **Review Recommended**: The Critic agent flagged this answer for review. "
            "Treat it as a starting point and verify with the appropriate team."
        )

else:
    # Landing state
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; color: #94a3b8;">
        <div style="font-size: 3rem; margin-bottom: 16px">🔗</div>
        <div style="font-size: 1.1rem; font-weight: 500; color: #64748b; margin-bottom: 8px">
            Ask a policy question to get started
        </div>
        <div style="font-size: 0.9rem">
            Try one of the sample questions in the sidebar, or type your own.
        </div>
    </div>
    """, unsafe_allow_html=True)
