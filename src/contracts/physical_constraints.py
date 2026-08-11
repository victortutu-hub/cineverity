"""Physical Constraints Contract v0.1 for closed Director and Research interpretation."""

from enum import Enum
from typing import Literal, Optional

from pydantic import Field, StrictBool, model_validator

from src.contracts.director_intent import Priority, StrictModel
from src.contracts.research_evidence import EvidenceStatus, MaterialUnknownParameterReference


class PhysicalAssessmentStatus(str, Enum):
    """Physical assessment of a constraint, distinct from question coverage."""

    supported = "supported"
    conditionally_supported = "conditionally_supported"
    conflicting = "conflicting"
    unsupported = "unsupported"
    indeterminate = "indeterminate"


class PhysicalQuestionCoverageState(str, Enum):
    """Whether a Director physical question has been answered by this contract."""

    addressed = "addressed"
    partially_addressed = "partially_addressed"
    unresolved = "unresolved"


class MaterialIdentityStatus(str, Enum):
    """Whether evidence identity can be applied to the referenced scene entity."""

    established_for_scene_entity = "established_for_scene_entity"
    contextual_only = "contextual_only"
    unresolved = "unresolved"


class PhysicalConflictResolutionStatus(str, Enum):
    unresolved = "unresolved"
    context_dependent = "context_dependent"
    artist_decision_required = "artist_decision_required"


class ArtisticDeviationType(str, Enum):
    explicitly_nonphysical = "explicitly_nonphysical"
    artistic_amplification = "artistic_amplification"
    speculative_behavior = "speculative_behavior"


class ResearchFindingProvenanceReference(StrictModel):
    """Minimal finding-to-source projection used for internal provenance validation."""

    finding_id: str = Field(..., min_length=1)
    source_ids: list[str]
    evidence_status: EvidenceStatus


class PhysicalConstraintsScope(StrictModel):
    """Authoritative input snapshot for internal Step 3.1 reference validation."""

    director_physical_question_ids: list[str]
    director_research_requirement_ids: list[str]
    director_scene_entity_ids: list[str]
    director_material_unknown_parameters: list[MaterialUnknownParameterReference]
    director_validation_target_ids: list[str]
    research_finding_provenance: list[ResearchFindingProvenanceReference]
    research_conflict_ids: list[str]
    research_unresolved_question_ids: list[str]


class MaterialIdentityReference(StrictModel):
    """Provenanced material-identity disposition for one scene entity."""

    scene_entity_id: str = Field(..., min_length=1)
    status: MaterialIdentityStatus
    identity_label: Optional[str] = None
    research_finding_ids: list[str]
    source_ids: list[str]
    limitation: Optional[str] = None


class PhysicalConstraint(StrictModel):
    """A physically interpreted consequence with closed Research provenance."""

    id: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=1)
    domain: str = Field(..., min_length=1)
    status: PhysicalAssessmentStatus
    director_physical_question_ids: list[str] = Field(..., min_length=1)
    director_research_requirement_ids: list[str]
    director_scene_entity_ids: list[str]
    related_material_unknown_parameters: list[MaterialUnknownParameterReference]
    research_finding_ids: list[str]
    source_ids: list[str]
    conditions: list[str]
    limitations: list[str]
    material_identity_references: list[MaterialIdentityReference]
    safe_downstream_assumptions: list[str]
    unsafe_downstream_assumptions: list[str]


class PhysicalConflict(StrictModel):
    """An explicit physical conflict, never a silent repair of Director intent."""

    id: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=1)
    constraint_ids: list[str] = Field(..., min_length=1)
    director_physical_question_ids: list[str] = Field(..., min_length=1)
    research_finding_ids: list[str]
    source_ids: list[str]
    research_conflict_ids: list[str]
    conditions: list[str]
    limitations: list[str]
    resolution_status: PhysicalConflictResolutionStatus


