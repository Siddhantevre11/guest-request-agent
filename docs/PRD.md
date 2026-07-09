# PRD — Guest Request Agent

> Point-of-reference product doc synthesised from the design/grilling session.
> Companion docs: [`CONTEXT.md`](../CONTEXT.md) (glossary) and [`docs/adr/`](./adr/) (ADR-0001…0013).
> Uses the project's ubiquitous language throughout — capitalised terms (Intent, Booking, Conversation, Upsell, Approval, Escalation, Graceful miss, Pending item, Affirmation) are defined in `CONTEXT.md`.

## Problem Statement

A short-term rental host is drowning in repetitive inbound guest messages. A single message might be a booking change ("can I check out late?"), a property question ("what's the wifi password?"), or a moment where an Upsell is possible (a gap night before the guest's stay they could add). Today the host reads, triages, looks up the reservation, and replies to each one by hand — tedious, slow, and easy to drop. Guests, meanwhile, expect near-instant answers; if a reply takes too long they abandon the channel and phone the host directly, defeating the point of the platform.

The host needs the tedious, repetitive work automated on both ends — quick self-serve answers for guests, and only a few clicks for the host — **without** the automation ever inventing availability, pricing, or booking state. Those facts must come from real data, not from a language model's guess.

## Solution

A Guest Request Agent that reads each inbound guest message, figures out what the guest needs (possibly several things at once), resolves each need against real booking/availability/SOP data, and either handles it directly or hands it to the host — remembering context across messages so it never re-asks or re-offers something already settled.

The design rests on two boundaries:

1. **LLM proposes; deterministic code decides anything with consequences.** The model only classifies incoming messages and drafts outgoing wording. Every decision that touches a reservation, money, or the truth of a fact is made by plain deterministic code. Consequential facts are rendered from real data into fixed template slots, never hand-typed by the model.
2. **Confidence boundary.** Each Intent is scored individually; low-confidence Intents are clarified or escalated rather than guessed. Retries happen only on transient tool failures, never on genuine ambiguity (re-running a classifier on the same ambiguous text yields the same answer).

Guests get a single fast consolidated reply per message (target ~30s, hard ceiling ~60s). Hosts get two clean queues: **Approvals** (one-click yes/no on prepared booking changes) and **Escalations** (concise "here's what's happening and what you need to do" summaries for genuine problems).

## User Stories

**Guest — property questions**
1. As a guest, I want to ask for the wifi password and get it instantly, so that I can get online without waiting on the host.
2. As a guest, I want to ask several things in one message (e.g. checkout time *and* wifi) and get all of them answered, so that I don't have to send separate messages.
3. As a guest, I want an honest answer when something isn't documented ("I don't see a hair dryer listed, but the notes mention an iron and a laundry room"), so that I'm not misled by a confident-sounding wrong answer.
4. As a guest, I want the agent to suggest genuinely available alternatives when my exact request isn't covered, so that I still get something useful instead of a dead end.

**Guest — booking changes**
5. As a guest, I want to request a late checkout in plain language, so that I don't have to navigate a form.
6. As a guest, I want to be told promptly "checking with your host, they'll confirm shortly," so that I know my request was understood and is moving.
7. As a guest, I want the confirmation message to state the exact new checkout time and any fee, so that there's no ambiguity about what was agreed.
8. As a guest with multiple bookings, I want each of my message threads to be about the right reservation automatically, so that I never have to specify which trip I mean.

**Guest — upsell**
9. As a guest, I want to be offered a gap night before my stay when one is genuinely available, so that I can extend my trip easily.
10. As a guest, I don't want to be re-offered an extra night I already declined, so that the conversation doesn't feel naggy.
11. As a guest who just reported a problem (e.g. broken AC), I don't want to be pitched an upsell in the same breath, so that I feel heard rather than sold to.
12. As a guest, I want to accept an offer by simply replying "yes," so that I don't have to restate the details.
13. As a guest, I want my "yes" to an extra night to still be confirmed by the host before anything is charged, so that I'm not billed by an automated guess.

**Guest — conversation continuity**
14. As a guest, I want the agent to remember what we've already covered in this conversation, so that I'm not asked the same question twice.
15. As a guest, I want a follow-up like "yes" or "sounds good" to be understood in the context of what was just offered, so that short replies still work.

**Host — automation & control**
16. As a host, I want repetitive guest questions answered without my involvement, so that I reclaim my time.
17. As a host, I want to approve or deny a proposed booking change in one click, so that I stay in control of my reservations without doing the triage.
18. As a host, I never want the agent to change a reservation or charge a guest on its own, so that I retain final say over anything with consequences.
19. As a host, I want a clean Approvals queue separate from Escalations, so that quick one-click items aren't buried under genuine problems.
20. As a host, I want each Escalation to carry a concise summary of what's happening and what I need to do, so that I can act fast without reading raw logs.
21. As a host, I want genuinely ambiguous or failing requests escalated to me, so that the agent never guesses on something consequential.
22. As a host, I want the guest automatically notified of my decision, so that I don't have to write the follow-up.
23. As a host, I want gaps in my SOP notes surfaced when guests ask about undocumented things, so that I can improve my documentation over time.

**System — safety & reliability**
24. As the system, I want each Intent scored for confidence independently, so that a clear Intent can proceed even when another in the same message is ambiguous.
25. As the system, I want risk-tiered confidence thresholds, so that low-stakes questions clear easily while consequential ones require more certainty.
26. As the system, I want to retry a flaky tool/DB lookup a few times before giving up, so that transient failures don't become escalations.
27. As the system, I want to escalate only the Intents that depended on a failed tool, so that unrelated Intents in the same message still get answered.
28. As the system, I never want to invent availability, pricing, or booking facts, so that guests are never given false information.
29. As the system, I want consequential facts rendered from real data into fixed template slots, so that the drafting model can't garble a number that matters.
30. As the system, I want a host approval to execute exactly the pre-specified change deterministically, so that a committed action is never re-interpreted by the model.

## Implementation Decisions

**Architecture (ADR-0013)**
- Split at an HTTP boundary: **Next.js + React** (frontend + thin Node/Next.js BFF: auth, session, serving UIs, proxying) ⇄ HTTP ⇄ **Python / FastAPI** hosting the **LangGraph** agent graph.
- Two distinct UIs: a **guest chat** UI and a **host dashboard** with separate Approvals and Escalations queues (ADR-0008).
- The LangGraph graph mirrors the query-flow design; its checkpointer is in-memory (`MemorySaver`) for the build and maps to `PostgresSaver` in production without changing graph logic.
- LLM provider is OpenAI for the build, called behind a thin swappable wrapper. The hard rules don't depend on the provider (structured outputs / function calling cover classify).

**LLM boundary as graph topology (ADR-0013)**
- Exactly **two** LLM nodes: `classify` (structured output — `intents[]`, each with type + confidence + sentiment) and `draft` (natural wording; consequential facts injected via template slots).
- Pure-Python nodes for everything with consequences: route, gates, retry, verify, upsell suppression, affirmation binding, and the tool stubs.

**API contracts**
- `POST /message` — one guest turn. Input: guest message + conversation identity `(guest_id, conversation_id)`. Output: the single consolidated guest reply plus any Approvals/Escalations created as side effects.
- `POST /host/decision` — a host approve/deny on an Approval. Input: the Approval reference + decision. Output: the executed booking mutation (on approve) and the templated guest notification.

**Intent & confidence (ADR-0001)**
- Confidence is scored **per-Intent**, not once per message. The LLM proposes the number; deterministic code applies the threshold.
- Thresholds are **risk-tiered**: low bar (~0.4) for property-question; high bar (~0.7) for booking-change and upsell.
- Low-confidence handling by risk tier: property-question **clarifies** (one attempt), booking-change/upsell **escalate** immediately. A clarify round-trip that comes back still below the bar escalates rather than looping.

**Reply strategy & latency (ADR-0002)**
- One **consolidated** reply per guest turn, folding in per-Intent status.
- `escalate()` is **fast and non-blocking** — it logs the handoff and returns immediately; the human's reply is a separate later follow-up, never part of the turn's latency budget.
- Latency target ~30s, hard ceiling ~60s.

**Failure handling (ADR-0003)**
- `lookup_booking` is deliberately flaky; retry a few times then escalate.
- **Fixed small retry delay** for the build; exponential backoff is the production upgrade (spoken, not built).
- **Per-Intent failure isolation**: only Intents that depend on the failed tool escalate; independent Intents (e.g. an FAQ via `answer_from_notes`) still resolve in the same consolidated reply. Consolidate tracks, per Intent, which tool results it depended on.

**Memory (ADR-0004)**
- Memory stores a **structured summary of resolved state** (answered Intents, pending Escalations, offered/declined Upsells), not a raw transcript. Fed into `classify` each turn. In-memory dict for the build; Postgres/Redis in production.

**Identity (ADR-0005)**
- Keyed by **`(guest_id, conversation_id)`**; the platform binds each Conversation to exactly one Booking before the message reaches the agent. Resolving a Conversation → Booking is a deterministic lookup, never an LLM inference. Supports guests with multiple bookings (one Conversation each).

**Upsell (ADR-0006)**
- Deterministic code gates an Upsell on **three** conditions, all required: (1) `find_upsell` returns a real gap from actual calendar data; (2) memory shows it wasn't already offered/declined; (3) no complaint/negative sentiment in the current message. The LLM may surface that a gap exists; code decides whether it's offered.

**Booking changes (ADR-0007)**
- The agent **never** mutates a Booking autonomously. It prepares a fully-specified proposed change and routes it to the host as a one-click **Approval**. Guest-facing reply: "checking with your host, they'll confirm shortly." (Future: host-configured auto-approve policy engine — deferred to production.)

**Host queues (ADR-0008)**
- Two distinct item types in two queues: **Approval** (happy-path, one-click) vs. **Escalation** (a problem; concise summary of what's happening and what to do — not a verbose dump). Deterministic code tags the type based on the path it took.

**Fact verification (ADR-0009)**
- High-consequence facts (checkout time, price, dates) are rendered into explicit **template slots** filled directly from tool-returned values; the LLM writes only the connective prose. This sidesteps parsing facts back out of free text. Free-prose fact extraction/comparison is deferred to production hardening.

**Graceful miss (ADR-0010)**
- On a notes miss for a property question, the agent responds with a **Graceful miss** (truthful negative + real retrieved alternatives) rather than escalating. Hard constraint: both the negative and the alternatives must be grounded in **retrieved** note content — a fabricated alternative is still inventing. Escalation is reserved for consequential Intents, not property trivia.

**Affirmation (ADR-0011)**
- The LLM classifies "yes"/"sounds good" as an **Affirmation**; deterministic code binds it to the specific **Pending item** in memory. Affirming **never auto-commits** — it converts an offer into a proposed change routed to the host as an Approval. If two items are pending and the guest sends a bare "yes," the agent **clarifies once**, then escalates if still unclear.

**Loop close (ADR-0012)**
- A host approval executes the **pre-specified diff deterministically** against the data store — it does **not** re-enter the LLM pipeline. The guest notification may use the LLM for friendly wording, but consequential facts fill template slots from the executed change and route to the right guest via the Approval's `conversation_id`. Denial is symmetric: no mutation, templated "host couldn't accommodate" with optional LLM softening.

**Tools (in-memory stubs for the build)**
- `lookup_booking(guest_id)` — flaky (intermittent failure, to exercise retry).
- `check_availability(date)` — deterministic.
- `find_upsell(booking, calendar)` — deterministic gap detection.
- `answer_from_notes(question)` — retrieval over the host's SOP notes; returns matching passages (so code can detect a miss), the LLM only phrases them.
- `escalate(reason)` — fast, non-blocking handoff.

## Testing Decisions

**What makes a good test here:** assert on **external behaviour at a seam**, never on internal implementation. Feed an input to a seam and assert on the output and the observable side effects (the consolidated reply, the Approvals/Escalations created, the booking mutation). Do **not** reach into the router, gates, retry counter, or verifier directly — they are exercised *through* the seams.

**Seams (confirmed with the developer):**
1. **`POST /message` (primary, highest seam)** — the bulk of tests. Given a guest message + prior memory state, assert on the consolidated reply and host-queue side effects. Covers: multi-intent handling, per-Intent confidence & risk-tiered thresholds, clarify-vs-escalate, retry, per-Intent failure isolation, upsell suppression (all three gates), graceful miss, affirmation binding, and memory continuity across turns.
2. **`POST /host/decision` (loop-close seam)** — approve/deny in; assert the deterministic booking mutation happened as pre-specified (no LLM round-trip) and the guest notification carries the exact templated facts.
3. **The LLM wrapper (unavoidable lower seam)** — **stubbed** in tests so `classify`/`draft` are deterministic. We don't test the model; we inject its structured output to drive seams 1 and 2. This is the single place we mock, because non-determinism can't be asserted against.

**Modules tested:** the agent graph via seams 1–2. Deterministic sub-components (router, gates, retry, verifier, upsell suppression, affirmation binding) are covered transitively through seam 1, not in isolation.

**Prior art:** none yet — this is a greenfield repo. These seams establish the pattern: HTTP-boundary behavioural tests with a stubbed LLM.

## Out of Scope

- **Auth / sessions** beyond what the BFF needs to route a message to a Conversation (skipped for the build).
- **Persistent storage** — the build keeps `db`, `memory`, calendar, and SOP notes as **in-memory dicts**. Production infra (Postgres for node-state checkpoints, Redis for hot lookups, Kafka to queue inbound messages under load, an MCP server as a clean swappable tool interface) is **spoken, not built**.
- **Host-configured auto-approval policy engine** — auto-approving low-risk changes within preset rules is a future evolution (ADR-0007), deferred.
- **Exponential backoff** on retries — build uses a fixed small delay; backoff is the production upgrade (ADR-0003).
- **Free-prose fact extraction/verification** — build renders facts via template slots instead (ADR-0009); post-draft claim parsing is production hardening.
- **Trained/dedicated intent classifier** — build uses the LLM classifier; swapping for a trained classifier is a production note.
- **Multi-booking disambiguation from message content** — explicitly avoided; the platform binds a Conversation to one Booking (ADR-0005).

## Further Notes

- The reference sketch is [`interview-system-design.svg`](../interview-system-design.svg) (query-flow diagram). The two boundaries and the "production version, spoken not built" and "scope cuts" callouts in that SVG are the north star.
- Build order (foundation-first): **(1)** Python LangGraph agent core + scripted terminal demo proving every path → **(2)** FastAPI wrapper (`/message`, `/host/decision`) → **(3)** Next.js BFF + guest chat UI → **(4)** host dashboard (Approvals + Escalations). Phase 1 carries the design's substance and de-risks everything above it.
- Guiding principle throughout: automate the tedious, repetitive work on both ends (quick everything for the guest, few clicks for the host) — but never at the cost of inventing a consequential fact.
