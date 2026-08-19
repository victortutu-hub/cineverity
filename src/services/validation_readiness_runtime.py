"""Deterministic closed-input helpers for Validation Readiness runtime v0.1."""

from __future__ import annotations

import json
from typing import Any, Sequence

from src.contracts.director_intent import DirectorIntentContract
from src.contracts.physical_constraints import PhysicalConstraintsContract
from src.contracts.scene_planning import ScenePlanningContract
from src.contracts.validation_readiness import (
    ValidationArtisticDeviationReference,
    ValidationDependencyReference,
    ValidationHookReference,
    ValidationPhysicalConflictReference,
    ValidationPhysicalConstraintReference,
    ValidationReadinessContract,
    ValidationReadinessScope,
    ValidationUnresolvedReference,
)
from src.services.scene_planning_runtime import (
    _canonical_contract_sha256,
    validate_exact_physical_scope_for_director,
    validate_exact_scene_planning_scope,
)


class ValidationReadinessScopeValidationError(ValueError):
    """Raised when a readiness candidate changes the runtime-owned input scope."""


def validate_runtime_inputs(
    director_json: str,
    physical_constraints_json: str,
    scene_planning_json: str,
) -> tuple[DirectorIntentContract, PhysicalConstraintsContract, ScenePlanningContract]:
    """Parse and preflight all three upstream snapshots before any model work."""
    director = DirectorIntentContract.model_validate_json(director_json)
    physical = PhysicalConstraintsContract.model_validate_json(physical_constraints_json)
    validate_exact_physical_scope_for_director(director, physical)
    scene = ScenePlanningContract.model_validate_json(scene_planning_json)
    validate_exact_scene_planning_scope(scene, director, physical)
    return director, physical, scene


def derive_validation_readiness_scope(
    director: DirectorIntentContract,
    physical: PhysicalConstraintsContract,
    scene: ScenePlanningContract,
) -> ValidationReadinessScope:
    """Derive the complete ordered ValidationReadinessScope from validated inputs."""
    validate_exact_physical_scope_for_director(director, physical)
    validate_exact_scene_planning_scope(scene, director, physical)
    return ValidationReadinessScope(
        director_contract_sha256=_canonical_contract_sha256(director),
        physical_constraints_contract_sha256=_canonical_contract_sha256(physical),
        scene_planning_contract_sha256=_canonical_contract_sha256(scene),
        director_validation_target_ids=[item.id for item in director.validation_targets],
        director_scene_entity_ids=[item.id for item in director.scene_entities],
        director_physical_question_ids=[item.id for item in director.physical_questions],
        physical_constraint_references=[
            ValidationPhysicalConstraintReference(
                physical_constraint_id=item.id,
                status=item.status,
                director_scene_entity_ids=list(item.director_scene_entity_ids),
                director_physical_question_ids=list(item.director_physical_question_ids),
            )
            for item in physical.constraints
        ],
        physical_conflict_references=[
            ValidationPhysicalConflictReference(
                physical_conflict_id=item.id,
                resolution_status=item.resolution_status,
                physical_constraint_ids=list(item.constraint_ids),
                director_physical_question_ids=list(item.director_physical_question_ids),
            )
            for item in physical.conflicts
        ],
        unresolved_physical_constraint_references=[
            ValidationUnresolvedReference(
                unresolved_physical_constraint_id=item.id,
                director_scene_entity_ids=list(item.director_scene_entity_ids),
                director_physical_question_ids=list(item.director_physical_question_ids),
            )
            for item in physical.unresolved_constraints
        ],
        artistic_deviation_references=[
            ValidationArtisticDeviationReference(
                artistic_deviation_id=item.id,
                deviation_type=item.deviation_type,
                requires_explicit_artist_acceptance=item.requires_explicit_artist_acceptance,
                director_scene_entity_ids=list(item.director_scene_entity_ids),
                director_physical_question_ids=list(item.director_physical_question_ids),
            )
            for item in physical.artistic_deviations
        ],
        scene_validation_hook_references=[
            ValidationHookReference(
                scene_validation_hook_id=item.id,
                kind=item.kind,
                director_validation_target_ids=list(item.director_validation_target_ids),
                physical_constraint_ids=list(item.physical_constraint_ids),
                physical_conflict_ids=list(item.physical_conflict_ids),
                unresolved_physical_constraint_ids=list(item.unresolved_physical_constraint_ids),
                artistic_deviation_ids=list(item.artistic_deviation_ids),
                dependency_ids=list(item.dependency_ids),
            )
            for item in scene.validation_hooks
        ],
        scene_dependency_references=[
            ValidationDependencyReference(
                scene_dependency_id=dependency.id,
                validation_hook_ids=[
                    hook.id for hook in scene.validation_hooks if dependency.id in hook.dependency_ids
                ],
            )
            for dependency in scene.dependencies
        ],
    )


