# EduAgent

An AI student assistant for education institutions, built around a **tool-calling agent** that reads student data, answers institutional questions via RAG, and **performs real, guarded write operations** (e.g. booking coaching appointments) against a PostgreSQL database.

> Personal project / Vertical AI prototype. All data is synthetic; "Nova Eğitim Kurumları" is a fictional institution.

📹 **Demo video:** _(coming soon)_

---

## Why this project is different

This is not another read-only chatbot. Two things set it apart from a standard RAG or tool-calling demo:

**1. A guarded agent that writes to the database.**
The agent doesn't just retrieve information — it creates coaching appointments as real database rows, with conflict detection and a database-level uniqueness constraint. Giving an LLM write access safely is the core engineering challenge here (see [Security](#security)).

**2. Eval-driven, not "looks fine to me".**
Agent behavior is measured, not eyeballed. A custom eval harness scores tool-selection accuracy and RAG retrieval quality against a labeled test set, producing a reproducible baseline (see [Evaluation](#evaluation)).

---

## What the agent can do

A logged-in student can chat naturally and the agent decides which tool to call:

- **Exam analysis** — "How are my last exams going?" → reads results, interprets trends
- **Schedule** — "What classes do I have?" → returns the weekly schedule
- **Coach info** — "Who is my coach?"
- **Availability** — "What slots are free on Sept 5?" → free hours after removing booked ones
- **Appointment booking** — "Book me 3 PM with my coach" → **writes** a confirmed appointment
- **Institutional Q&A (RAG)** — "What's the attendance policy?" → answers from a knowledge base, says "I don't know" when the answer isn't there

---

## Architecture

Frontend (Next.js) ──HTTP──► Backend (FastAPI)
│
┌───────┴────────┐
│ Agent (Groq) │ ← decides which tool to call
└───────┬────────┘
│
┌─────────────┼─────────────┐
▼ ▼ ▼
Tools (6) RAG (pgvector) Auth (JWT)
│ │
▼ ▼
PostgreSQL (Neon) — student data + vector store



The agent is orchestrated in `agent_calistir`: it sends the user message plus tool definitions to the model, the model chooses a tool, the backend executes it, and the result is fed back for a natural-language answer. Conversation history is passed on each turn so multi-step flows (coach → date → time → booking) keep context.

**Tools:** `get_exam_results`, `get_student_schedule`, `get_coach`, `get_coach_availability`, `create_appointment`, `search_knowledge_base`

---

## Security

The whole design assumes the LLM cannot be trusted with identity or raw database access.

- **Identity never comes from the model.** `student_id` is extracted from the signed JWT (`get_current_student`), never from user input or the LLM. A student physically cannot request another student's data — the tools don't even accept a `student_id` argument.
- **Tool abstraction.** The agent never runs SQL. It calls named tools; each tool applies its own authorization and filtering.
- **Guarded writes.** `create_appointment` validates input (past dates, working hours), checks for conflicts, and relies on a database `UNIQUE(coach_id, tarih, saat)` constraint as the real defense against race conditions — a friendly in-code check for UX, the constraint for correctness.
- **No hallucinated data.** When the knowledge base has no answer, the agent says so instead of inventing one.

---

## Evaluation

A standalone eval harness (`evals/`) measures two layers against a labeled test set. All runs use `temperature=0` for reproducibility.

| Layer | Metric | Baseline |
|-------|--------|----------|
| Tool selection | exact match | **88% (35/40)** |
| RAG retrieval | recall@5 | **100% (18/18)** |

The tool suite deliberately includes hard cases: colloquial Turkish, İ/I casing traps, abbreviations (TYT/AYT), ambiguous one-word queries, and "no tool should fire" cases (greetings, off-topic) — since the most common agent failure is calling a tool when it shouldn't.

Of the 5 tool-selection misses, analysis showed 2 were flaws in the test set's expected answers (multi-turn flows can't be judged in one turn), and 3 were the agent over-eagerly searching the knowledge base for out-of-scope institutional questions. The baseline is kept honest rather than tuned to look perfect; full analysis is in [`evals/report.md`](evals/report.md).

Run it:

```bash
python evals/run_eval.py --suite tools
python evals/run_eval.py --suite retrieval
```

---

## Tech stack

- **Backend:** FastAPI, SQLAlchemy
- **Database:** PostgreSQL (Neon) with pgvector
- **Agent LLM:** Groq (openai/gpt-oss-120b)
- **Embeddings:** Gemini (gemini-embedding-001)
- **Auth:** JWT (python-jose) + bcrypt password hashing
- **Frontend:** Next.js, TypeScript, Tailwind CSS

---

## Running locally

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt
# create a .env with DATABASE_URL, GROQ_API_KEY, GEMINI_API_KEY, SECRET_KEY
python create_tables.py
python seed.py                   # synthetic student data
python seed_knowledge.py         # RAG knowledge base
python -m uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Demo login: `ahmet` / `1234`

---

## Deployment

The backend includes a `Dockerfile` and is deploy-ready (container-based, portable to Render/AWS/etc.). It currently runs locally and is demonstrated via the demo video above; a hosted link is a straightforward next step.

---

## Not in scope (yet)

Deliberately left out to keep the MVP focused: parent and admin roles, institution-wide analytics, WhatsApp/mobile, and real student data. The architecture (session-based authorization, tool abstraction) extends to these without redesign.
