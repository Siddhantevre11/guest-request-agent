import copy
from typing import Callable, List, TypedDict

from langgraph.graph import END, StateGraph

from .bookings import Booking, BookingLookupError
from .gating import BOOKING_DEPENDENT_TYPES, BOOKING_FAILURE_MESSAGE, HELD_BACK_MESSAGES, partition_intents
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
                facts.append(
                    f"Your booking (confirmation {booking['booking_id']}) runs "
                    f"{booking['checkin']} to {booking['checkout']}."
                )

        held_back_notes = [HELD_BACK_MESSAGES[intent.type] for intent in held_back]
        return {"facts": facts, "held_back_notes": held_back_notes, "escalation_notes": escalation_notes}

    def draft_node(state: GraphState) -> dict:
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
