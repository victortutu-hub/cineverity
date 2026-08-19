"""Validation Readiness Contract v0.1: deterministic preflight, never execution results."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, StrictBool, model_validator

from src.contracts.director_intent import StrictModel
from src.contracts.physical_constraints import (
    ArtisticDeviationType,
    PhysicalAssessmentStatus,
    PhysicalConflictResolutionStatus,
)
from src.contracts.scene_planning import SceneValidationHookKind


class ValidationReadinessState(str, Enum):
    structurally_checkable = "structurally_checkable"
    ready_for_execution = "ready_for_execution"
    blocked = "blocked"
    cannot_validate_yet = "cannot_validate_yet"


class ValidationExecutionState(str, Enum):
    not_required = "not_required"
    not_executed = "not_executed"
    unavailable = "unavailable"


class ValidationRequirementClass(str, Enum):
    contract_preflight = "contract_preflight"
    renderer_execution = "renderer_execution"
    simulation_execution = "simulation_execution"
    measurement = "measurement"
    external_scientific_verification = "external_scientific_verification"


class ValidationSubjectKind(str, Enum):
    physical_constraint = "physical_constraint"
    physical_conflict = "physical_conflict"
    unresolved_physical_constraint = "unresolved_physical_constraint"
    artistic_deviation = "artistic_deviation"


class ValidationPhysicalConstraintReference(StrictModel):
    physical_constraint_id: str = Field(..., min_length=1)
    status: PhysicalAssessmentStatus
    director_scene_entity_ids: list[str]
    director_physical_question_ids: list[str]


class ValidationPhysicalConflictReference(StrictModel):
    physical_conflict_id: str = Field(..., min_length=1)
    resolution_status: PhysicalConflictResolutionStatus
    physical_constraint_ids: list[str]
    director_physical_question_ids: list[str]


class ValidationUnresolvedReference(StrictModel):
    unresolved_physical_constraint_id: str = Field(..., min_length=1)
    director_scene_entity_ids: list[str]
    director_physical_question_ids: list[str]


class ValidationArtisticDeviationReference(StrictModel):
    artistic_deviation_id: str = Field(..., min_length=1)
    deviation_type: ArtisticDeviationType
    requires_explicit_artist_acceptance: StrictBool
    director_scene_entity_ids: list[str]
    director_physical_question_ids: list[str]


class ValidationHookReference(StrictModel):
    scene_validation_hook_id: str = Field(..., min_length=1)
    kind: SceneValidationHookKind
    director_validation_target_ids: list[str]
    physical_constraint_ids: list[str]
    physical_conflict_ids: list[str]
    unresolved_physical_constraint_ids: list[str]
    artistic_deviation_ids: list[str]
    dependency_ids: list[str]


class ValidationDependencyReference(StrictModel):
    """A dependency plus authoritative Scene Planning hook bindings."""
    scene_dependency_id: str = Field(..., min_length=1)
    validation_hook_ids: list[str]


class ValidationReadinessScope(StrictModel):
    director_contract_sha256: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    physical_constraints_contract_sha256: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    scene_planning_contract_sha256: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    director_validation_target_ids: list[str]
    director_scene_entity_ids: list[str]
    director_physical_question_ids: list[str]
    physical_constraint_references: list[ValidationPhysicalConstraintReference]
    physical_conflict_references: list[ValidationPhysicalConflictReference]
    unresolved_physical_constraint_references: list[ValidationUnresolvedReference]
    artistic_deviation_references: list[ValidationArtisticDeviationReference]
    scene_validation_hook_references: list[ValidationHookReference]
    scene_dependency_references: list[ValidationDependencyReference]


class ValidationTargetReadiness(StrictModel):
    director_validation_target_id: str = Field(..., min_length=1)
    state: ValidationReadinessState
    execution_state: ValidationExecutionState
    validation_hook_ids: list[str]
    physical_constraint_ids: list[str]
    physical_conflict_ids: list[str]
    unresolved_physical_constraint_ids: list[str]
    artistic_deviation_ids: list[str]
    dependency_ids: list[str]
    prerequisites: list[str]
    limitations: list[str]


class ValidationHookReadiness(StrictModel):
    scene_validation_hook_id: str = Field(..., min_length=1)
    state: ValidationReadinessState
    execution_state: ValidationExecutionState
    director_validation_target_ids: list[str]
    physical_constraint_ids: list[str]
    physical_conflict_ids: list[str]
    unresolved_physical_constraint_ids: list[str]
    artistic_deviation_ids: list[str]
    dependency_ids: list[str]
    prerequisites: list[str]
    limitations: list[str]


class ValidationSubjectReadiness(StrictModel):
    subject_kind: ValidationSubjectKind
    subject_id: str = Field(..., min_length=1)
    state: ValidationReadinessState
    execution_state: ValidationExecutionState
    director_validation_target_ids: list[str]
    validation_hook_ids: list[str]
    dependency_ids: list[str]
    prerequisites: list[str]
    limitations: list[str]


class ValidationDependencyCoverage(StrictModel):
    scene_dependency_id: str = Field(..., min_length=1)
    validation_hook_ids: list[str]
    prerequisites: list[str]
    limitations: list[str]


class ValidationReadinessContract(StrictModel):
    contract_version: Literal["0.1"]
    agent: Literal["validation_readiness_agent"]
    input_scope: ValidationReadinessScope
    target_readiness: list[ValidationTargetReadiness]
    hook_readiness: list[ValidationHookReadiness]
    subject_readiness: list[ValidationSubjectReadiness]
    dependency_coverage: list[ValidationDependencyCoverage]
    required_execution_classes: list[ValidationRequirementClass]
    readiness_summary: str = Field(..., min_length=1)
    limitations: list[str]

    @model_validator(mode="after")
    def validate_contract(self):
        def unique(values: list[str], label: str) -> set[str]:
            if any(not value for value in values) or len(values) != len(set(values)):
                raise ValueError(f"Duplicate or blank {label}")
            return set(values)

        def refs(values: list[str], allowed: set[str], label: str) -> None:
            if any(not value for value in values) or len(values) != len(set(values)) or not set(values) <= allowed:
                raise ValueError(f"Invalid {label}")

        scope = self.input_scope
        targets = unique(scope.director_validation_target_ids, "scope validation target IDs")
        entities = unique(scope.director_scene_entity_ids, "scope scene entity IDs")
        questions = unique(scope.director_physical_question_ids, "scope physical question IDs")
        dependencies = unique(
            [item.scene_dependency_id for item in scope.scene_dependency_references],
            "scope dependency IDs",
        )
        constraints = unique([item.physical_constraint_id for item in scope.physical_constraint_references], "scope physical constraint IDs")
        conflicts = unique([item.physical_conflict_id for item in scope.physical_conflict_references], "scope physical conflict IDs")
        unresolved = unique([item.unresolved_physical_constraint_id for item in scope.unresolved_physical_constraint_references], "scope unresolved IDs")
        deviations = unique([item.artistic_deviation_id for item in scope.artistic_deviation_references], "scope artistic deviation IDs")
        hooks = unique([item.scene_validation_hook_id for item in scope.scene_validation_hook_references], "scope validation hook IDs")

        for item in scope.physical_constraint_references:
            refs(item.director_scene_entity_ids, entities, "constraint scope entities")
            refs(item.director_physical_question_ids, questions, "constraint scope questions")
        for item in scope.physical_conflict_references:
            refs(item.physical_constraint_ids, constraints, "conflict scope constraints")
            refs(item.director_physical_question_ids, questions, "conflict scope questions")
        for item in scope.unresolved_physical_constraint_references:
            refs(item.director_scene_entity_ids, entities, "unresolved scope entities")
            refs(item.director_physical_question_ids, questions, "unresolved scope questions")
        for item in scope.artistic_deviation_references:
            refs(item.director_scene_entity_ids, entities, "deviation scope entities")
            refs(item.director_physical_question_ids, questions, "deviation scope questions")
        for item in scope.scene_validation_hook_references:
            refs(item.director_validation_target_ids, targets, "hook scope targets")
            refs(item.physical_constraint_ids, constraints, "hook scope constraints")
            refs(item.physical_conflict_ids, conflicts, "hook scope conflicts")
            refs(item.unresolved_physical_constraint_ids, unresolved, "hook scope unresolved")
            refs(item.artistic_deviation_ids, deviations, "hook scope deviations")
            refs(item.dependency_ids, dependencies, "hook scope dependencies")
        dependency_scope = {item.scene_dependency_id: item for item in scope.scene_dependency_references}
        for item in scope.scene_dependency_references:
            refs(item.validation_hook_ids, hooks, "dependency scope hooks")
        for hook in scope.scene_validation_hook_references:
            for dependency_id in hook.dependency_ids:
                if hook.scene_validation_hook_id not in dependency_scope[dependency_id].validation_hook_ids:
                    raise ValueError("Dependency scope must preserve authoritative hook binding")

        target_records = unique([item.director_validation_target_id for item in self.target_readiness], "target readiness IDs")
        hook_records = unique([item.scene_validation_hook_id for item in self.hook_readiness], "hook readiness IDs")
        if target_records != targets:
            raise ValueError("Validation target readiness must cover every scoped Director validation target exactly once")
        if hook_records != hooks:
            raise ValueError("Validation hook readiness must cover every scoped Scene Planning hook exactly once")

        dependency_records = unique([item.scene_dependency_id for item in self.dependency_coverage], "dependency coverage IDs")
        if dependency_records != dependencies:
            raise ValueError("Dependency coverage must cover every scoped Scene Planning dependency exactly once")

        subject_keys = [(item.subject_kind.value, item.subject_id) for item in self.subject_readiness]
        if any(not subject_id for _, subject_id in subject_keys) or len(subject_keys) != len(set(subject_keys)):
            raise ValueError("Duplicate or blank subject readiness")
        expected_subjects = ({("physical_constraint", value) for value in constraints}
            | {("physical_conflict", value) for value in conflicts}
            | {("unresolved_physical_constraint", value) for value in unresolved}
            | {("artistic_deviation", value) for value in deviations})
        if set(subject_keys) != expected_subjects:
            raise ValueError("Subject readiness must cover every scoped Physical subject exactly once")

        hook_map = {item.scene_validation_hook_id: item for item in scope.scene_validation_hook_references}
        constraint_status = {item.physical_constraint_id: item.status for item in scope.physical_constraint_references}
        deviation_acceptance = {item.artistic_deviation_id: item.requires_explicit_artist_acceptance for item in scope.artistic_deviation_references}

        def state_ok(state: ValidationReadinessState, execution: ValidationExecutionState, label: str) -> None:
            expected = {
                ValidationReadinessState.structurally_checkable: ValidationExecutionState.not_required,
                ValidationReadinessState.ready_for_execution: ValidationExecutionState.not_executed,
                ValidationReadinessState.blocked: ValidationExecutionState.unavailable,
                ValidationReadinessState.cannot_validate_yet: ValidationExecutionState.unavailable,
            }[state]
            if execution is not expected:
                raise ValueError(f"{label} has incompatible readiness and execution state")

        for item in self.target_readiness:
            state_ok(item.state, item.execution_state, "Target readiness")
            refs(item.validation_hook_ids, hooks, "target readiness hooks"); refs(item.physical_constraint_ids, constraints, "target readiness constraints")
            refs(item.physical_conflict_ids, conflicts, "target readiness conflicts"); refs(item.unresolved_physical_constraint_ids, unresolved, "target readiness unresolved")
            refs(item.artistic_deviation_ids, deviations, "target readiness deviations"); refs(item.dependency_ids, dependencies, "target readiness dependencies")
            for hook_id in item.validation_hook_ids:
                if item.director_validation_target_id not in hook_map[hook_id].director_validation_target_ids:
                    raise ValueError("Validation target cannot be reassigned to an unrelated hook")
            for subject_ids, attribute, label in (
                (item.physical_constraint_ids, "physical_constraint_ids", "constraints"),
                (item.physical_conflict_ids, "physical_conflict_ids", "conflicts"),
                (item.unresolved_physical_constraint_ids, "unresolved_physical_constraint_ids", "unresolved"),
                (item.artistic_deviation_ids, "artistic_deviation_ids", "deviations"),
            ):
                if subject_ids and not item.validation_hook_ids:
                    raise ValueError(f"Target readiness {label} require an authoritative hook binding")
                for subject_id in subject_ids:
                    if not any(subject_id in getattr(hook_map[hook_id], attribute) for hook_id in item.validation_hook_ids):
                        raise ValueError(f"Target readiness {label} are not bound to its validation hooks")
        for item in self.hook_readiness:
            state_ok(item.state, item.execution_state, "Hook readiness")
            scope_hook = hook_map[item.scene_validation_hook_id]
            for actual, expected, label in ((item.director_validation_target_ids, scope_hook.director_validation_target_ids, "targets"), (item.physical_constraint_ids, scope_hook.physical_constraint_ids, "constraints"), (item.physical_conflict_ids, scope_hook.physical_conflict_ids, "conflicts"), (item.unresolved_physical_constraint_ids, scope_hook.unresolved_physical_constraint_ids, "unresolved"), (item.artistic_deviation_ids, scope_hook.artistic_deviation_ids, "deviations"), (item.dependency_ids, scope_hook.dependency_ids, "dependencies")):
                if actual != expected:
                    raise ValueError(f"Hook readiness must preserve authoritative hook {label}")
        for item in self.subject_readiness:
            state_ok(item.state, item.execution_state, "Subject readiness")
            refs(item.director_validation_target_ids, targets, "subject readiness targets"); refs(item.validation_hook_ids, hooks, "subject readiness hooks"); refs(item.dependency_ids, dependencies, "subject readiness dependencies")
            hook_attribute = {
                ValidationSubjectKind.physical_constraint: "physical_constraint_ids",
                ValidationSubjectKind.physical_conflict: "physical_conflict_ids",
                ValidationSubjectKind.unresolved_physical_constraint: "unresolved_physical_constraint_ids",
                ValidationSubjectKind.artistic_deviation: "artistic_deviation_ids",
            }[item.subject_kind]
            for hook_id in item.validation_hook_ids:
                if item.subject_id not in getattr(hook_map[hook_id], hook_attribute):
                    raise ValueError("Subject readiness cannot be reassigned to an unrelated validation hook")
                if item.director_validation_target_ids and not set(item.director_validation_target_ids) <= set(hook_map[hook_id].director_validation_target_ids):
                    raise ValueError("Subject readiness targets must be bound by its validation hook")
            if item.subject_kind is ValidationSubjectKind.physical_constraint:
                if constraint_status[item.subject_id] in {PhysicalAssessmentStatus.unsupported, PhysicalAssessmentStatus.indeterminate} and item.state in {ValidationReadinessState.structurally_checkable, ValidationReadinessState.ready_for_execution}:
                    raise ValueError("Unsupported or indeterminate constraint cannot be validation-ready")
                if constraint_status[item.subject_id] is PhysicalAssessmentStatus.conditionally_supported and item.state is ValidationReadinessState.structurally_checkable:
                    raise ValueError("Conditional constraint cannot be unconditionally preflight-checkable")
            elif item.subject_kind is ValidationSubjectKind.physical_conflict:
                if item.state in {ValidationReadinessState.structurally_checkable, ValidationReadinessState.ready_for_execution}:
                    raise ValueError("Physical conflict cannot be validation-ready without an authorized resolution")
            elif item.subject_kind is ValidationSubjectKind.unresolved_physical_constraint:
                if item.state in {ValidationReadinessState.structurally_checkable, ValidationReadinessState.ready_for_execution}:
                    raise ValueError("Unresolved constraint cannot be validation-ready")
            elif deviation_acceptance[item.subject_id] and item.state in {ValidationReadinessState.structurally_checkable, ValidationReadinessState.ready_for_execution}:
                raise ValueError("Artist acceptance requirement cannot be treated as accepted")
        for item in self.dependency_coverage:
            refs(item.validation_hook_ids, hooks, "dependency coverage hooks")
            if item.validation_hook_ids != dependency_scope[item.scene_dependency_id].validation_hook_ids:
                raise ValueError("Dependency coverage must preserve authoritative hook bindings")
        return self
