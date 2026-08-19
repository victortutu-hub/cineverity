"""Deterministic preflight helpers for Scene Planning runtime v0.1."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Sequence

from src.contracts.director_intent import DirectorIntentContract
from src.contracts.physical_constraints import PhysicalConstraintsContract, PhysicalConstraintsScope
from src.contracts.scene_planning import (
    ArtisticDeviationScopeReference,
    PhysicalConflictScopeReference,
    PhysicalConstraintScopeReference,
    SceneMaterialIdentityScopeReference,
    ScenePlanningScope,
    ScenePlanningContract,
    UnresolvedPhysicalConstraintScopeReference,
)


class DirectorPhysicalScopeValidationError(ValueError):
    """Raised when accepted Physical Constraints scope is not faithful to the supplied Director contract."""


def _canonical_contract_text(contract: Any) -> str:
    """Render a validated contract using CineVerity's frozen canonical JSON convention."""
    return json.dumps(
        contract.model_dump(mode="json"),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"


def _canonical_contract_bytes(contract: Any) -> bytes:
    """Return explicit UTF-8 canonical contract bytes without a BOM."""
    return _canonical_contract_text(contract).encode("utf-8")


def _canonical_contract_sha256(contract: Any) -> str:
    """Bind a hash to the exact validated contract snapshot, not historical authorship."""
    return hashlib.sha256(_canonical_contract_bytes(contract)).hexdigest()


def _director_owned_physical_scope(director: DirectorIntentContract) -> dict[str, list[Any]]:
    """Project only the Director-owned fields Physical Constraints must preserve."""
    return {
        "director_physical_question_ids": [item.id for item in director.physical_questions],
        "director_research_requirement_ids": [item.id for item in director.research_required],
        "director_scene_entity_ids": [item.id for item in director.scene_entities],
        "director_material_unknown_parameters": [
            {"entity_id": item.entity_id, "parameter": parameter}
            for item in director.material_intent
            for parameter in item.unknown_parameters
        ],
        "director_validation_target_ids": [item.id for item in director.validation_targets],
    }


def _canonical_director_owned_scope(scope: PhysicalConstraintsScope | dict[str, list[Any]]) -> tuple[Any, ...]:
    """Defensively compare Director-owned membership without hiding blanks or duplicates."""
    def values(field_name: str) -> list[Any]:
        if isinstance(scope, dict):
            return scope[field_name]
        return getattr(scope, field_name)

    def members(field_name: str) -> tuple[str, ...]:
        items = list(values(field_name))
        if any(not item for item in items):
            raise DirectorPhysicalScopeValidationError(f"{field_name} contains blank identifiers.")
        if len(items) != len(set(items)):
            raise DirectorPhysicalScopeValidationError(f"{field_name} contains duplicate identifiers.")
        return tuple(sorted(items))

    pairs = [
        (item["entity_id"], item["parameter"])
        if isinstance(item, dict)
        else (item.entity_id, item.parameter)
        for item in values("director_material_unknown_parameters")
    ]
    if any(not entity_id or not parameter for entity_id, parameter in pairs):
        raise DirectorPhysicalScopeValidationError("director_material_unknown_parameters contains blank pairs.")
    if len(pairs) != len(set(pairs)):
        raise DirectorPhysicalScopeValidationError("director_material_unknown_parameters contains duplicate pairs.")

    return (
        members("director_physical_question_ids"),
        members("director_research_requirement_ids"),
        members("director_scene_entity_ids"),
        tuple(sorted(pairs)),
        members("director_validation_target_ids"),
    )


def validate_exact_physical_scope_for_director(
    director: DirectorIntentContract,
    physical: PhysicalConstraintsContract,
) -> None:
    """Require order-insensitive exact membership for the five Director-owned fields."""
    expected = _canonical_director_owned_scope(_director_owned_physical_scope(director))
    actual = _canonical_director_owned_scope(physical.input_scope)
    if actual != expected:
        raise DirectorPhysicalScopeValidationError(
            "PhysicalConstraintsContract Director-owned scope does not exactly match the supplied Director contract."
        )


def validate_runtime_inputs(
    director_json: str,
    physical_constraints_json: str,
) -> tuple[DirectorIntentContract, PhysicalConstraintsContract]:
    """Parse and cross-validate inputs before future packet or model work can begin."""
    director = DirectorIntentContract.model_validate_json(director_json)
    physical = PhysicalConstraintsContract.model_validate_json(physical_constraints_json)
    validate_exact_physical_scope_for_director(director, physical)
    return director, physical


def derive_scene_planning_scope(
    director: DirectorIntentContract,
    physical: PhysicalConstraintsContract,
) -> ScenePlanningScope:
    """Derive the authoritative, ordered Scene Planning scope from validated inputs."""
    validate_exact_physical_scope_for_director(director, physical)
    return ScenePlanningScope(
        director_contract_sha256=_canonical_contract_sha256(director),
        physical_constraints_contract_sha256=_canonical_contract_sha256(physical),
        director_scene_entity_ids=[item.id for item in director.scene_entities],
        director_validation_target_ids=[item.id for item in director.validation_targets],
        director_physical_question_ids=[item.id for item in director.physical_questions],
        director_material_unknown_parameters=[
            {"entity_id": item.entity_id, "parameter": parameter}
            for item in director.material_intent
            for parameter in item.unknown_parameters
        ],
        physical_constraint_references=[
            PhysicalConstraintScopeReference(
                physical_constraint_id=item.id,
                status=item.status,
                director_scene_entity_ids=list(item.director_scene_entity_ids),
                director_physical_question_ids=list(item.director_physical_question_ids),
                related_material_unknown_parameters=list(item.related_material_unknown_parameters),
            )
            for item in physical.constraints
        ],
        physical_conflict_references=[
            PhysicalConflictScopeReference(
                physical_conflict_id=item.id,
                resolution_status=item.resolution_status,
                physical_constraint_ids=list(item.constraint_ids),
                director_physical_question_ids=list(item.director_physical_question_ids),
            )
            for item in physical.conflicts
        ],
        unresolved_physical_constraint_references=[
            UnresolvedPhysicalConstraintScopeReference(
                unresolved_physical_constraint_id=item.id,
                director_scene_entity_ids=list(item.director_scene_entity_ids),
                director_physical_question_ids=list(item.director_physical_question_ids),
                related_material_unknown_parameters=list(item.related_material_unknown_parameters),
            )
            for item in physical.unresolved_constraints
        ],
        artistic_deviation_references=[
            ArtisticDeviationScopeReference(
                artistic_deviation_id=item.id,
                deviation_type=item.deviation_type,
                requires_explicit_artist_acceptance=item.requires_explicit_artist_acceptance,
                director_scene_entity_ids=list(item.director_scene_entity_ids),
                director_physical_question_ids=list(item.director_physical_question_ids),
                related_material_unknown_parameters=list(item.related_material_unknown_parameters),
            )
            for item in physical.artistic_deviations
        ],
        material_identity_references=[
            SceneMaterialIdentityScopeReference(
                physical_constraint_id=constraint.id,
                scene_entity_id=identity.scene_entity_id,
                status=identity.status,
                identity_label=identity.identity_label,
            )
            for constraint in physical.constraints
            for identity in constraint.material_identity_references
        ],
    )

def build_scene_planning_packet(
    director: DirectorIntentContract,
    physical: PhysicalConstraintsContract,
) -> dict[str, Any]:
    """Build the deterministic model packet with explicit runtime/data trust separation."""
    expected_scope = derive_scene_planning_scope(director, physical)
    return {
        "authoritative_runtime": {
            "expected_input_scope": expected_scope.model_dump(mode="json"),
        },
        "untrusted_input_data": {
            "director_context": director.model_dump(mode="json"),
            "physical_constraints_context": physical.model_dump(mode="json"),
        },
    }


def render_scene_planning_packet(packet: dict[str, Any]) -> str:
    """Render the deterministic model-message packet without altering list order or Unicode."""
    return json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False)

