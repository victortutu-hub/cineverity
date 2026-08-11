"""Deterministic structural tests for Physical Constraints Contract v0.1."""

from copy import deepcopy

import pytest
from pydantic import ValidationError

from src.contracts.physical_constraints import (
    ArtisticDeviationType,
    MaterialIdentityStatus,
    PhysicalAssessmentStatus,
    PhysicalConstraintsContract,
    PhysicalQuestionCoverageState,
)


def valid_payload():
    return {
        "contract_version": "0.1",
        "agent": "physical_constraints_agent",
        "input_scope": {
            "director_physical_question_ids": ["pq_optics", "pq_caustic"],
            "director_research_requirement_ids": ["rr_optics"],
            "director_scene_entity_ids": ["crystal_1", "surface_1"],
            "director_material_unknown_parameters": [
                {"entity_id": "crystal_1", "parameter": "refractive_index"},
            ],
            "director_validation_target_ids": ["vt_optics"],
            "research_finding_provenance": [
                {"finding_id": "finding_optics", "source_ids": ["source_optics"], "evidence_status": "supported"},
                {"finding_id": "finding_caustics", "source_ids": ["source_caustics"], "evidence_status": "partially_supported"},
            ],
            "research_conflict_ids": ["research_conflict_1"],
            "research_unresolved_question_ids": ["research_unresolved_1"],
        },
        "constraints": [
            {
                "id": "constraint_optics",
                "statement": "The supplied evidence supports wavelength-dependent optical behavior.",
                "domain": "optics",
                "status": "supported",
                "director_physical_question_ids": ["pq_optics"],
                "director_research_requirement_ids": ["rr_optics"],
                "director_scene_entity_ids": ["crystal_1"],
                "related_material_unknown_parameters": [
                    {"entity_id": "crystal_1", "parameter": "refractive_index"},
                ],
                "research_finding_ids": ["finding_optics"],
                "source_ids": ["source_optics"],
                "conditions": ["reported wavelength context applies"],
                "limitations": ["material identity remains constrained by cited evidence"],
                "material_identity_references": [
                    {
                        "scene_entity_id": "crystal_1",
                        "status": "established_for_scene_entity",
                        "identity_label": "transparent crystal context",
                        "research_finding_ids": ["finding_optics"],
                        "source_ids": ["source_optics"],
                        "limitation": None,
                    },
                ],
                "safe_downstream_assumptions": ["qualitative wavelength dependence is grounded"],
                "unsafe_downstream_assumptions": ["quantitative magnitude is not assumed"],
            },
            {
                "id": "constraint_caustics",
                "statement": "Caustic behavior remains conditional on scene and material conditions.",
                "domain": "optics",
                "status": "conditionally_supported",
                "director_physical_question_ids": ["pq_caustic"],
                "director_research_requirement_ids": ["rr_optics"],
                "director_scene_entity_ids": ["crystal_1", "surface_1"],
                "related_material_unknown_parameters": [],
                "research_finding_ids": ["finding_caustics"],
                "source_ids": ["source_caustics"],
                "conditions": ["geometry and incidence remain relevant"],
                "limitations": ["quantitative magnitude is unresolved"],
                "material_identity_references": [],
                "safe_downstream_assumptions": ["the effect needs conditions"],
                "unsafe_downstream_assumptions": ["the effect magnitude is fixed"],
            },
        ],
        "conflicts": [
            {
                "id": "physical_conflict_1",
                "statement": "The requested intensity may exceed the grounded qualitative behavior.",
                "constraint_ids": ["constraint_caustics"],
                "director_physical_question_ids": ["pq_caustic"],
                "research_finding_ids": ["finding_caustics"],
                "source_ids": ["source_caustics"],
                "research_conflict_ids": ["research_conflict_1"],
                "conditions": [],
                "limitations": ["artist intent is preserved"],
                "resolution_status": "artist_decision_required",
            },
        ],
        "unresolved_constraints": [
            {
                "id": "unresolved_magnitude",
                "why_indeterminate": "The accepted evidence does not establish the requested magnitude.",
                "evidence_needed": ["material-specific quantitative characterization"],
                "priority": "high",
                "director_physical_question_ids": ["pq_caustic"],
                "director_scene_entity_ids": ["crystal_1"],
                "related_material_unknown_parameters": [
                    {"entity_id": "crystal_1", "parameter": "refractive_index"},
                ],
                "research_finding_ids": ["finding_caustics"],
                "source_ids": ["source_caustics"],
                "research_conflict_ids": [],
                "research_unresolved_question_ids": ["research_unresolved_1"],
                "limitations": ["no material identity transfer is assumed"],
            },
        ],
        "artistic_deviations": [
            {
                "id": "deviation_rainbow",
                "statement": "Extreme rainbow separation is an artistic amplification.",
                "deviation_type": "artistic_amplification",
                "director_physical_question_ids": ["pq_optics"],
                "director_scene_entity_ids": ["crystal_1"],
                "related_material_unknown_parameters": [
                    {"entity_id": "crystal_1", "parameter": "refractive_index"},
                ],
                "constraint_ids": ["constraint_optics"],
                "physical_tradeoff": "Quantitative amplification exceeds grounded magnitude.",
                "requires_explicit_artist_acceptance": True,
            },
        ],
        "coverage": [
            {
                "director_physical_question_id": "pq_optics",
                "state": "addressed",
                "constraint_ids": ["constraint_optics"],
                "unresolved_constraint_ids": [],
                "artistic_deviation_ids": ["deviation_rainbow"],
                "notes": None,
            },
            {
                "director_physical_question_id": "pq_caustic",
                "state": "partially_addressed",
                "constraint_ids": ["constraint_caustics"],
                "unresolved_constraint_ids": ["unresolved_magnitude"],
                "artistic_deviation_ids": [],
                "notes": "Magnitude remains unresolved.",
            },
        ],
        "physical_summary": "Supported behavior, conditions, unresolved magnitude, and artistic amplification remain separate.",
    }


