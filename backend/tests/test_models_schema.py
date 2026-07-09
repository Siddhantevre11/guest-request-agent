import pytest
from pydantic import ValidationError

from app.models import IntentResult, ProposedChange


def _assert_every_object_forbids_additional_properties(node):
    """OpenAI's strict structured-output mode requires every object-typed
    schema node to explicitly set additionalProperties: false. A bare `dict`
    field produces an unconstrained object schema and is rejected outright --
    caught via a live integration call, not by any mock (a 400 from the real
    API, not something a fake LLM client could ever surface)."""
    if isinstance(node, dict):
        if node.get("type") == "object":
            assert node.get("additionalProperties") is False, node
        for value in node.values():
            _assert_every_object_forbids_additional_properties(value)
    elif isinstance(node, list):
        for item in node:
            _assert_every_object_forbids_additional_properties(item)


def test_intent_result_schema_is_strict_structured_output_compatible():
    schema = IntentResult.model_json_schema()
    _assert_every_object_forbids_additional_properties(schema)
    if "$defs" in schema:
        _assert_every_object_forbids_additional_properties(schema["$defs"])


def test_proposed_change_never_accepts_a_date_field():
    """The LLM must never propose a date -- it isn't given the guest's actual
    booking, so any date it produced would be a guess. Dates are resolved
    deterministically from the resolved Booking instead. extra="forbid" makes
    this a structural guarantee, not a prompting convention."""
    with pytest.raises(ValidationError):
        ProposedChange(date="2026-08-05", new_checkout_time="13:00")
