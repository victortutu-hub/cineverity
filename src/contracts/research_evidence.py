"""Research Agent evidence contract v0.1."""

from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import Field, model_validator

from src.contracts.director_intent import Priority, StrictModel


class SourceType(str, Enum):
    peer_reviewed_paper = "peer_reviewed_paper"
    academic_reference = "academic_reference"
    standards_document = "standards_document"
    government_or_institutional = "government_or_institutional"
    manufacturer_technical_data = "manufacturer_technical_data"
    technical_documentation = "technical_documentation"
    authoritative_database = "authoritative_database"
    other = "other"


class EvidenceStatus(str, Enum):
    supported = "supported"
    partially_supported = "partially_supported"
    conflicting = "conflicting"
    unsupported = "unsupported"
    insufficient_evidence = "insufficient_evidence"


class ConflictResolutionStatus(str, Enum):
    unresolved = "unresolved"
    context_dependent = "context_dependent"
    requires_domain_validation = "requires_domain_validation"


class ResearchCoverageState(str, Enum):
    addressed = "addressed"
    partially_addressed = "partially_addressed"
    unresolved = "unresolved"


class MaterialUnknownParameterReference(StrictModel):
    """Identity pair for a material parameter left unknown by the Director."""

    entity_id: str = Field(..., min_length=1)
    parameter: str = Field(..., min_length=1)


class ResearchScope(StrictModel):
    """Explicit snapshot of Director identifiers available to this research result."""

    director_research_requirement_ids: list[str]
    director_physical_question_ids: list[str]
    director_scene_entity_ids: list[str]
    director_material_unknown_parameters: list[MaterialUnknownParameterReference]


class EvidenceSource(StrictModel):
    """Normalized source metadata. A source record is not itself a factual claim."""

    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    source_type: SourceType
    publisher: Optional[str] = None
    url: Optional[str] = None
    publication_date: Optional[date] = None
    accessed_at: Optional[datetime] = None


class PhysicalParameterEvidence(StrictModel):
    """Source-linked physical quantity preserved without coercing it to a scalar."""

    name: str = Field(..., min_length=1)
    value_text: str = Field(..., min_length=1)
    source_ids: list[str] = Field(..., min_length=1)
    unit: Optional[str] = None
    conditions: list[str]
    uncertainty: Optional[str] = None
    related_entity: Optional[str] = None


class ResearchFinding(StrictModel):
    """A source-linked research claim, not a final physical verdict."""

    id: str = Field(..., min_length=1)
    claim: str = Field(..., min_length=1)
    domain: str = Field(..., min_length=1)
    evidence_status: EvidenceStatus
    source_ids: list[str]
    director_research_requirement_ids: list[str]
    director_physical_question_ids: list[str]
    related_scene_entities: list[str]
    related_material_unknown_parameters: list[MaterialUnknownParameterReference]
    conditions: list[str]
    limitations: list[str]
    missing_context: list[str]
    physical_parameters: list[PhysicalParameterEvidence]


class EvidenceConflict(StrictModel):
    """Visible disagreement between already-recorded findings and/or sources."""

    id: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    finding_ids: list[str]
    source_ids: list[str]
    description: str = Field(..., min_length=1)
    contextual_explanation: Optional[str] = None
    resolution_status: ConflictResolutionStatus


class UnresolvedResearchQuestion(StrictModel):
    """Research gap retained for downstream work without a physical conclusion."""

    id: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    why_unresolved: str = Field(..., min_length=1)
    evidence_needed: list[str]
    priority: Priority
    director_research_requirement_ids: list[str]
    director_physical_question_ids: list[str]
    related_material_unknown_parameters: list[MaterialUnknownParameterReference]


class ResearchCoverage(StrictModel):
    """Mandatory completion state for exactly one Director research requirement."""

    director_research_requirement_id: str = Field(..., min_length=1)
    state: ResearchCoverageState
    notes: Optional[str] = None


