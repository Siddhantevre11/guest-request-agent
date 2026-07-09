# Guest Request Agent

An agent that reads inbound short-term-rental guest messages, figures out what each guest needs (property questions, booking changes, upsells), resolves it against real booking/availability/SOP data, and either handles it or hands it to the host — remembering context across messages, and **never inventing** availability, pricing, or booking state.

## Two boundaries

1. **LLM proposes; deterministic code decides anything with consequences.** The model only classifies inbound messages and drafts outbound wording. Consequential facts render from real data into fixed template slots — never hand-typed by the model.
2. **Confidence boundary.** Each Intent is scored individually; low-confidence Intents are clarified or escalated, never guessed. Retries happen only on transient tool failures.

## Architecture

**Next.js + React** (frontend + thin BFF) ⇄ HTTP ⇄ **Python / FastAPI** hosting a **LangGraph** agent graph. Two UIs: guest chat, and a host dashboard with separate **Approvals** (one-click) and **Escalations** (concise summary) queues. In-memory stores for the build; production infra (Postgres checkpoints, Redis, Kafka, MCP) is spoken, not built.

## Docs

- [`CONTEXT.md`](./CONTEXT.md) — domain glossary (ubiquitous language)
- [`docs/PRD.md`](./docs/PRD.md) — product requirements
- [`docs/adr/`](./docs/adr/) — architecture decision records (0001–0013)
- [`interview-system-design.svg`](./interview-system-design.svg) — query-flow sketch (north star)
