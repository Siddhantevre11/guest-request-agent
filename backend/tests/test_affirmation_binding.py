from app.bookings import BookingLookup
from app.main import create_app
from app.memory import get_memory
from app.models import IntentResult
from fastapi.testclient import TestClient
from tests.doubles import FakeLLMClient

UPSELL_INTENT = IntentResult(type="upsell", confidence=0.9, query="gap night")
AFFIRMATION_INTENT = IntentResult(type="affirmation", confidence=0.9, query="yes")


def make_client(intents):
    llm = FakeLLMClient(intents=intents, draft_template="{{fact:0}}")
    return TestClient(create_app(llm, booking_lookup=BookingLookup(failure_rate=0.0)))


def test_affirmation_binds_to_the_single_pending_upsell_and_creates_an_approval_not_a_commit():
    client = make_client(intents=[[UPSELL_INTENT], [AFFIRMATION_INTENT]])

    client.post("/message", json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "hi!"})
    response = client.post(
        "/message", json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "yes"}
    )

    reply = response.json()["reply"]
    # never auto-committed -- still routes through the host, same as any booking change
    assert "checking with your host" in reply.lower()
    approvals = client.get("/host/approvals").json()
    assert len(approvals) == 1
    assert approvals[0]["change"] == {"type": "add_gap_night", "date": "2026-07-31", "price": 120}


def test_bare_affirmation_with_no_pending_offer_is_a_no_op():
    client = make_client(intents=[[AFFIRMATION_INTENT]])

    response = client.post(
        "/message", json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "yes"}
    )

    assert response.json()["reply"].strip() == ""
    assert client.get("/host/approvals").json() == []


def test_ambiguous_affirmation_clarifies_once_then_escalates():
    client = make_client(intents=[[AFFIRMATION_INTENT], [AFFIRMATION_INTENT]])
    memory = get_memory("guest-1", "conv-1")
    memory["upsell_offers"] = {
        "2026-07-31": {"status": "offered", "price": 120},
        "2026-08-06": {"status": "offered", "price": 90},
    }

    first = client.post(
        "/message", json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "yes"}
    ).json()["reply"]
    second = client.post(
        "/message", json={"guest_id": "guest-1", "conversation_id": "conv-1", "message": "yes"}
    ).json()["reply"]

    assert "which one" in first.lower()
    assert "flagged this for your host" in second
    assert len(client.get("/host/escalations").json()) == 1
    # never guessed and created an approval for either ambiguous item
    assert client.get("/host/approvals").json() == []