class UnresolvedPhysicalConstraint(StrictModel):
    """A physical question that remains indeterminate without invented evidence."""

    id: str = Field(..., min_length=1)
    why_indeterminate: str = Field(..., min_length=1)
    evidence_needed: list[str]
    priority: Priority
    director_physical_question_ids: list[str] = Field(..., min_length=1)
    director_scene_entity_ids: list[str]
    related_material_unknown_parameters: list[MaterialUnknownParameterReference]
    research_finding_ids: list[str]
    source_ids: list[str]
    research_conflict_ids: list[str]
    research_unresolved_question_ids: list[str]
    limitations: list[str]


class ArtisticDeviation(StrictModel):
    """An explicit artistic choice separate from physical assessment."""

    id: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=1)
    deviation_type: ArtisticDeviationType
    director_physical_question_ids: list[str] = Field(..., min_length=1)
    director_scene_entity_ids: list[str]
    related_material_unknown_parameters: list[MaterialUnknownParameterReference]
    constraint_ids: list[str] = Field(..., min_length=1)
    physical_tradeoff: str = Field(..., min_length=1)
    requires_explicit_artist_acceptance: StrictBool


class PhysicalQuestionCoverage(StrictModel):
    """Completion record for exactly one scoped Director physical question."""

    director_physical_question_id: str = Field(..., min_length=1)
    state: PhysicalQuestionCoverageState
    constraint_ids: list[str]
    unresolved_constraint_ids: list[str]
    artistic_deviation_ids: list[str]
    notes: Optional[str] = None


