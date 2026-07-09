# Architecture: Next.js/React frontend + BFF over a Python/LangGraph agent service

The agent core is Python + LangGraph (the SVG is literally a node graph; LangGraph models it natively and its checkpointer maps to the prod Postgres-checkpoint note). Next.js cannot run a LangGraph graph in-process, so the system splits at an HTTP boundary:

- **Next.js + React** — frontend plus a thin Node/Next.js API (BFF) layer: auth, session, serving the UIs, proxying to the agent. Two distinct UIs, both falling out of ADR-0008: a guest chat UI and a separate host dashboard with the Approvals queue (one-click) and Escalations queue (concise summaries).
- **Python / FastAPI** — hosts the LangGraph graph. Exposes `POST /message` (a guest turn) and `POST /host/decision` (host approve/deny). Deterministic tools operate over in-memory dicts for the build.

LLM boundary as graph topology: exactly two LLM nodes — `classify` (structured output: intents[] with type, confidence, sentiment) and `draft` (natural wording with consequential facts injected via template slots per ADR-0009). Everything with consequences — route, gates, retry, verify, upsell suppression, affirmation binding — is pure Python between them. Provider is OpenAI for the build, called behind a thin swappable wrapper; the hard rules don't depend on the provider.
