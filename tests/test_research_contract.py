"""Deterministic tests for ResearchEvidenceContract v0.1."""

import copy

import pytest
from pydantic import ValidationError

from src.contracts.research_evidence import ResearchEvidenceContract


def make_valid_payload() -> dict:
    return {
        "contract_version": "0.1",
        "agent": "research_agent",
        "research_scope": {
            "director_research_requirement_ids": ["rr_optics", "rr_caustics"],
            "director_physical_question_ids": ["pq_refraction"],
            "director_scene_entity_ids": ["crystal_1", "basalt_1"],
            "director_material_unknown_parameters": [
                {"entity_id": "crystal_1", "parameter": "refractive_index"},
                {"entity_id": "crystal_1", "parameter": "dispersion_curve"},
            ],
        },
        "sources": [
            {"id": "source_1", "title": "Optical reference", "source_type": "academic_reference", "url": "https://example.test/optics"},
            {"id": "source_2", "title": "Caustics reference", "source_type": "technical_documentation"},
        ],
        "findings": [
            {
                "id": "finding_1", "claim": "Candidate transparent materials require wavelength context.",
                "domain": "optics", "evidence_status": "supported", "source_ids": ["source_1"],
                "director_research_requirement_ids": ["rr_optics"], "director_physical_question_ids": ["pq_refraction"],
                "related_scene_entities": ["crystal_1"],
                "related_material_unknown_parameters": [{"entity_id": "crystal_1", "parameter": "refractive_index"}],
                "conditions": ["reported spectral conditions must be retained"], "limitations": [], "missing_context": [],
                "physical_parameters": [{"name": "refractive_index", "value_text": "1.45-1.55 across reported samples", "unit": None, "source_ids": ["source_1"], "conditions": ["wavelength dependent"], "uncertainty": "sample dependent", "related_entity": "crystal_1"}],
            }
        ],
        "conflicts": [{"id": "conflict_1", "topic": "caustic visibility", "finding_ids": ["finding_1"], "source_ids": ["source_2"], "description": "Evidence applies under different illumination conditions.", "contextual_explanation": "Conditions are not equivalent.", "resolution_status": "context_dependent"}],
        "unresolved_questions": [{"id": "unresolved_1", "topic": "candidate material selection", "why_unresolved": "No specific composition was supplied.", "evidence_needed": ["identified material composition"], "priority": "high", "director_research_requirement_ids": ["rr_caustics"], "director_physical_question_ids": [], "related_material_unknown_parameters": [{"entity_id": "crystal_1", "parameter": "dispersion_curve"}]}],
        "coverage": [{"director_research_requirement_id": "rr_optics", "state": "addressed"}, {"director_research_requirement_id": "rr_caustics", "state": "unresolved", "notes": "Material remains unspecified."}],
        "research_summary": "Evidence is preserved with conditions and unresolved material selection.",
    }


def assert_invalid(payload: dict, text: str) -> None:
    with pytest.raises(ValidationError) as error:
        ResearchEvidenceContract(**payload)
    assert text in str(error.value)


def test_1_valid_research_contract_accepted():
    contract = ResearchEvidenceContract(**make_valid_payload())
    assert contract.agent == "research_agent"


def test_2_wrong_contract_version_rejected():
    payload = make_valid_payload(); payload["contract_version"] = "0.2"
    assert_invalid(payload, "contract_version")


def test_3_wrong_agent_identity_rejected():
    payload = make_valid_payload(); payload["agent"] = "director_agent"
    assert_invalid(payload, "agent")


def test_4_unknown_fields_rejected():
    payload = make_valid_payload(); payload["unexpected"] = True
    assert_invalid(payload, "unexpected")


def test_5_duplicate_source_ids_rejected():
    payload = make_valid_payload(); payload["sources"].append(copy.deepcopy(payload["sources"][0]))
    assert_invalid(payload, "Duplicate EvidenceSource IDs")


def test_6_duplicate_finding_ids_rejected():
    payload = make_valid_payload(); payload["findings"].append(copy.deepcopy(payload["findings"][0]))
    assert_invalid(payload, "Duplicate ResearchFinding IDs")


def test_7_finding_unknown_source_rejected():
    payload = make_valid_payload(); payload["findings"][0]["source_ids"] = ["missing"]
    assert_invalid(payload, "unknown source")


@pytest.mark.parametrize("status", ["supported", "partially_supported"])
def test_8_and_9_grounded_statuses_require_sources(status):
    payload = make_valid_payload(); payload["findings"][0]["evidence_status"] = status; payload["findings"][0]["source_ids"] = []; payload["findings"][0]["physical_parameters"] = []
    assert_invalid(payload, "requires evidence sources")


@pytest.mark.parametrize("status", ["unsupported", "insufficient_evidence"])
def test_10_unsupported_statuses_can_have_no_sources(status):
    payload = make_valid_payload(); payload["findings"][0]["evidence_status"] = status; payload["findings"][0]["source_ids"] = []; payload["findings"][0]["physical_parameters"] = []
    assert ResearchEvidenceContract(**payload).findings[0].source_ids == []


