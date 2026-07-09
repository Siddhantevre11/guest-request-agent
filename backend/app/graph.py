import copy
from typing import Callable, List, TypedDict

from langgraph.graph import END, StateGraph

from .approvals import create_approval
from .bookings import Booking, BookingLookupError
from .calendar_store import check_availability, find_upsell
from .escalations import create_escalation
from .gating import (
    AMBIGUOUS_AFFIRMATION_QUESTION,
    BOOKING_CHANGE_PENDING_MESSAGE,
    BOOKING_CHANGE_UNAVAILABLE_MESSAGE,
    BOOKING_DEPENDENT_TYPES,
    BOOKING_FAILURE_MESSAGE,
    GUEST_ESCALATED_NOTE,
    partition_intents,
    process_held_back_intent,
)
from .llm import LLMClient
from .memory import get_memory
from .models import IntentResult
from .retry import retry
from .tools import answer_from_notes, graceful_miss_message

BookingLookupFn = Callable[[str, str], Booking]


class GraphState(TypedDict):
    guest_id: str
    conversation_id: str
    message: str
    intents: List[IntentResult]
    facts: List[str]
    held_back_notes: List[str]
    escalation_notes: List[str]
    reply: str


def build_graph(llm: LLMClient, booking_lookup: BookingLookupFn):
    def classify_node(state: GraphState) -> dict:
        memory = get_memory(state["guest_id"], state["conversation_id"])
        return {"intents": llm.classify(state["message"], copy.deepcopy(memory))}

    def handle_node(state: GraphState) -> dict:
        proceeding, held_back = partition_intents(state["intents"])
        memory = get_memory(state["guest_id"], state["conversation_id"])

        booking: Booking | None = None
        booking_failed = False
        if any(intent.type in BOOKING_DEPENDENT_TYPES for intent in proceeding):
            try:
                booking = retry(lambda: booking_lookup(state["guest_id"], state["conversation_id"]))
            except BookingLookupError:
                booking_failed = True

        facts: List[str] = []
        escalation_notes: List[str] = []
        for intent in proceeding:
            if intent.type in BOOKING_DEPENDENT_TYPES and booking_failed:
                escalation_notes.append(BOOKING_FAILURE_MESSAGE)
            elif intent.type == "property_question":
                topic = intent.query or state["message"]
                passages = answer_from_notes(topic)
                facts.append(passages[0] if passages else graceful_miss_message())
                if topic not in memory["answered_topics"]:
                    memory["answered_topics"].append(topic)
            elif intent.type == "booking_change" and booking is not None:
                # date is always the resolved booking's own checkout date --
                # never proposed by the LLM, which is never given the booking
                # and would otherwise have to guess (e.g. "my last day").
                date = booking["checkout"]
                change = intent.proposed_change.model_dump(exclude_none=True) if intent.proposed_change else {}
                change["date"] = date
                if check_availability(date):
                    create_approval(
                        guest_id=state["guest_id"],
                        conversation_id=state["conversation_id"],
                        booking_id=booking["booking_id"],
                        change=change,
                    )
                    facts.append(BOOKING_CHANGE_PENDING_MESSAGE)
                else:
                    facts.append(BOOKING_CHANGE_UNAVAILABLE_MESSAGE)
            elif intent.type == "upsell" and booking is not None:
                gap = find_upsell(booking)
                offers = memory.setdefault("upsell_offers", {})
                has_complaint = any(i.sentiment == "negative" for i in state["intents"])
                if gap and gap["date"] not in offers and not has_complaint:
                    offers[gap["date"]] = {"status": "offered", "price": gap["price"]}
                    facts.append(
                        f"We noticed {gap['date']} is open right before your stay — "
                        f"want to add it for ${gap['price']}?"
                    )
                # else: suppressed silently -- never surfaced to the guest (ADR-0006)
            elif intent.type == "affirmation" and booking is not None:
                offers = memory.setdefault("upsell_offers", {})
                pending_dates = [d for d, info in offers.items() if info["status"] == "offered"]
                if len(pending_dates) == 1:
                    gap_date = pending_dates[0]
                    price = offers[gap_date]["price"]
                    offers[gap_date]["status"] = "accepted"
                    # never auto-commit -- affirming converts the offer into a
                    # proposed change routed to the host as an Approval (ADR-0011).
                    create_approval(
                        guest_id=state["guest_id"],
                        conversation_id=state["conversation_id"],
                        booking_id=booking["booking_id"],
                        change={"type": "add_gap_night", "date": gap_date, "price": price},
                    )
                    facts.append(BOOKING_CHANGE_PENDING_MESSAGE)
                elif len(pending_dates) > 1:
                    if not memory.get("affirmation_clarify_attempted"):
                        memory["affirmation_clarify_attempted"] = True
                        facts.append(AMBIGUOUS_AFFIRMATION_QUESTION)
                    else:
                        create_escalation(
                            state["guest_id"],
                            state["conversation_id"],
                            "Guest affirmation is ambiguous between multiple pending offers — needs manual review.",
                        )
                        facts.append(GUEST_ESCALATED_NOTE)
                # else: nothing pending to bind to -- no-op

        held_back_notes: List[str] = []
        for intent in held_back:
            guest_note, escalation_reason = process_held_back_intent(intent, memory)
            held_back_notes.append(guest_note)
            if escalation_reason is not None:
                create_escalation(state["guest_id"], state["conversation_id"], escalation_reason)

        return {"facts": facts, "held_back_notes": held_back_notes, "escalation_notes": escalation_notes}

    def draft_node(state: GraphState) -> dict:
        if not state["facts"] and not state["held_back_notes"] and not state["escalation_notes"]:
            # nothing resolved and nothing suppressed needs mentioning (e.g. a
            # silently-gated upsell) -- deterministic code decides there's
            # nothing to say, rather than the LLM inventing filler.
            return {"reply": ""}
        reply = llm.draft(state["facts"])
        for i, fact in enumerate(state["facts"]):
            reply = reply.replace(f"{{{{fact:{i}}}}}", fact)
        for note in [*state["held_back_notes"], *state["escalation_notes"]]:
            reply = f"{reply} {note}"
        return {"reply": reply}

    graph = StateGraph(GraphState)
    graph.add_node("classify", classify_node)
    graph.add_node("handle", handle_node)
    graph.add_node("draft", draft_node)
    graph.set_entry_point("classify")
    graph.add_edge("classify", "handle")
    graph.add_edge("handle", "draft")
    graph.add_edge("draft", END)
    return graph.compile()
