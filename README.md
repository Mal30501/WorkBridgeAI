# 🛡️ PolicyPilot AI

**Guardrailed Multi-Agent Enterprise Policy Assistant**

PolicyPilot is a production-style prototype that answers employee questions about company policies using a coordinated pipeline of AI agents. Every answer is grounded in official internal policy documents — the system is designed to retrieve before it answers, validate before it responds, and block unsafe inputs before they reach the model.

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

Each agent is a separate Python module. The Streamlit app (`app.py`) orchestrates them in sequence and displays each agent's output in the UI for full traceability.

---

## 🤖 Agent Descriptions

| Agent | Role | Key Behaviour |
|---|---|---|
| **Guardrail** | Input safety | Regex-based detection of prompt injection, jailbreak phrases, off-topic requests. Blocks before any LLM call. |
| **Planner** | Query decomposition | Uses GPT-4o-mini to break the question into 2–4 actionable retrieval steps. Makes the plan visible in the trace. |
| **Retriever** | Policy search | Keyword-overlap scoring over chunked local `.txt` policy files. No vector DB required. Returns top-K scored chunks. |
| **Analyst** | Answer generation | RAG-style generation. System prompt explicitly forbids using knowledge outside the provided context. |
| **Critic** | Quality validation | Structured evaluation: grounding, accuracy, completeness, confidence, recommendation (APPROVE / APPROVE WITH CAVEAT / REVISE). |
| **Response** | Output formatting | Formats the final answer for a non-technical employee. Appends confidence warnings or caveats as needed. |

---

## 📁 Project Structure

```
policypilot/
│
├── agents/
│   ├── guardrail_agent.py   # Input safety & injection detection
│   ├── planner_agent.py     # Query decomposition
│   ├── retriever_agent.py   # Local policy document search
│   ├── analyst_agent.py     # Grounded answer generation (RAG)
│   ├── critic_agent.py      # Answer validation
│   └── response_agent.py   # Final answer formatting
│
├── policies/
│   ├── refund_policy.txt       # Refund authorization rules
│   ├── pii_policy.txt          # PII definitions and data handling
│   └── escalation_policy.txt   # Escalation triggers and procedures
│
├── utils/
│   └── openai_helper.py    # Centralised OpenAI client wrapper
│
├── app.py                  # Streamlit UI & pipeline orchestration
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourname/policypilot.git
cd policypilot
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
| What information is considered PII? | PII Policy |
| What if a customer threatens legal action? | Escalation Policy |
| How long does a standard refund take? | Refund Policy |
| What happens if I suspect a data breach? | PII + Escalation Policy |

---

## 🔮 Future Improvements

- **Vector search**: Replace keyword scoring with embeddings (e.g. `sentence-transformers` + FAISS) for semantic retrieval
- **More policy documents**: Add HR, IT security, travel expense, acceptable use policies
- **LangGraph orchestration**: Implement conditional branching (e.g. re-retrieve if Critic recommends REVISE)
- **Conversation memory**: Allow multi-turn follow-up questions within a session
- **Audit logging**: Log all queries and agent outputs to a database for compliance review
- **User roles**: Show/hide certain policy sections based on employee role
- **PDF support**: Ingest scanned or formatted PDF policy documents

---

## 📸 Screenshots

*[Add screenshots of the Streamlit UI here after running the app]*

- Main query interface with sidebar
- Agent trace panel showing all 6 steps
- Retrieved source snippets panel
- Final answer with confidence indicators

---

## 🧑‍💻 Built With

- [Streamlit](https://streamlit.io) — UI framework
- [OpenAI GPT-4o-mini](https://platform.openai.com) — LLM backbone
- [python-dotenv](https://pypi.org/project/python-dotenv/) — Environment variable management

---

## ⚖️ Disclaimer

PolicyPilot is a prototype demonstration. Answers are generated from local policy documents and should be verified with the appropriate department before taking action on sensitive matters.
