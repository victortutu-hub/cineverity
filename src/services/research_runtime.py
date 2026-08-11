"""Deterministic Research synthesis packet and three-gate acceptance pipeline."""

from __future__ import annotations

import json
from typing import Any, Sequence

from src.contracts.director_intent import DirectorIntentContract
from src.contracts.research_evidence import ResearchEvidenceContract, ResearchScope
from src.services.research_retrieval import (
    RetrievalRegistry,
    derive_research_scope,
    validate_research_contract_provenance,
)


class ResearchScopeValidationError(ValueError):
    """Raised when candidate scope membership differs from the Director-derived scope."""


def _canonical_scope(scope: ResearchScope) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[tuple[str, str], ...]]:
    def members(values: list[str], label: str) -> tuple[str, ...]:
        if any(not value for value in values) or len(values) != len(set(values)):
            raise ResearchScopeValidationError(f"{label} contains duplicate or blank identifiers.")
        return tuple(sorted(values))

    pairs = [(item.entity_id, item.parameter) for item in scope.director_material_unknown_parameters]
    if any(not entity_id or not parameter for entity_id, parameter in pairs) or len(pairs) != len(set(pairs)):
        raise ResearchScopeValidationError("Material unknown scope contains duplicate or blank pairs.")
    return (
        members(scope.director_research_requirement_ids, "Research requirement scope"),
        members(scope.director_physical_question_ids, "Physical question scope"),
        members(scope.director_scene_entity_ids, "Scene entity scope"),
        tuple(sorted(pairs)),
    )


def validate_exact_research_scope(candidate: ResearchEvidenceContract, director: DirectorIntentContract) -> None:
    """Require exact scope membership while deliberately ignoring list ordering."""
    expected = _canonical_scope(derive_research_scope(director))
    actual = _canonical_scope(candidate.research_scope)
    if actual != expected:
        raise ResearchScopeValidationError("Candidate ResearchScope does not exactly match Director-derived scope membership.")


def _json_value(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def build_synthesis_packet(director: DirectorIntentContract, registry: RetrievalRegistry) -> dict[str, Any]:
    """Build a JSON-safe closed evidence snapshot with explicit deterministic list ordering."""
    scope = derive_research_scope(director)
    allowed_sources = []
    untrusted_content = []
    for source_id in sorted(registry.sources_by_id):
        source = registry.sources_by_id[source_id]
        allowed_sources.append({
            "source_id": source.source_id,
            "url": source.provider_url,
            "title": source.provider_title,
            "publication_date": _json_value(source.provider_publication_date),
            "accessed_at": source.first_retrieved_at_utc.isoformat(),
            "publisher": None,
            "source_type": "other",
        })
        occurrences = sorted(
            source.occurrences,
            key=lambda item: (
                item.director_research_requirement_id,
                item.search_id,
                item.result_rank,
                item.retrieved_at_utc.isoformat(),
            ),
        )
        untrusted_content.append({
            "source_id": source.source_id,
            "occurrences": [
                {
                    "director_research_requirement_id": item.director_research_requirement_id,
                    "search_id": item.search_id,
                    "session_id": item.session_id,
                    "result_rank": item.result_rank,
                    "retrieved_at_utc": item.retrieved_at_utc.isoformat(),
                    "excerpts": list(item.excerpts),
                }
                for item in occurrences
            ],
        })

    return {
        "trusted_runtime": {
            "research_scope": scope.model_dump(mode="json"),
            "director_research_context": {
                "research_required": [item.model_dump(mode="json") for item in director.research_required],
                "physical_questions": [item.model_dump(mode="json") for item in director.physical_questions],
                "scene_entities": [item.model_dump(mode="json") for item in director.scene_entities],
                "material_intent": [item.model_dump(mode="json") for item in director.material_intent],
            },
            "search_executions": [
                {
                    "director_research_requirement_id": search.director_research_requirement_id,
                    "objective": search.objective,
                    "search_queries": list(search.search_queries),
                    "search_id": search.search_id,
                    "session_id": search.session_id,
                    "raw_result_count": search.result_count,
                    "eligible_source_ids": list(search.eligible_source_ids),
                    "retrieved_at_utc": search.retrieved_at_utc.isoformat(),
                }
                for search in registry.searches
            ],
            "allowed_sources": allowed_sources,
        },
        "untrusted_provider_content": untrusted_content,
    }


def render_synthesis_packet(packet: dict[str, Any]) -> str:
    """Render the immutable packet deterministically without Unicode mutation."""
    return json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False)


def extract_research_text_from_adk_events(events: Sequence[dict[str, Any]]) -> str:
    """Extract non-thought text parts while ignoring metadata-only ADK events."""
    text_chunks: list[str] = []
    for event in events:
        content = event.get("content") or {}
        for part in content.get("parts") or []:
            if part.get("thought"):
                continue
            if part.get("text"):
                text_chunks.append(part["text"])
    text = "".join(text_chunks).strip()
    if not text:
        raise ValueError("No model text response found in ADK events.")
    return text


def accept_research_candidate(raw_text: str, director: DirectorIntentContract, registry: RetrievalRegistry) -> ResearchEvidenceContract:
    """Parse then gate a candidate; no repair, retry, or partial return is possible."""
    candidate = ResearchEvidenceContract.model_validate_json(raw_text)
    validate_exact_research_scope(candidate, director)
    validate_research_contract_provenance(candidate, registry)
    return candidate


async def synthesize_with_app(app: Any, director: DirectorIntentContract, registry: RetrievalRegistry) -> ResearchEvidenceContract:
    """Run a supplied ADK app once over the closed packet, then apply all acceptance gates."""
    packet = build_synthesis_packet(director, registry)
    events = []
    async for event in app.async_stream_query(user_id="cineverity-local-research", message=render_synthesis_packet(packet)):
        events.append(event)
    return accept_research_candidate(extract_research_text_from_adk_events(events), director, registry)
