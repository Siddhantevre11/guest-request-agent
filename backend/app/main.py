from fastapi import FastAPI

from .bookings import BookingLookup
from .graph import BookingLookupFn, build_graph
from .llm import LLMClient
from .models import MessageRequest, MessageResponse


def create_app(llm_client: LLMClient, booking_lookup: BookingLookupFn | None = None) -> FastAPI:
    app = FastAPI()
    graph = build_graph(llm_client, booking_lookup or BookingLookup())

    @app.post("/message", response_model=MessageResponse)
    def post_message(req: MessageRequest) -> MessageResponse:
        result = graph.invoke(
            {
                "guest_id": req.guest_id,
                "conversation_id": req.conversation_id,
                "message": req.message,
                "intents": [],
                "facts": [],
                "held_back_notes": [],
                "escalation_notes": [],
                "reply": "",
            }
        )
        return MessageResponse(reply=result["reply"])

    return app
