# Two distinct host-facing item types: Approval vs. Escalation

Both booking-change proposals and low-confidence/failure handoffs reach the host, but they demand different actions: a proposed change is a happy-path, one-click yes/no; a genuine escalation is a problem the host must read and handle. We decided to keep them as two distinct item types in two queues rather than one undifferentiated "needs host" pile — conflating them buries clean approvals under real problems and undercuts the "few clicks for the host" goal. Deterministic code already knows which path it took, so it tags the item type for free.

An Escalation carries a concise summary — what's happening and what the host needs to do — not a verbose transcript or data dump. The point is to let the host grasp and act quickly, not to hand them raw logs.
