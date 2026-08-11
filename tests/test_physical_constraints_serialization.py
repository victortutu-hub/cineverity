"""Deterministic serialization tests for PhysicalConstraintsContract v0.1."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.export_physical_constraints_schema import canonical_schema_text, export_schema
from src.contracts.physical_constraints import (
    ArtisticDeviationType,
    MaterialIdentityStatus,
    PhysicalAssessmentStatus,
    PhysicalConstraintsContract,
    PhysicalQuestionCoverageState,
)
from src.contracts.research_evidence import EvidenceStatus


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
                "id": "constraint_optics", "statement": "Supplied evidence supports wavelength-dependent behavior λ.", "domain": "optics", "status": "supported",
                "director_physical_question_ids": ["pq_optics"], "director_research_requirement_ids": ["rr_optics"], "director_scene_entity_ids": ["crystal_1"],
                "related_material_unknown_parameters": [{"entity_id": "crystal_1", "parameter": "refractive_index"}],
                "research_finding_ids": ["finding_optics"], "source_ids": ["source_optics"], "conditions": ["reported context"], "limitations": ["quantitative magnitude unresolved"],
                "material_identity_references": [{"scene_entity_id": "crystal_1", "status": "established_for_scene_entity", "identity_label": "crystal μ context", "research_finding_ids": ["finding_optics"], "source_ids": ["source_optics"], "limitation": None}],
                "safe_downstream_assumptions": ["qualitative behavior is grounded"], "unsafe_downstream_assumptions": ["magnitude is not fixed"],
            },
            {
                "id": "constraint_caustics", "statement": "Caustics remain conditional.", "domain": "optics", "status": "conditionally_supported",
                "director_physical_question_ids": ["pq_caustic"], "director_research_requirement_ids": ["rr_optics"], "director_scene_entity_ids": ["crystal_1", "surface_1"],
                "related_material_unknown_parameters": [], "research_finding_ids": ["finding_caustics"], "source_ids": ["source_caustics"], "conditions": ["geometry relevant"], "limitations": ["conditions remain"],
                "material_identity_references": [], "safe_downstream_assumptions": ["conditions matter"], "unsafe_downstream_assumptions": ["magnitude is fixed"],
            },
        ],
        "conflicts": [{"id": "physical_conflict_1", "statement": "Requested intensity may conflict with evidence.", "constraint_ids": ["constraint_caustics"], "director_physical_question_ids": ["pq_caustic"], "research_finding_ids": ["finding_caustics"], "source_ids": ["source_caustics"], "research_conflict_ids": ["research_conflict_1"], "conditions": [], "limitations": ["intent preserved"], "resolution_status": "artist_decision_required"}],
        "unresolved_constraints": [{"id": "unresolved_magnitude", "why_indeterminate": "Evidence does not establish magnitude.", "evidence_needed": ["quantitative characterization"], "priority": "high", "director_physical_question_ids": ["pq_caustic"], "director_scene_entity_ids": ["crystal_1"], "related_material_unknown_parameters": [{"entity_id": "crystal_1", "parameter": "refractive_index"}], "research_finding_ids": ["finding_caustics"], "source_ids": ["source_caustics"], "research_conflict_ids": [], "research_unresolved_question_ids": ["research_unresolved_1"], "limitations": ["identity unresolved"]}],
        "artistic_deviations": [{"id": "deviation_rainbow", "statement": "Rainbow separation is artistic.", "deviation_type": "artistic_amplification", "director_physical_question_ids": ["pq_optics"], "director_scene_entity_ids": ["crystal_1"], "related_material_unknown_parameters": [{"entity_id": "crystal_1", "parameter": "refractive_index"}], "constraint_ids": ["constraint_optics"], "physical_tradeoff": "Magnitude is exaggerated.", "requires_explicit_artist_acceptance": True}],
        "coverage": [
            {"director_physical_question_id": "pq_optics", "state": "addressed", "constraint_ids": ["constraint_optics"], "unresolved_constraint_ids": [], "artistic_deviation_ids": ["deviation_rainbow"], "notes": "Ångström-safe Unicode."},
            {"director_physical_question_id": "pq_caustic", "state": "partially_addressed", "constraint_ids": ["constraint_caustics"], "unresolved_constraint_ids": ["unresolved_magnitude"], "artistic_deviation_ids": [], "notes": None},
        ],
        "physical_summary": "Unicode λ μ Å 漢字 survives canonical serialization.",
    }


@pytest.fixture
def reference_contract() -> PhysicalConstraintsContract:
    return PhysicalConstraintsContract.model_validate(valid_payload())


def canonical_contract_text(contract: PhysicalConstraintsContract) -> str:
    return json.dumps(contract.model_dump(mode="json"), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def assert_invalid_json(payload: dict, expected: str) -> None:
    with pytest.raises(ValidationError, match=expected):
        PhysicalConstraintsContract.model_validate_json(json.dumps(payload))


def test_1_model_json_schema_returns_dict():
    assert isinstance(PhysicalConstraintsContract.model_json_schema(), dict)


def test_2_schema_identity_title():
    assert PhysicalConstraintsContract.model_json_schema()["title"] == "PhysicalConstraintsContract"


def test_3_contract_version_is_restricted():
    field = PhysicalConstraintsContract.model_json_schema()["properties"]["contract_version"]
    assert field.get("enum") == ["0.1"] or field.get("const") == "0.1"


def test_4_agent_is_restricted():
    field = PhysicalConstraintsContract.model_json_schema()["properties"]["agent"]
    assert field.get("enum") == ["physical_constraints_agent"] or field.get("const") == "physical_constraints_agent"


def test_5_assessment_enum_values_are_exact():
    assert [member.value for member in PhysicalAssessmentStatus] == ["supported", "conditionally_supported", "conflicting", "unsupported", "indeterminate"]


def test_6_coverage_enum_values_are_exact():
    assert [member.value for member in PhysicalQuestionCoverageState] == ["addressed", "partially_addressed", "unresolved"]


def test_7_material_and_artistic_enum_values_are_exact():
    assert [member.value for member in MaterialIdentityStatus] == ["established_for_scene_entity", "contextual_only", "unresolved"]
    assert [member.value for member in ArtisticDeviationType] == ["explicitly_nonphysical", "artistic_amplification", "speculative_behavior"]


def test_8_evidence_status_is_inherited_from_research_boundary():
    schema_values = PhysicalConstraintsContract.model_json_schema()["$defs"]["EvidenceStatus"]["enum"]
    assert sorted(schema_values) == sorted(member.value for member in EvidenceStatus)


def test_9_model_dump_mode_json_is_json_safe(reference_contract):
    dumped = reference_contract.model_dump(mode="json")
    assert json.dumps(dumped)
    assert dumped["input_scope"]["research_finding_provenance"][0]["evidence_status"] == "supported"


def test_10_canonical_contract_keys_are_sorted(reference_contract):
    rendered = canonical_contract_text(reference_contract)
    assert rendered.startswith('{\n  "agent": "physical_constraints_agent",')


def test_11_canonical_contract_rendering_is_deterministic(reference_contract):
    assert canonical_contract_text(reference_contract) == canonical_contract_text(reference_contract)


def test_12_canonical_contract_preserves_unicode_without_ascii_escaping(reference_contract):
    rendered = canonical_contract_text(reference_contract)
    assert "λ μ Å 漢字" in rendered
    assert "\\u03bb" not in rendered


def test_13_canonical_contract_is_lf_only_with_exactly_one_final_lf(reference_contract):
    rendered = canonical_contract_text(reference_contract)
    assert "\r" not in rendered
    assert rendered.endswith("\n") and not rendered.endswith("\n\n")


def test_14_canonical_contract_bytes_are_utf8_without_bom(reference_contract):
    artifact = canonical_contract_text(reference_contract).encode("utf-8")
    assert artifact.startswith(b"{")
    assert not artifact.startswith(b"\xef\xbb\xbf")
    assert artifact.endswith(b"\n") and not artifact.endswith(b"\n\n")


def test_15_canonical_contract_round_trip_preserves_semantic_equality(reference_contract):
    assert PhysicalConstraintsContract.model_validate_json(canonical_contract_text(reference_contract)) == reference_contract


def test_16_model_dump_json_round_trip_preserves_semantic_equality(reference_contract):
    assert PhysicalConstraintsContract.model_validate_json(reference_contract.model_dump_json()) == reference_contract


def test_17_unknown_field_is_rejected_after_json_deserialization(reference_contract):
    payload = reference_contract.model_dump(mode="json"); payload["unknown"] = True
    assert_invalid_json(payload, "unknown")


def test_18_cross_question_reference_is_rejected_after_json_deserialization(reference_contract):
    payload = reference_contract.model_dump(mode="json"); payload["coverage"][0]["constraint_ids"] = ["constraint_caustics"]
    assert_invalid_json(payload, "cannot link a PhysicalConstraint for another physical question")


def test_19_provenance_subset_is_rejected_after_json_deserialization(reference_contract):
    payload = reference_contract.model_dump(mode="json"); payload["constraints"][0]["source_ids"] = ["source_caustics"]
    assert_invalid_json(payload, "source IDs must be a subset")


def test_20_checked_in_schema_matches_independent_canonical_bytes():
    schema_path = Path(__file__).resolve().parent.parent / "schemas" / "physical-constraints-contract-v0.1.schema.json"
    expected = (json.dumps(PhysicalConstraintsContract.model_json_schema(), indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    assert schema_path.read_bytes() == expected


def test_21_canonical_schema_text_is_deterministic_and_has_one_lf():
    first = canonical_schema_text(); second = canonical_schema_text()
    assert first == second
    assert "\r" not in first
    assert first.endswith("\n") and not first.endswith("\n\n")


def test_22_exported_schema_is_json_and_utf8_without_bom(tmp_path):
    output_path = export_schema(tmp_path / "schema.json")
    artifact = output_path.read_bytes()
    assert json.loads(artifact.decode("utf-8"))["title"] == "PhysicalConstraintsContract"
    assert not artifact.startswith(b"\xef\xbb\xbf")
    assert artifact.endswith(b"\n") and not artifact.endswith(b"\n\n")


def test_23_repeated_schema_export_is_byte_identical(tmp_path):
    output_path = tmp_path / "schema.json"
    export_schema(output_path); first = output_path.read_bytes()
    export_schema(output_path); second = output_path.read_bytes()
    assert first == second