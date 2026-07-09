# Guest Request Agent

Handles inbound guest messages for a short-term rental host: classifying what the guest needs, resolving it against real booking/availability data, and drafting a reply — without ever inventing facts that have consequences (availability, pricing, booking state).

## Language

**Intent**:
A single thing a guest message is asking for, classified by the LLM. A message may contain multiple Intents (e.g. a checkout-time question and a wifi question in one message). Each Intent carries its own confidence score — confidence is scored per-Intent, not once for the whole message, so one clear Intent can proceed while an ambiguous one is clarified or escalated. The LLM proposes the confidence number; deterministic code applies the threshold. The threshold is risk-tiered, not global: low bar for property-question (low stakes, easily corrected), high bar for booking-change and upsell (touches real reservations/money).
_Avoid_: request, topic, category

**Escalate**:
A fast, non-blocking handoff to a human host — logs the request and returns immediately without waiting for the human to act. The human's eventual response is a separate follow-up, never part of the current turn's reply.
_Avoid_: block, wait for human, defer

**SOP notes**:
A small set of host-authored reference documents (wifi password, house rules, check-in steps, etc.) that `answer_from_notes` reads from directly. Already in-memory and small enough that no separate caching layer is needed for this scope.
_Avoid_: cache, knowledge base, docs cache

**Memory**:
A structured summary of what's already been resolved in a guest's conversation (e.g. which intents were answered, which are pending escalation, what upsell was offered and whether it was answered) — not a raw message transcript. Fed back into classification each turn so the agent doesn't re-ask or re-offer something already settled.
_Avoid_: transcript, chat history, conversation log

**Conversation**:
A single message thread between one guest and the host, bound by the platform to exactly one Booking. A guest with multiple bookings has multiple Conversations, one per booking. Memory and booking lookup are keyed by `(guest_id, conversation_id)`; the agent never guesses which booking a message refers to — the channel already resolved it.
_Avoid_: chat, thread (when ambiguous), session

**Booking**:
A guest's reservation at a property, held in the (in-memory, for the build) data store. The source of truth for dates, pricing, and stay details — the LLM reads these via tools and never invents them. Resolved deterministically from a Conversation, not inferred from message content.
_Avoid_: reservation, trip, stay

**Upsell**:
An agent-initiated offer to add a real, available gap night before a guest's Booking. Distinct from reactive intents in that the guest didn't ask for it — so it is gated by deterministic suppression rules (must be a real gap from calendar data, not already offered/declined, and no complaint present in the current message) before it's ever surfaced to the guest.
_Avoid_: cross-sell, promotion, offer (bare)

**Approval**:
A structured, one-click host-facing item on the happy path — a valid proposed booking change the agent prepared (guest wants X, availability confirms it's possible, host approves or denies). Fast to clear.
_Avoid_: request, confirmation, ticket

**Escalation**:
A host-facing item created when something went wrong or is uncertain (low-confidence intent, repeated tool failure) and the agent can't safely proceed. Carries a concise summary — what's happening and what the host needs to do — not a verbose dump. Kept in a separate queue from Approvals so clean one-click items aren't buried under problems.
_Avoid_: error, ticket, alert

**Graceful miss**:
The agent's response when a property question isn't covered by the SOP notes: a truthful negative plus real, retrieved alternatives ("I don't see X listed, but the notes mention Y and Z"). Not an Escalation — small property questions are answered by the agent, not punted to the host. Both the negative and the alternatives must be grounded in retrieved note content; suggesting a fabricated alternative is still inventing.
_Avoid_: fallback, apology, no-match

**Pending item**:
An offer or proposed change awaiting the guest's response, held in Memory (e.g. an offered Upsell, or a proposed change the guest hasn't confirmed). A guest Affirmation is resolved against the Pending item(s), not against message content alone.
_Avoid_: open offer, outstanding request

**Affirmation**:
A guest message ("yes", "sounds good") that only has meaning relative to a Pending item. The LLM classifies it as an affirmation; deterministic code binds it to the specific Pending item. Affirming never auto-commits a booking mutation — it produces a proposed change routed to the host as an Approval.
_Avoid_: confirmation, acceptance, yes-intent