def assert_invalid(payload, message):
    with pytest.raises(ValidationError, match=message):
        PhysicalConstraintsContract.model_validate(payload)


def test_1_valid_contract_accepted():
    contract = PhysicalConstraintsContract.model_validate(valid_payload())
    assert contract.constraints[0].status is PhysicalAssessmentStatus.supported
    assert contract.coverage[0].state is PhysicalQuestionCoverageState.addressed


def test_2_contract_identity_literals_are_strict():
    payload = valid_payload(); payload["agent"] = "research_agent"
    assert_invalid(payload, "physical_constraints_agent")


def test_3_unknown_fields_rejected():
    payload = valid_payload(); payload["unexpected"] = True
    assert_invalid(payload, "Extra inputs are not permitted")


def test_4_scope_finding_provenance_ids_must_be_unique():
    payload = valid_payload(); payload["input_scope"]["research_finding_provenance"].append({"finding_id": "finding_optics", "source_ids": [], "evidence_status": "unsupported"})
    assert_invalid(payload, "Duplicate ResearchFindingProvenanceReference")


@pytest.mark.parametrize("field", [
    "director_physical_question_ids",
    "director_research_requirement_ids",
    "director_scene_entity_ids",
    "director_validation_target_ids",
])
def test_5_to_8_duplicate_scope_director_ids_rejected(field):
    payload = valid_payload(); payload["input_scope"][field].append(payload["input_scope"][field][0])
    assert_invalid(payload, "Duplicate PhysicalConstraintsScope")


def test_9_constraint_requires_known_physical_question():
    payload = valid_payload(); payload["constraints"][0]["director_physical_question_ids"] = ["unknown"]
    assert_invalid(payload, "Director physical question IDs references unknown")


def test_10_constraint_requires_known_material_pair():
    payload = valid_payload(); payload["constraints"][0]["related_material_unknown_parameters"] = [{"entity_id": "crystal_1", "parameter": "density"}]
    assert_invalid(payload, "unknown Director material parameter")


def test_11_constraint_source_must_be_subset_of_cited_findings():
    payload = valid_payload(); payload["constraints"][0]["source_ids"] = ["source_caustics"]
    assert_invalid(payload, "source IDs must be a subset")


def test_12_supported_constraint_requires_findings_and_sources():
    payload = valid_payload(); payload["constraints"][0]["research_finding_ids"] = []; payload["constraints"][0]["source_ids"] = []
    assert_invalid(payload, "requires Research findings and sources")


