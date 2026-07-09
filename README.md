# Guest Request Agent

An agent that reads inbound short-term-rental guest messages, figures out what each guest needs (property questions, booking changes, upsells), resolves it against real booking/availability/SOP data, and either handles it or hands it to the host — remembering context across messages, and **never inventing** availability, pricing, or booking state.

## Two boundaries

1. **LLM proposes; deterministic code decides anything with consequences.** The model only classifies inbound messages and drafts outbound wording. Consequential facts render from real data into fixed template slots — never hand-typed by the model.
2. **Confidence boundary.** Each Intent is scored individually; low-confidence Intents are clarified or escalated, never guessed. Retries happen only on transient tool failures.

## Architecture

**Next.js + React** (frontend + thin BFF) ⇄ HTTP ⇄ **Python / FastAPI** hosting a **LangGraph** agent graph. Two UIs: guest chat, and a host dashboard with separate **Approvals** (one-click) and **Escalations** (concise summary) queues. In-memory stores for the build; production infra (Postgres checkpoints, Redis, Kafka, MCP) is spoken, not built.

## Running it

**Backend** (FastAPI + LangGraph agent):
```
cd backend
.venv/Scripts/python.exe -m pip install -r requirements.txt   # first time
.venv/Scripts/python.exe -m pytest                             # 25 tests
export OPENAI_API_KEY=sk-...                                   # real classify()/draft() calls
.venv/Scripts/python.exe -m uvicorn app.server:app --reload
```
`app/server.py` wires the real `OpenAILLMClient` (backed by `langchain_openai.ChatOpenAI`)
into `create_app`. Tests never hit the real API — they inject a stub at the same seam
(`FakeLLMClient`, or a fake chat-model object for `OpenAILLMClient` itself).

**Frontend** (Next.js — guest chat at `/`, host dashboard at `/host`):
```
cd frontend
npm install       # first time
cp .env.example .env.local   # BACKEND_URL, defaults to http://localhost:8000
npm run dev
npm test          # vitest, 7 tests
```

## Docs

- [`CONTEXT.md`](./CONTEXT.md) — domain glossary (ubiquitous language)
- [`docs/PRD.md`](./docs/PRD.md) — product requirements
- [`docs/adr/`](./docs/adr/) — architecture decision records (0001–0013)
- [`interview-system-design.svg`](./interview-system-design.svg) — query-flow sketch (north star)