class PhysicalConstraintsContract(StrictModel):
    """Deterministic boundary between accepted evidence and downstream scene planning."""

    contract_version: Literal["0.1"]
    agent: Literal["physical_constraints_agent"]
    input_scope: PhysicalConstraintsScope
    constraints: list[PhysicalConstraint]
    conflicts: list[PhysicalConflict]
    unresolved_constraints: list[UnresolvedPhysicalConstraint]
    artistic_deviations: list[ArtisticDeviation]
    coverage: list[PhysicalQuestionCoverage]
    physical_summary: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_cross_references(self) -> "PhysicalConstraintsContract":
        """Validate closed-scope references and provenance without scientific entailment."""
        def reject_duplicates(values: list[str], label: str) -> None:
            duplicates = sorted({value for value in values if values.count(value) > 1})
            if duplicates:
                raise ValueError(f"Duplicate {label}: {duplicates}")

        def validate_identifier_list(values: list[str], allowed: set[str], label: str) -> None:
            reject_duplicates(values, label)
            if any(not value for value in values):
                raise ValueError(f"Blank {label} are not allowed")
            for value in values:
                if value not in allowed:
                    raise ValueError(f"{label} references unknown identifier: '{value}'")

        scope = self.input_scope
        for values, label in (
            (scope.director_physical_question_ids, "PhysicalConstraintsScope Director physical question IDs"),
            (scope.director_research_requirement_ids, "PhysicalConstraintsScope Director research requirement IDs"),
            (scope.director_scene_entity_ids, "PhysicalConstraintsScope Director scene entity IDs"),
            (scope.director_validation_target_ids, "PhysicalConstraintsScope Director validation target IDs"),
            (scope.research_conflict_ids, "PhysicalConstraintsScope Research conflict IDs"),
            (scope.research_unresolved_question_ids, "PhysicalConstraintsScope Research unresolved question IDs"),
        ):
            reject_duplicates(values, label)
            if any(not value for value in values):
                raise ValueError(f"Blank {label} are not allowed")

        question_ids = set(scope.director_physical_question_ids)
        requirement_ids = set(scope.director_research_requirement_ids)
        entity_ids = set(scope.director_scene_entity_ids)
        validation_target_ids = set(scope.director_validation_target_ids)
        research_conflict_ids = set(scope.research_conflict_ids)
        research_unresolved_ids = set(scope.research_unresolved_question_ids)

        scope_pairs = [
            (reference.entity_id, reference.parameter)
            for reference in scope.director_material_unknown_parameters
        ]
        if len(scope_pairs) != len(set(scope_pairs)):
            raise ValueError("Duplicate MaterialUnknownParameterReference pairs in PhysicalConstraintsScope")
        for entity_id, parameter in scope_pairs:
            if not entity_id or not parameter:
                raise ValueError("Blank MaterialUnknownParameterReference values are not allowed")
            if entity_id not in entity_ids:
                raise ValueError(f"MaterialUnknownParameterReference references unknown scene entity: '{entity_id}'")
        scope_pair_set = set(scope_pairs)

        provenance_sources_by_finding: dict[str, set[str]] = {}
        provenance_status_by_finding: dict[str, EvidenceStatus] = {}
        provenance_ids = [item.finding_id for item in scope.research_finding_provenance]
        reject_duplicates(provenance_ids, "ResearchFindingProvenanceReference finding IDs")
        for item in scope.research_finding_provenance:
            reject_duplicates(item.source_ids, f"ResearchFindingProvenanceReference '{item.finding_id}' source IDs")
            if any(not source_id for source_id in item.source_ids):
                raise ValueError(f"Blank ResearchFindingProvenanceReference '{item.finding_id}' source IDs are not allowed")
            provenance_sources_by_finding[item.finding_id] = set(item.source_ids)
            provenance_status_by_finding[item.finding_id] = item.evidence_status
        finding_ids = set(provenance_sources_by_finding)

        constraint_ids = [item.id for item in self.constraints]
        conflict_ids = [item.id for item in self.conflicts]
        unresolved_ids = [item.id for item in self.unresolved_constraints]
        deviation_ids = [item.id for item in self.artistic_deviations]
        reject_duplicates(constraint_ids, "PhysicalConstraint IDs")
        reject_duplicates(conflict_ids, "PhysicalConflict IDs")
        reject_duplicates(unresolved_ids, "UnresolvedPhysicalConstraint IDs")
        reject_duplicates(deviation_ids, "ArtisticDeviation IDs")
        constraint_id_set = set(constraint_ids)
        unresolved_id_set = set(unresolved_ids)
        deviation_id_set = set(deviation_ids)
        constraints_by_id = {item.id: item for item in self.constraints}
        unresolved_by_id = {item.id: item for item in self.unresolved_constraints}
        deviations_by_id = {item.id: item for item in self.artistic_deviations}

        def validate_material_pairs(values: list[MaterialUnknownParameterReference], label: str) -> None:
            pairs = [(item.entity_id, item.parameter) for item in values]
            if len(pairs) != len(set(pairs)):
                raise ValueError(f"Duplicate {label} material unknown-parameter references")
            for pair in pairs:
                if pair not in scope_pair_set:
                    raise ValueError(f"{label} references unknown Director material parameter: {pair}")

        def validate_source_subset(source_ids: list[str], cited_finding_ids: list[str], label: str) -> None:
            validate_identifier_list(cited_finding_ids, finding_ids, f"{label} Research finding IDs")
            reject_duplicates(source_ids, f"{label} source IDs")
            if any(not source_id for source_id in source_ids):
                raise ValueError(f"Blank {label} source IDs are not allowed")
            allowed_sources = set().union(*(provenance_sources_by_finding[item] for item in cited_finding_ids)) if cited_finding_ids else set()
            if not set(source_ids).issubset(allowed_sources):
                raise ValueError(f"{label} source IDs must be a subset of cited ResearchFinding source IDs")

        for constraint in self.constraints:
            validate_identifier_list(constraint.director_physical_question_ids, question_ids, f"PhysicalConstraint '{constraint.id}' Director physical question IDs")
            validate_identifier_list(constraint.director_research_requirement_ids, requirement_ids, f"PhysicalConstraint '{constraint.id}' Director research requirement IDs")
            validate_identifier_list(constraint.director_scene_entity_ids, entity_ids, f"PhysicalConstraint '{constraint.id}' Director scene entity IDs")
            validate_material_pairs(constraint.related_material_unknown_parameters, f"PhysicalConstraint '{constraint.id}'")
            validate_source_subset(constraint.source_ids, constraint.research_finding_ids, f"PhysicalConstraint '{constraint.id}'")
            cited_statuses = {provenance_status_by_finding[item] for item in constraint.research_finding_ids}
            if constraint.status in {
                PhysicalAssessmentStatus.supported,
                PhysicalAssessmentStatus.conditionally_supported,
                PhysicalAssessmentStatus.conflicting,
            } and (not constraint.research_finding_ids or not constraint.source_ids):
                raise ValueError(f"PhysicalConstraint '{constraint.id}' with status '{constraint.status.value}' requires Research findings and sources")
            if constraint.status is PhysicalAssessmentStatus.supported and EvidenceStatus.supported not in cited_statuses:
                raise ValueError(f"PhysicalConstraint '{constraint.id}' with status 'supported' requires at least one supported Research finding")
            if constraint.status is PhysicalAssessmentStatus.conditionally_supported and not cited_statuses.intersection({EvidenceStatus.supported, EvidenceStatus.partially_supported}):
                raise ValueError(f"PhysicalConstraint '{constraint.id}' with status 'conditionally_supported' requires at least one supported or partially_supported Research finding")
            if constraint.status is PhysicalAssessmentStatus.unsupported and not constraint.research_finding_ids:
                raise ValueError(f"PhysicalConstraint '{constraint.id}' with status 'unsupported' requires at least one Research finding")

            identity_entities = [item.scene_entity_id for item in constraint.material_identity_references]
            reject_duplicates(identity_entities, f"PhysicalConstraint '{constraint.id}' material identity scene entity IDs")
            for identity in constraint.material_identity_references:
                if identity.scene_entity_id not in entity_ids:
                    raise ValueError(f"MaterialIdentityReference references unknown scene entity: '{identity.scene_entity_id}'")
                if identity.scene_entity_id not in constraint.director_scene_entity_ids:
                    raise ValueError(f"MaterialIdentityReference for '{identity.scene_entity_id}' must belong to its PhysicalConstraint scene entities")
                validate_source_subset(identity.source_ids, identity.research_finding_ids, "MaterialIdentityReference")
                if not set(identity.research_finding_ids).issubset(set(constraint.research_finding_ids)):
                    raise ValueError("MaterialIdentityReference Research findings must be cited by its parent PhysicalConstraint")
                if not set(identity.source_ids).issubset(set(constraint.source_ids)):
                    raise ValueError("MaterialIdentityReference source IDs must be a subset of its parent PhysicalConstraint source IDs")
                if identity.status in {
                    MaterialIdentityStatus.established_for_scene_entity,
                    MaterialIdentityStatus.contextual_only,
                }:
                    if not identity.identity_label or not identity.research_finding_ids or not identity.source_ids:
                        raise ValueError(f"MaterialIdentityReference '{identity.status.value}' requires identity_label and Research provenance")
                if identity.status is MaterialIdentityStatus.contextual_only and not identity.limitation:
                    raise ValueError("MaterialIdentityReference 'contextual_only' requires limitation")
                if identity.status is MaterialIdentityStatus.unresolved and identity.identity_label is not None:
                    raise ValueError("MaterialIdentityReference 'unresolved' must not have identity_label")

        for conflict in self.conflicts:
            validate_identifier_list(conflict.constraint_ids, constraint_id_set, f"PhysicalConflict '{conflict.id}' constraint IDs")
            validate_identifier_list(conflict.director_physical_question_ids, question_ids, f"PhysicalConflict '{conflict.id}' Director physical question IDs")
            validate_source_subset(conflict.source_ids, conflict.research_finding_ids, f"PhysicalConflict '{conflict.id}'")
            constraint_question_ids = set().union(*(set(constraints_by_id[item].director_physical_question_ids) for item in conflict.constraint_ids))
            if not set(conflict.director_physical_question_ids).issubset(constraint_question_ids):
                raise ValueError(f"PhysicalConflict '{conflict.id}' physical question IDs must be covered by its referenced constraints")
            validate_identifier_list(conflict.research_conflict_ids, research_conflict_ids, f"PhysicalConflict '{conflict.id}' Research conflict IDs")

        for unresolved in self.unresolved_constraints:
            validate_identifier_list(unresolved.director_physical_question_ids, question_ids, f"UnresolvedPhysicalConstraint '{unresolved.id}' Director physical question IDs")
            validate_identifier_list(unresolved.director_scene_entity_ids, entity_ids, f"UnresolvedPhysicalConstraint '{unresolved.id}' Director scene entity IDs")
            validate_material_pairs(unresolved.related_material_unknown_parameters, f"UnresolvedPhysicalConstraint '{unresolved.id}'")
            validate_source_subset(unresolved.source_ids, unresolved.research_finding_ids, f"UnresolvedPhysicalConstraint '{unresolved.id}'")
            validate_identifier_list(unresolved.research_conflict_ids, research_conflict_ids, f"UnresolvedPhysicalConstraint '{unresolved.id}' Research conflict IDs")
            validate_identifier_list(unresolved.research_unresolved_question_ids, research_unresolved_ids, f"UnresolvedPhysicalConstraint '{unresolved.id}' Research unresolved question IDs")

        for deviation in self.artistic_deviations:
            validate_identifier_list(deviation.director_physical_question_ids, question_ids, f"ArtisticDeviation '{deviation.id}' Director physical question IDs")
            validate_identifier_list(deviation.director_scene_entity_ids, entity_ids, f"ArtisticDeviation '{deviation.id}' Director scene entity IDs")
            validate_material_pairs(deviation.related_material_unknown_parameters, f"ArtisticDeviation '{deviation.id}'")
            validate_identifier_list(deviation.constraint_ids, constraint_id_set, f"ArtisticDeviation '{deviation.id}' constraint IDs")
            constraint_question_ids = set().union(*(set(constraints_by_id[item].director_physical_question_ids) for item in deviation.constraint_ids))
            if not set(deviation.director_physical_question_ids).issubset(constraint_question_ids):
                raise ValueError(f"ArtisticDeviation '{deviation.id}' physical question IDs must be covered by its referenced constraints")

        coverage_question_ids = [item.director_physical_question_id for item in self.coverage]
        reject_duplicates(coverage_question_ids, "PhysicalQuestionCoverage Director physical question IDs")
        if set(coverage_question_ids) != question_ids:
            raise ValueError("PhysicalQuestionCoverage must contain exactly one entry for every scoped Director physical question")
        for item in self.coverage:
            validate_identifier_list(item.constraint_ids, constraint_id_set, f"PhysicalQuestionCoverage '{item.director_physical_question_id}' constraint IDs")
            validate_identifier_list(item.unresolved_constraint_ids, unresolved_id_set, f"PhysicalQuestionCoverage '{item.director_physical_question_id}' unresolved constraint IDs")
            validate_identifier_list(item.artistic_deviation_ids, deviation_id_set, f"PhysicalQuestionCoverage '{item.director_physical_question_id}' artistic deviation IDs")
            if any(item.director_physical_question_id not in constraints_by_id[constraint_id].director_physical_question_ids for constraint_id in item.constraint_ids):
                raise ValueError(f"PhysicalQuestionCoverage '{item.director_physical_question_id}' cannot link a PhysicalConstraint for another physical question")
            if any(item.director_physical_question_id not in unresolved_by_id[unresolved_id].director_physical_question_ids for unresolved_id in item.unresolved_constraint_ids):
                raise ValueError(f"PhysicalQuestionCoverage '{item.director_physical_question_id}' cannot link an UnresolvedPhysicalConstraint for another physical question")
            if any(item.director_physical_question_id not in deviations_by_id[deviation_id].director_physical_question_ids for deviation_id in item.artistic_deviation_ids):
                raise ValueError(f"PhysicalQuestionCoverage '{item.director_physical_question_id}' cannot link an ArtisticDeviation for another physical question")
            if not (item.constraint_ids or item.unresolved_constraint_ids or item.artistic_deviation_ids):
                raise ValueError(f"PhysicalQuestionCoverage '{item.director_physical_question_id}' requires at least one linked record")
            if item.state is PhysicalQuestionCoverageState.unresolved and not item.unresolved_constraint_ids:
                raise ValueError(f"Unresolved PhysicalQuestionCoverage '{item.director_physical_question_id}' requires an unresolved constraint")

        return self