class ResearchEvidenceContract(StrictModel):
    """Top-level deterministic output boundary for Research Agent v0.1."""

    contract_version: Literal["0.1"]
    agent: Literal["research_agent"]
    research_scope: ResearchScope
    sources: list[EvidenceSource]
    findings: list[ResearchFinding]
    conflicts: list[EvidenceConflict]
    unresolved_questions: list[UnresolvedResearchQuestion]
    coverage: list[ResearchCoverage]
    research_summary: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_cross_references(self) -> "ResearchEvidenceContract":
        """Enforce identifier integrity; never infer scientific truth."""
        def reject_duplicates(values: list[str], label: str) -> None:
            duplicates = sorted({value for value in values if values.count(value) > 1})
            if duplicates:
                raise ValueError(f"Duplicate {label}: {duplicates}")

        source_ids = [source.id for source in self.sources]
        finding_ids = [finding.id for finding in self.findings]
        unresolved_ids = [question.id for question in self.unresolved_questions]
        conflict_ids = [conflict.id for conflict in self.conflicts]
        reject_duplicates(source_ids, "EvidenceSource IDs")
        reject_duplicates(finding_ids, "ResearchFinding IDs")
        reject_duplicates(unresolved_ids, "UnresolvedResearchQuestion IDs")
        reject_duplicates(conflict_ids, "EvidenceConflict IDs")

        source_id_set = set(source_ids)
        finding_id_set = set(finding_ids)
        for scope_ids, label in (
            (self.research_scope.director_research_requirement_ids, "ResearchScope Director research requirement IDs"),
            (self.research_scope.director_physical_question_ids, "ResearchScope Director physical question IDs"),
            (self.research_scope.director_scene_entity_ids, "ResearchScope Director scene entity IDs"),
        ):
            reject_duplicates(scope_ids, label)
            if any(not identifier for identifier in scope_ids):
                raise ValueError(f"Blank {label} are not allowed")

        requirement_id_set = set(self.research_scope.director_research_requirement_ids)
        question_id_set = set(self.research_scope.director_physical_question_ids)
        entity_id_set = set(self.research_scope.director_scene_entity_ids)
        unknown_pairs = [
            (reference.entity_id, reference.parameter)
            for reference in self.research_scope.director_material_unknown_parameters
        ]
        if len(unknown_pairs) != len(set(unknown_pairs)):
            raise ValueError("Duplicate MaterialUnknownParameterReference pairs in ResearchScope")
        for entity_id, parameter in unknown_pairs:
            if entity_id not in entity_id_set:
                raise ValueError(
                    f"MaterialUnknownParameterReference references unknown scene entity: '{entity_id}'"
                )

        def validate_scope_references(
            requirement_ids: list[str],
            physical_question_ids: list[str],
            material_unknowns: list[MaterialUnknownParameterReference],
            label: str,
        ) -> None:
            reject_duplicates(requirement_ids, f"{label} director research requirement IDs")
            reject_duplicates(physical_question_ids, f"{label} director physical question IDs")
            pairs = [(item.entity_id, item.parameter) for item in material_unknowns]
            if len(pairs) != len(set(pairs)):
                raise ValueError(f"Duplicate {label} material unknown-parameter references")
            for requirement_id in requirement_ids:
                if requirement_id not in requirement_id_set:
                    raise ValueError(f"{label} references unknown Director research requirement: '{requirement_id}'")
            for question_id in physical_question_ids:
                if question_id not in question_id_set:
                    raise ValueError(f"{label} references unknown Director physical question: '{question_id}'")
            for pair in pairs:
                if pair not in unknown_pairs:
                    raise ValueError(
                        f"{label} references unknown Director material parameter: {pair}"
                    )

        for finding in self.findings:
            reject_duplicates(finding.source_ids, f"ResearchFinding '{finding.id}' source IDs")
            if finding.evidence_status in {
                EvidenceStatus.supported,
                EvidenceStatus.partially_supported,
                EvidenceStatus.conflicting,
            } and not finding.source_ids:
                raise ValueError(
                    f"ResearchFinding '{finding.id}' with status '{finding.evidence_status.value}' requires evidence sources"
                )
            for source_id in finding.source_ids:
                if source_id not in source_id_set:
                    raise ValueError(f"ResearchFinding '{finding.id}' references unknown source: '{source_id}'")
            validate_scope_references(
                finding.director_research_requirement_ids,
                finding.director_physical_question_ids,
                finding.related_material_unknown_parameters,
                f"ResearchFinding '{finding.id}'",
            )
            reject_duplicates(finding.related_scene_entities, f"ResearchFinding '{finding.id}' scene entity IDs")
            for entity_id in finding.related_scene_entities:
                if entity_id not in entity_id_set:
                    raise ValueError(f"ResearchFinding '{finding.id}' references unknown scene entity: '{entity_id}'")
            for parameter in finding.physical_parameters:
                reject_duplicates(parameter.source_ids, f"PhysicalParameterEvidence '{parameter.name}' source IDs")
                for source_id in parameter.source_ids:
                    if source_id not in source_id_set:
                        raise ValueError(
                            f"PhysicalParameterEvidence '{parameter.name}' references unknown source: '{source_id}'"
                        )
                if not set(parameter.source_ids).issubset(set(finding.source_ids)):
                    raise ValueError(
                        f"PhysicalParameterEvidence '{parameter.name}' sources must be a subset of parent ResearchFinding '{finding.id}' source IDs"
                    )
                if parameter.related_entity is not None and parameter.related_entity not in entity_id_set:
                    raise ValueError(
                        f"PhysicalParameterEvidence '{parameter.name}' references unknown scene entity: '{parameter.related_entity}'"
                    )

        for question in self.unresolved_questions:
            validate_scope_references(
                question.director_research_requirement_ids,
                question.director_physical_question_ids,
                question.related_material_unknown_parameters,
                f"UnresolvedResearchQuestion '{question.id}'",
            )

        for conflict in self.conflicts:
            reject_duplicates(conflict.finding_ids, f"EvidenceConflict '{conflict.id}' finding IDs")
            reject_duplicates(conflict.source_ids, f"EvidenceConflict '{conflict.id}' source IDs")
            if len(set(conflict.finding_ids)) + len(set(conflict.source_ids)) < 2:
                raise ValueError(f"EvidenceConflict '{conflict.id}' requires at least two evidence references")
            for finding_id in conflict.finding_ids:
                if finding_id not in finding_id_set:
                    raise ValueError(f"EvidenceConflict '{conflict.id}' references unknown finding: '{finding_id}'")
            for source_id in conflict.source_ids:
                if source_id not in source_id_set:
                    raise ValueError(f"EvidenceConflict '{conflict.id}' references unknown source: '{source_id}'")

        coverage_ids = [entry.director_research_requirement_id for entry in self.coverage]
        reject_duplicates(coverage_ids, "ResearchCoverage requirement IDs")
        if set(coverage_ids) != requirement_id_set:
            raise ValueError("ResearchCoverage must contain exactly one entry for every scoped Director research requirement")

        return self