def build_validation_readiness_packet(
    director: DirectorIntentContract,
    physical: PhysicalConstraintsContract,
    scene: ScenePlanningContract,
) -> dict[str, Any]:
    """Build the closed, trust-separated model packet from validated objects only."""
    expected_scope = derive_validation_readiness_scope(director, physical, scene)
    return {
        "authoritative_runtime": {"expected_input_scope": expected_scope.model_dump(mode="json")},
        "validated_context": {
            "director": director.model_dump(mode="json"),
            "physical_constraints": physical.model_dump(mode="json"),
            "scene_planning": scene.model_dump(mode="json"),
        },
    }


def render_validation_readiness_packet(packet: dict[str, Any]) -> str:
    """Render packet JSON deterministically without changing semantic list ordering."""
    return json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False)


def extract_validation_readiness_text_from_adk_events(events: Sequence[dict[str, Any]]) -> str:
    """Return joined non-thought text only; metadata never becomes contract data."""
    chunks: list[str] = []
    for event in events:
        for part in (event.get("content") or {}).get("parts") or []:
            if not part.get("thought") and part.get("text"):
                chunks.append(part["text"])
    text = "".join(chunks).strip()
    if not text:
        raise ValueError("No model text response found in ADK events.")
    return text


async def query_validation_readiness_once(
    app: Any,
    director: DirectorIntentContract,
    physical: PhysicalConstraintsContract,
    scene: ScenePlanningContract,
) -> str:
    """Preflight, render, and invoke exactly one injected ADK app query."""
    message = render_validation_readiness_packet(
        build_validation_readiness_packet(director, physical, scene)
    )
    events = []
    async for event in app.async_stream_query(
        user_id="cineverity-local-validation-readiness",
        message=message,
    ):
        events.append(event)
    return extract_validation_readiness_text_from_adk_events(events)


def validate_exact_validation_readiness_scope(
    candidate: ValidationReadinessContract,
    director: DirectorIntentContract,
    physical: PhysicalConstraintsContract,
    scene: ScenePlanningContract,
) -> None:
    """Require exact, ordered candidate fidelity to the runtime-derived scope."""
    expected_scope = derive_validation_readiness_scope(director, physical, scene)
    if candidate.input_scope != expected_scope:
        raise ValidationReadinessScopeValidationError(
            "Candidate ValidationReadinessScope does not exactly match the runtime-derived input scope."
        )


def accept_validation_readiness_candidate(
    raw_text: str,
    director: DirectorIntentContract,
    physical: PhysicalConstraintsContract,
    scene: ScenePlanningContract,
) -> ValidationReadinessContract:
    """Parse frozen contract validators first, then enforce runtime-owned scope fidelity."""
    candidate = ValidationReadinessContract.model_validate_json(raw_text)
    validate_exact_validation_readiness_scope(candidate, director, physical, scene)
    return candidate


async def synthesize_validation_readiness(
    app: Any,
    director: DirectorIntentContract,
    physical: PhysicalConstraintsContract,
    scene: ScenePlanningContract,
) -> ValidationReadinessContract:
    """Use a single model call and accept only an exactly scoped candidate."""
    # Direct callers cannot bypass upstream-pair fidelity merely by skipping the runner.
    validate_exact_physical_scope_for_director(director, physical)
    validate_exact_scene_planning_scope(scene, director, physical)
    raw_text = await query_validation_readiness_once(app, director, physical, scene)
    return accept_validation_readiness_candidate(raw_text, director, physical, scene)
