"""Offline tests for the strict hosted Director runtime boundary."""

import asyncio
import inspect
import json

import pytest
from pydantic import ValidationError

from src.services.director_runtime import (
    accept_director_candidate,
    extract_director_text_from_adk_events,
    synthesize_director,
)
from tests.test_scene_planning_runtime import director_payload


class FakeDirectorApp:
    def __init__(self, events):
        self.events = events
        self.calls = []

    async def async_stream_query(self, **kwargs):
        self.calls.append(kwargs)
        for event in self.events:
            yield event


def event(text, *, thought=False):
    return {"content": {"parts": [{"text": text, "thought": thought}]}}


def test_valid_raw_director_json_is_accepted():
    accepted = accept_director_candidate(json.dumps(director_payload()))
    assert accepted.agent == "director_agent"


def test_fenced_director_json_is_rejected_without_cleanup():
    raw = "```json\n" + json.dumps(director_payload()) + "\n```"
    with pytest.raises(ValidationError):
        accept_director_candidate(raw)


def test_malformed_director_json_is_rejected():
    with pytest.raises(ValidationError):
        accept_director_candidate("{not json")


def test_metadata_only_events_are_rejected():
    with pytest.raises(ValueError, match="No model text"):
        extract_director_text_from_adk_events([{"metadata": {"event": "only"}}])


def test_thought_only_text_is_ignored_and_rejected_as_no_candidate():
    with pytest.raises(ValueError, match="No model text"):
        extract_director_text_from_adk_events([event("internal", thought=True)])


def test_thoughts_are_ignored_and_non_thought_chunks_keep_stream_order():
    text = extract_director_text_from_adk_events(
        [event("ignored", thought=True), event("{") , event('"a"'), event("}")]
    )
    assert text == '{"a"}'


def test_synthesis_invokes_supplied_app_once_and_keeps_original_brief():
    app = FakeDirectorApp([event(json.dumps(director_payload()))])
    accepted = asyncio.run(synthesize_director(app, "  original brief  "))
    assert accepted.agent == "director_agent"
    assert app.calls == [{"user_id": "cineverity-hosted-director", "message": "  original brief  "}]


def test_invalid_candidate_does_not_trigger_a_second_invocation():
    app = FakeDirectorApp([event("{}")])
    with pytest.raises(ValidationError):
        asyncio.run(synthesize_director(app, "brief"))
    assert len(app.calls) == 1


def test_strict_runtime_does_not_reference_historical_repair_helper():
    import src.services.director_runtime as runtime

    assert "validate_director_response" not in inspect.getsource(runtime)


@pytest.mark.parametrize("brief", [None, "", "   "])
def test_invalid_brief_fails_before_app_invocation(brief):
    app = FakeDirectorApp([event(json.dumps(director_payload()))])
    with pytest.raises(ValueError, match="Creative brief"):
        asyncio.run(synthesize_director(app, brief))
    assert app.calls == []
