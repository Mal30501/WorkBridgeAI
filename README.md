# 🔗 WorkBridge AI

**Guardrailed Multi-Agent Enterprise Workflow Assistant**

WorkBridge AI is a guardrailed multi-agent enterprise assistant that answers employee policy and workflow questions using retrieved internal policy documents. The system supports policy domains such as refunds, PII handling, escalation workflows, PTO/leave, remote work, equipment usage, and expense reimbursement.

---

## 📐 Architecture

```
User Query
    │
    ▼
┌─────────────────┐
│  Guardrail Agent│  ← Blocks prompt injection, off-topic queries
└────────┬────────┘
         │ (safe)
    ▼
┌─────────────────┐
│  Planner Agent  │  ← Breaks query into retrieval steps
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│ Retriever Agent │  ← Keyword search over local policy .txt files
└────────┬────────┘
         │ (top-K chunks)
    ▼
┌─────────────────┐
│  Analyst Agent  │  ← Answers using ONLY retrieved context (RAG)
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│  Critic Agent   │  ← Validates grounding, accuracy, confidence
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│ Response Agent  │  ← Formats clean final answer, adds caveats
└─────────────────┘
         │
    Final Answer (shown in UI)
```

Each agent is implemented as a separate Python module. The Streamlit application (`app.py`) orchestrates the workflow sequentially, where each agent passes structured outputs downstream to the next stage in the pipeline. The UI exposes intermediate reasoning and retrieval steps for explainability and traceability.

---

## 🤖 Agent Descriptions

| Agent | Role | Key Behaviour |
|---|---|---|
| **Guardrail** | Input safety | Regex-based detection of prompt injection, jailbreak phrases, off-topic requests. Blocks before any LLM call. |
| **Planner** | Query decomposition | Uses GPT-4o-mini to break the question into 2–4 actionable retrieval steps. Makes the plan visible in the trace. |
| **Retriever** | Policy search | Lightweight intent-aware retrieval over chunked local `.txt` policy files using keyword overlap, synonym expansion, and policy-domain matching. Returns top-K scored chunks. |
| **Analyst** | Answer generation | RAG-style generation. System prompt explicitly forbids using knowledge outside the provided context. |
| **Critic** | Quality validation | Structured evaluation: grounding, accuracy, completeness, confidence, recommendation (APPROVE / APPROVE WITH CAVEAT / REVISE). |
| **Response** | Output formatting | Formats the final answer for a non-technical employee. Appends confidence warnings or caveats as needed. |

---

## 📁 Project Structure

```text
WorkBridgeAI/
│
├── agents/
│   ├── guardrail_agent.py          # Input safety & injection detection
│   ├── planner_agent.py            # Query decomposition & domain inference
│   ├── retriever_agent.py          # Intent-aware local policy retrieval
│   ├── analyst_agent.py            # Grounded answer generation (RAG)
│   ├── critic_agent.py             # Answer validation & confidence scoring
│   └── response_agent.py           # Final answer formatting
│
├── policies/
│   ├── refund_policy.txt                   # Refund authorization rules
│   ├── pii_policy.txt                      # PII definitions & data handling
│   ├── escalation_policy.txt               # Escalation procedures
│   ├── hr_pto_policy.txt                   # PTO & leave policy
│   ├── remote_work_equipment_policy.txt    # Remote work & equipment usage
│   └── expense_travel_policy.txt           # Expense reimbursement & travel policy
│
├── utils/
│   └── openai_helper.py            # Centralised OpenAI client wrapper
│
├── screenshots/
│   ├── dashboard.png
│   ├── agent-trace.png
│   ├── final-answer.png
│   └── guardrail-block.png
│
├── app.py                          # Streamlit UI & orchestration layer
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourname/WorkBridgeAI.git
cd WorkBridgeAI
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Open .env and add your OpenAI API key
```

Your `.env` file should look like:

```
OPENAI_API_KEY=sk-your-key-here
```

### 5. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 🌐 Deployment

