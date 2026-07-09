from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .approvals import get_approval, list_pending_approvals
from .bookings import BOOKINGS, BookingLookup
from .escalations import list_escalations
from .graph import BookingLookupFn, build_graph
from .llm import LLMClient
from .models import MessageRequest, MessageResponse
from .notifications import add_notification, pop_notifications


class HostDecisionRequest(BaseModel):
    approval_id: str
    decision: Literal["approve", "deny"]


class HostDecisionResponse(BaseModel):
    status: Literal["approved", "denied"]
    guest_notification: str
    booking: Optional[dict] = None


def _guest_notification_for_approval(change: dict) -> str:
    parts = [f"Great news — your checkout has been extended to {change['new_checkout_time']}"]
    if change.get("fee"):
        parts.append(f" for a ${change['fee']} fee")
    return "".join(parts) + "."


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

    @app.get("/host/approvals")
    def get_approvals() -> list:
        return list_pending_approvals()

    @app.get("/host/escalations")
    def get_escalations() -> list:
        return list_escalations()

    @app.post("/host/decision", response_model=HostDecisionResponse)
    def post_host_decision(req: HostDecisionRequest) -> HostDecisionResponse:
        approval = get_approval(req.approval_id)
        if approval is None:
            raise HTTPException(status_code=404, detail="approval not found")

        if req.decision == "deny":
            approval["status"] = "denied"
            notification = "Unfortunately your host couldn't accommodate this change this time."
            add_notification(approval["guest_id"], approval["conversation_id"], notification)
            return HostDecisionResponse(status="denied", guest_notification=notification, booking=None)

        # Approve: execute the pre-specified diff deterministically -- never
        # re-enters the LLM (ADR-0012).
        booking_key = (approval["guest_id"], approval["conversation_id"])
        booking = BOOKINGS[booking_key]
        change = approval["change"]
        if "new_checkout_time" in change:
            booking["checkout_time"] = change["new_checkout_time"]
        if "fee" in change:
            booking["fee"] = change["fee"]
        approval["status"] = "approved"

        notification = _guest_notification_for_approval(change)
        add_notification(approval["guest_id"], approval["conversation_id"], notification)

        return HostDecisionResponse(status="approved", guest_notification=notification, booking=dict(booking))

    @app.get("/notifications")
    def get_notifications(guest_id: str, conversation_id: str) -> list:
        return pop_notifications(guest_id, conversation_id)

    return app