def extract_scene_planning_text_from_adk_events(events: Sequence[dict[str, Any]]) -> str:
    """Extract non-thought text parts and reject metadata-only ADK responses."""
    chunks: list[str] = []
    for event in events:
        for part in (event.get("content") or {}).get("parts") or []:
            if not part.get("thought") and part.get("text"):
                chunks.append(part["text"])
    text = "".join(chunks).strip()
    if not text:
        raise ValueError("No model text response found in ADK events.")
    return text


async def query_scene_planning_once(
    app: Any,
    director: DirectorIntentContract,
    physical: PhysicalConstraintsContract,
) -> str:
    """Build the preflighted packet, invoke an injected app once, and return raw model text."""
    message = render_scene_planning_packet(build_scene_planning_packet(director, physical))
    events = []
    async for event in app.async_stream_query(
        user_id="cineverity-local-scene-planning",
        message=message,
    ):
        events.append(event)
    return extract_scene_planning_text_from_adk_events(events)

class ScenePlanningScopeValidationError(ValueError):
    """Raised when agent output does not faithfully preserve runtime-derived Scene Planning input scope."""


def validate_exact_scene_planning_scope(
    candidate: ScenePlanningContract,
    director: DirectorIntentContract,
    physical: PhysicalConstraintsContract,
) -> None:
    """Require the candidate scope to equal the ordered scope derived from runtime inputs."""
    expected_scope = derive_scene_planning_scope(director, physical)
    if candidate.input_scope != expected_scope:
        raise ScenePlanningScopeValidationError(
            "Candidate ScenePlanningScope does not exactly match the runtime-derived input scope."
        )


def accept_scene_planning_candidate(
    raw_text: str,
    director: DirectorIntentContract,
    physical: PhysicalConstraintsContract,
) -> ScenePlanningContract:
    """Parse once with frozen validators, then require exact runtime-owned scope fidelity."""
    candidate = ScenePlanningContract.model_validate_json(raw_text)
    validate_exact_scene_planning_scope(candidate, director, physical)
    return candidate


async def synthesize_scene_planning(
    app: Any,
    director: DirectorIntentContract,
    physical: PhysicalConstraintsContract,
) -> ScenePlanningContract:
    """Invoke the existing single-call transport path, then accept or reject once."""
    raw_text = await query_scene_planning_once(app, director, physical)
    return accept_scene_planning_candidate(raw_text, director, physical)