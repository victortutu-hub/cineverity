"""Strict Director runtime boundary for hosted orchestration."""

from __future__ import annotations

from typing import Any, Sequence

from src.contracts.director_intent import DirectorIntentContract


def extract_director_text_from_adk_events(events: Sequence[dict[str, Any]]) -> str:
    """Return only non-thought text, preserving raw candidate bytes/chunks."""
    chunks: list[str] = []
    for event in events:
        for part in (event.get("content") or {}).get("parts") or []:
            if not part.get("thought") and part.get("text"):
                chunks.append(part["text"])
    if not chunks:
        raise ValueError("No model text response found in ADK events.")
    return "".join(chunks)


def accept_director_candidate(raw_text: str) -> DirectorIntentContract:
    """Strictly parse one raw candidate without cleanup, repair, or fallback."""
    return DirectorIntentContract.model_validate_json(raw_text)


async def synthesize_director(app: Any, brief: str) -> DirectorIntentContract:
    """Invoke an injected ADK app once and accept only strict contract JSON."""
    if not isinstance(brief, str) or not brief.strip():
        raise ValueError("Creative brief must be a non-empty string.")

    events = []
    async for event in app.async_stream_query(
        user_id="cineverity-hosted-director",
        message=brief,
    ):
        events.append(event)
    return accept_director_candidate(extract_director_text_from_adk_events(events))