def test_13_indeterminate_constraint_can_be_source_free():
    payload = valid_payload(); item = payload["constraints"][1]; item["status"] = "indeterminate"; item["research_finding_ids"] = []; item["source_ids"] = []
    assert PhysicalConstraintsContract.model_validate(payload).constraints[1].status is PhysicalAssessmentStatus.indeterminate


def test_14_material_identity_established_requires_label_and_provenance():
    payload = valid_payload(); identity = payload["constraints"][0]["material_identity_references"][0]; identity["identity_label"] = None
    assert_invalid(payload, "established_for_scene_entity.*requires identity_label")


def test_15_contextual_identity_requires_limitation():
    payload = valid_payload(); identity = payload["constraints"][0]["material_identity_references"][0]; identity["status"] = "contextual_only"; identity["limitation"] = None; payload["constraints"][0]["related_material_unknown_parameters"] = []
    assert_invalid(payload, "contextual_only.*requires limitation")


def test_16_contextual_identity_can_preserve_related_unresolved_material_unknown():
    payload = valid_payload(); payload["constraints"][0]["material_identity_references"][0]["status"] = "contextual_only"; payload["constraints"][0]["material_identity_references"][0]["limitation"] = "comparison only"
    assert PhysicalConstraintsContract.model_validate(payload).constraints[0].related_material_unknown_parameters[0].parameter == "refractive_index"


def test_17_unresolved_identity_must_not_have_label():
    payload = valid_payload(); identity = payload["constraints"][0]["material_identity_references"][0]; identity["status"] = "unresolved"
    assert_invalid(payload, "unresolved.*must not have identity_label")


def test_18_identity_provenance_must_belong_to_parent_constraint():
    payload = valid_payload(); identity = payload["constraints"][0]["material_identity_references"][0]; identity["research_finding_ids"] = ["finding_caustics"]; identity["source_ids"] = ["source_caustics"]
    assert_invalid(payload, "must be cited by its parent")


def test_19_physical_conflict_requires_known_constraint():
    payload = valid_payload(); payload["conflicts"][0]["constraint_ids"] = ["missing"]
    assert_invalid(payload, "constraint IDs references unknown")


def test_20_unresolved_constraint_research_reference_must_exist():
    payload = valid_payload(); payload["unresolved_constraints"][0]["research_unresolved_question_ids"] = ["missing"]
    assert_invalid(payload, "Research unresolved question IDs references unknown")


def test_21_artistic_deviation_requires_explicit_boolean():
    payload = valid_payload(); payload["artistic_deviations"][0]["requires_explicit_artist_acceptance"] = "yes"
    assert_invalid(payload, "Input should be a valid boolean")


def test_22_coverage_is_exact_over_physical_questions():
    payload = valid_payload(); payload["coverage"] = payload["coverage"][:1]
    assert_invalid(payload, "must contain exactly one entry")


def test_23_coverage_rejects_unknown_constraint():
    payload = valid_payload(); payload["coverage"][0]["constraint_ids"] = ["missing"]
    assert_invalid(payload, "constraint IDs references unknown")


def test_24_unresolved_coverage_requires_unresolved_record():
    payload = valid_payload(); payload["coverage"][1]["state"] = "unresolved"; payload["coverage"][1]["unresolved_constraint_ids"] = []
    assert_invalid(payload, "requires an unresolved constraint")


def test_25_coverage_requires_linked_record():
    payload = valid_payload(); payload["coverage"][0]["constraint_ids"] = []; payload["coverage"][0]["artistic_deviation_ids"] = []
    assert_invalid(payload, "requires at least one linked record")


def test_26_assessment_and_coverage_enums_remain_distinct():
    assert [item.value for item in PhysicalAssessmentStatus] == ["supported", "conditionally_supported", "conflicting", "unsupported", "indeterminate"]
    assert [item.value for item in PhysicalQuestionCoverageState] == ["addressed", "partially_addressed", "unresolved"]


def test_27_artistic_deviation_enum_values_are_explicit():
    assert [item.value for item in ArtisticDeviationType] == ["explicitly_nonphysical", "artistic_amplification", "speculative_behavior"]