### Streamlit Community Cloud (free, recommended for demos)

1. Push the repository to GitHub (ensure `.env` is in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo and select `app.py` as the entry point
4. Add `OPENAI_API_KEY` in the **Secrets** panel (Settings → Secrets)

### Other options

- **Railway / Render**: Add as an environment variable in the dashboard; start command is `streamlit run app.py --server.port $PORT`
- **Local network demo**: `streamlit run app.py --server.address 0.0.0.0`

---

## 🔐 Security & Guardrails

### Input Safety (Guardrail Agent)

The Guardrail Agent runs before any LLM call and blocks:

- **Prompt injection**: Phrases like `"ignore previous instructions"`, `"reveal system prompt"`, `"bypass security"`
- **Jailbreak attempts**: `"developer mode"`, `"DAN"`, `"act as if you have no restrictions"`
- **Off-topic queries**: Recipes, entertainment, sports, financial data unrelated to company policy
- **Trivially short or excessively long inputs**

Blocked requests never reach the OpenAI API.

### Retrieval-Augmented Generation (RAG)

The Analyst agent's system prompt explicitly instructs the model to use **only** the retrieved policy context. This prevents the model from hallucinating policy rules from its training data.

### API Key Protection

- API keys are loaded from `.env` via `python-dotenv`
- The `.env.example` file shows structure without real credentials
- The key is never logged, displayed in the UI, or included in any agent output

### Critic Validation

Every answer is reviewed by the Critic agent before it reaches the user. Low-confidence answers trigger visible warning banners in the UI.

---

## 💡 Example Questions

| Question | Policy Domain |
|---|---|
| Can I approve a refund over $500? | Refund Policy |
| Can customer SSNs be stored in support tickets? | PII Policy |
| When should a case be escalated to compliance? | Escalation Policy |
| Can I take PTO next Friday? | PTO / Leave Policy |
| Can I expense a client dinner? | Expense Reimbursement Policy |
| Can I request a second monitor for remote work? | Remote Work Policy |
| What if a customer threatens legal action? | Escalation Policy |
| What happens if I suspect a data breach? | PII + Escalation Policy |

---

## 🔮 Future Improvements

- **Embedding-based retrieval**: Explore semantic retrieval using embeddings and FAISS for improved paraphrase handling
- **Conditional orchestration**: Add branching workflows such as automatic re-retrieval when the Critic recommends revision
- **Additional policy domains**: Expand the knowledge base with HR, IT security, acceptable use, and onboarding policies
- **Conversation memory**: Support multi-turn follow-up questions within a session
- **Audit logging**: Store workflow traces and decisions for compliance review
- **Role-aware responses**: Tailor policy visibility based on employee role or department
- **PDF ingestion**: Parse structured PDF policy documents directly into the retrieval pipeline

---

## 📸 Screenshots

### Main Dashboard

![Main Dashboard](screenshots/dashboard.png)

---

### Multi-Agent Workflow Trace

![Agent Workflow](screenshots/agent-trace.png)

---

### Final Answer, Confidence & Policy Risk Classification

![Final Answer](screenshots/final-answer.png)

---

### Guardrail Injection Blocking

![Guardrail Blocking](screenshots/guardrail-block.png)

## 🧠 Design Philosophy

WorkBridge AI intentionally prioritises:

- explainability over autonomous behaviour
- grounded retrieval over speculative generation
- lightweight orchestration over heavy infrastructure
- practical enterprise workflows over experimental agent autonomy

The goal was to build a safe, explainable, and deployable enterprise AI workflow assistant within a practical development timeline.

## 🧑‍💻 Built With

- [Streamlit](https://streamlit.io) — UI framework
- [OpenAI GPT-4o-mini](https://platform.openai.com) — LLM backbone
- [python-dotenv](https://pypi.org/project/python-dotenv/) — Environment variable management

---

## ⚖️ Disclaimer

WorkBridge is just a prototype demonstration. Answers are generated from local policy documents and should be verified with the appropriate department before taking action on sensitive matters.