def test_11_conflict_unknown_reference_rejected():
    payload = make_valid_payload(); payload["conflicts"][0]["finding_ids"] = ["missing"]; payload["conflicts"][0]["source_ids"] = ["source_2"]
    assert_invalid(payload, "unknown finding")


def test_12_coverage_unknown_requirement_rejected():
    payload = make_valid_payload(); payload["coverage"][1]["director_research_requirement_id"] = "missing"
    assert_invalid(payload, "exactly one entry")


def test_13_physical_parameter_preserves_range_text():
    contract = ResearchEvidenceContract(**make_valid_payload())
    parameter = contract.findings[0].physical_parameters[0]
    assert parameter.value_text == "1.45-1.55 across reported samples"
    assert parameter.conditions == ["wavelength dependent"]


def test_14_reference_case_is_representable():
    payload = make_valid_payload(); payload["research_summary"] = "Crystal monolith, basalt reflectance, dispersion, and caustic conditions remain source-linked."
    assert ResearchEvidenceContract(**payload).research_summary.startswith("Crystal monolith")


def test_15_adversarial_case_is_representable_without_verdict():
    payload = make_valid_payload(); payload["findings"][0]["claim"] = "Reported dispersion evidence bears on the requested red and blue behavior."; payload["findings"][0]["evidence_status"] = "insufficient_evidence"; payload["findings"][0]["source_ids"] = []; payload["findings"][0]["physical_parameters"] = []; payload["unresolved_questions"][0]["topic"] = "requested red-blue dispersion compatibility"
    contract = ResearchEvidenceContract(**payload)
    assert contract.findings[0].evidence_status.value == "insufficient_evidence"


def test_16_duplicate_material_unknown_pair_in_scope_rejected():
    payload = make_valid_payload(); payload["research_scope"]["director_material_unknown_parameters"].append({"entity_id": "crystal_1", "parameter": "refractive_index"})
    assert_invalid(payload, "Duplicate MaterialUnknownParameterReference pairs")


def test_17_finding_unknown_material_parameter_rejected():
    payload = make_valid_payload(); payload["findings"][0]["related_material_unknown_parameters"] = [{"entity_id": "crystal_1", "parameter": "density"}]
    assert_invalid(payload, "unknown Director material parameter")


def test_18_unresolved_unknown_material_parameter_rejected():
    payload = make_valid_payload(); payload["unresolved_questions"][0]["related_material_unknown_parameters"] = [{"entity_id": "crystal_1", "parameter": "density"}]
    assert_invalid(payload, "unknown Director material parameter")


def test_19_coverage_missing_requirement_rejected():
    payload = make_valid_payload(); payload["coverage"] = payload["coverage"][:1]
    assert_invalid(payload, "exactly one entry")


def test_20_coverage_extra_requirement_rejected():
    payload = make_valid_payload(); payload["coverage"].append({"director_research_requirement_id": "rr_extra", "state": "unresolved"})
    assert_invalid(payload, "exactly one entry")


def test_21_conflict_requires_two_evidence_references():
    payload = make_valid_payload(); payload["conflicts"][0]["source_ids"] = []
    assert_invalid(payload, "at least two evidence references")


def test_22_conflict_duplicate_references_rejected():
    payload = make_valid_payload(); payload["conflicts"][0]["source_ids"] = ["source_2", "source_2"]
    assert_invalid(payload, "Duplicate EvidenceConflict")

def test_23_duplicate_scoped_research_requirement_rejected():
    payload = make_valid_payload()
    payload["research_scope"]["director_research_requirement_ids"].append("rr_optics")
    assert_invalid(payload, "Duplicate ResearchScope Director research requirement IDs")


def test_24_duplicate_scoped_physical_question_rejected():
    payload = make_valid_payload()
    payload["research_scope"]["director_physical_question_ids"].append("pq_refraction")
    assert_invalid(payload, "Duplicate ResearchScope Director physical question IDs")


def test_25_duplicate_scoped_scene_entity_rejected():
    payload = make_valid_payload()
    payload["research_scope"]["director_scene_entity_ids"].append("crystal_1")
    assert_invalid(payload, "Duplicate ResearchScope Director scene entity IDs")


def test_26_blank_scoped_identifier_rejected():
    payload = make_valid_payload()
    payload["research_scope"]["director_research_requirement_ids"][0] = ""
    assert_invalid(payload, "Blank ResearchScope Director research requirement IDs")


def test_27_physical_parameter_source_must_belong_to_parent_finding():
    payload = make_valid_payload()
    payload["findings"][0]["physical_parameters"][0]["source_ids"] = ["source_2"]
    assert_invalid(payload, "sources must be a subset of parent ResearchFinding")


def test_28_physical_parameter_source_subset_is_accepted():
    payload = make_valid_payload()
    payload["findings"][0]["source_ids"] = ["source_1", "source_2"]
    payload["findings"][0]["physical_parameters"][0]["source_ids"] = ["source_1"]
    assert ResearchEvidenceContract(**payload).findings[0].physical_parameters[0].source_ids == ["source_1"]