def test_28_material_identity_enum_values_are_explicit():
    assert [item.value for item in MaterialIdentityStatus] == ["established_for_scene_entity", "contextual_only", "unresolved"]


def test_29_round_trip_preserves_semantic_equality():
    original = PhysicalConstraintsContract.model_validate(valid_payload())
    assert PhysicalConstraintsContract.model_validate_json(original.model_dump_json()) == original


def test_30_input_scope_is_preserved_as_snapshot_data():
    contract = PhysicalConstraintsContract.model_validate(valid_payload())
    assert contract.input_scope.research_finding_provenance[0].finding_id == "finding_optics"

def test_31_coverage_rejects_constraint_for_another_question():
    payload = valid_payload(); payload["coverage"][0]["constraint_ids"] = ["constraint_caustics"]
    assert_invalid(payload, "cannot link a PhysicalConstraint for another physical question")


def test_32_coverage_rejects_unresolved_record_for_another_question():
    payload = valid_payload(); payload["coverage"][0]["constraint_ids"] = []; payload["coverage"][0]["artistic_deviation_ids"] = []; payload["coverage"][0]["unresolved_constraint_ids"] = ["unresolved_magnitude"]
    assert_invalid(payload, "cannot link an UnresolvedPhysicalConstraint for another physical question")


def test_33_coverage_rejects_artistic_deviation_for_another_question():
    payload = valid_payload(); payload["coverage"][1]["artistic_deviation_ids"] = ["deviation_rainbow"]
    assert_invalid(payload, "cannot link an ArtisticDeviation for another physical question")


def test_34_conflict_rejects_constraint_for_another_question():
    payload = valid_payload(); payload["conflicts"][0]["constraint_ids"] = ["constraint_optics"]
    assert_invalid(payload, "PhysicalConflict.*must be covered by its referenced constraints")


def test_35_artistic_deviation_rejects_constraint_for_another_question():
    payload = valid_payload(); payload["artistic_deviations"][0]["constraint_ids"] = ["constraint_caustics"]
    assert_invalid(payload, "ArtisticDeviation.*must be covered by its referenced constraints")


def test_36_material_identity_source_must_belong_to_parent_constraint_sources():
    payload = valid_payload(); constraint = payload["constraints"][0]; constraint["research_finding_ids"].append("finding_caustics")
    identity = constraint["material_identity_references"][0]; identity["research_finding_ids"] = ["finding_caustics"]; identity["source_ids"] = ["source_caustics"]
    assert_invalid(payload, "MaterialIdentityReference source IDs must be a subset of its parent")


@pytest.mark.parametrize("research_status", ["unsupported", "insufficient_evidence", "conflicting"])
def test_37_to_39_supported_rejects_non_supporting_research_statuses(research_status):
    payload = valid_payload(); constraint = payload["constraints"][0]; constraint["research_finding_ids"] = ["finding_caustics"]; constraint["source_ids"] = ["source_caustics"]; constraint["material_identity_references"] = []
    payload["input_scope"]["research_finding_provenance"][1]["evidence_status"] = research_status
    assert_invalid(payload, "requires at least one supported Research finding")


def test_40_supported_accepts_supported_research_finding():
    assert PhysicalConstraintsContract.model_validate(valid_payload()).constraints[0].status is PhysicalAssessmentStatus.supported


def test_41_conditionally_supported_accepts_partially_supported_research_finding():
    assert PhysicalConstraintsContract.model_validate(valid_payload()).constraints[1].status is PhysicalAssessmentStatus.conditionally_supported


def test_42_unsupported_requires_a_research_finding():
    payload = valid_payload(); constraint = payload["constraints"][1]; constraint["status"] = "unsupported"; constraint["research_finding_ids"] = []; constraint["source_ids"] = []
    assert_invalid(payload, "status 'unsupported' requires at least one Research finding")


def test_43_unsupported_can_be_source_free_with_unsupported_finding():
    payload = valid_payload(); constraint = payload["constraints"][1]; constraint["status"] = "unsupported"; constraint["source_ids"] = []
    payload["input_scope"]["research_finding_provenance"][1]["evidence_status"] = "unsupported"
    assert PhysicalConstraintsContract.model_validate(payload).constraints[1].status is PhysicalAssessmentStatus.unsupported
