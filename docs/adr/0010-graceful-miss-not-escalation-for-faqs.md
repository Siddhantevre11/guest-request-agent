# Graceful miss on property FAQs, not escalation

Escalating every property question the SOP notes don't cover defeats the automation — the whole point is quick self-serve answers for guests and fewer interruptions for hosts. But we still can't let the LLM answer from its general prior (that's inventing). The resolution distinguishes two things that were being conflated:

- **Inventing** (forbidden): asserting a positive fact not in the data — "yes, there's a hair dryer in the closet."
- **Graceful miss** (allowed, preferred): a truthful negative plus real alternatives — "I don't see a hair dryer listed for this property, but the notes mention an iron and a laundry room."

So on a notes miss, the agent answers gracefully itself rather than escalating. The hard constraint that keeps this safe: both the negative and any "but we do have…" alternatives must be grounded in retrieved note content — the alternatives are retrieved, never fabricated, or we've just moved the invention from the missing item to the suggested one. Escalation is reserved for consequential intents (booking changes, tool failures, low-confidence consequential intent), not property trivia.

This overrides the earlier instinct to escalate on any notes miss.
