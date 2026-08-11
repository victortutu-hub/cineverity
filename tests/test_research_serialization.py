"""Deterministic JSON Schema and serialization tests for ResearchEvidenceContract v0.1."""

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.export_research_schema import canonical_schema_text
from src.contracts.director_intent import Priority
from src.contracts.research_evidence import ResearchEvidenceContract


@pytest.fixture
def reference_contract() -> ResearchEvidenceContract:
    payload = {
        "contract_version": "0.1",
        "agent": "research_agent",
        "research_scope": {
            "director_research_requirement_ids": ["rr_optics"],
            "director_physical_question_ids": ["pq_refraction"],
            "director_scene_entity_ids": ["crystal_1"],
            "director_material_unknown_parameters": [
                {"entity_id": "crystal_1", "parameter": "refractive_index"}
            ],
        },
        "sources": [
            {
                "id": "source_1",
                "title": "Optical properties reference",
                "source_type": "academic_reference",
                "publisher": "Example Institute",
                "url": "https://example.test/optics",
                "publication_date": date(2026, 8, 1),
                "accessed_at": datetime(2026, 8, 11, 12, 30, tzinfo=timezone.utc),
            },
            {
                "id": "source_2",
                "title": "Caustics conditions reference",
                "source_type": "technical_documentation",
            },
        ],
        "findings": [
            {
                "id": "finding_1",
                "claim": "Reported refractive values depend on wavelength and composition.",
                "domain": "optics",
                "evidence_status": "supported",
                "source_ids": ["source_1", "source_2"],
                "director_research_requirement_ids": ["rr_optics"],
                "director_physical_question_ids": ["pq_refraction"],
                "related_scene_entities": ["crystal_1"],
                "related_material_unknown_parameters": [
                    {"entity_id": "crystal_1", "parameter": "refractive_index"}
                ],
                "conditions": ["wavelength and composition reported"],
                "limitations": ["candidate material remains unspecified"],
                "missing_context": [],
                "physical_parameters": [
                    {
                        "name": "refractive_index",
                        "value_text": "n(λ) = 1.45-1.55 over reported visible wavelengths",
                        "unit": None,
                        "source_ids": ["source_1"],
                        "conditions": ["visible spectrum"],
                        "uncertainty": "sample dependent",
                        "related_entity": "crystal_1",
                    }
                ],
            }
        ],
        "conflicts": [
            {
                "id": "conflict_1",
                "topic": "caustic visibility",
                "finding_ids": ["finding_1"],
                "source_ids": ["source_2"],
                "description": "Reported conditions differ.",
                "contextual_explanation": "Illumination geometry is not identical.",
                "resolution_status": "context_dependent",
            }
        ],
        "unresolved_questions": [],
        "coverage": [
            {"director_research_requirement_id": "rr_optics", "state": "addressed"}
        ],
        "research_summary": "Source-linked optics evidence with retained conditions.",
    }
    return ResearchEvidenceContract(**payload)


def raw_contract(contract: ResearchEvidenceContract) -> dict:
    return contract.model_dump(mode="json")


def assert_json_invalid(payload: dict, expected: str) -> None:
    with pytest.raises(ValidationError) as error:
        ResearchEvidenceContract.model_validate_json(json.dumps(payload))
    assert expected in str(error.value)


def test_1_model_json_schema_returns_dict():
    assert isinstance(ResearchEvidenceContract.model_json_schema(), dict)


def test_2_schema_identity_title():
    assert ResearchEvidenceContract.model_json_schema()["title"] == "ResearchEvidenceContract"


def test_3_contract_version_is_restricted():
    field = ResearchEvidenceContract.model_json_schema()["properties"]["contract_version"]
    assert field.get("enum") == ["0.1"] or field.get("const") == "0.1"


def test_4_agent_is_restricted():
    field = ResearchEvidenceContract.model_json_schema()["properties"]["agent"]
    assert field.get("enum") == ["research_agent"] or field.get("const") == "research_agent"


def test_5_source_type_enum_values():
    values = ResearchEvidenceContract.model_json_schema()["$defs"]["SourceType"]["enum"]
    assert sorted(values) == sorted(["peer_reviewed_paper", "academic_reference", "standards_document", "government_or_institutional", "manufacturer_technical_data", "technical_documentation", "authoritative_database", "other"])


def test_6_evidence_status_enum_values():
    values = ResearchEvidenceContract.model_json_schema()["$defs"]["EvidenceStatus"]["enum"]
    assert sorted(values) == sorted(["supported", "partially_supported", "conflicting", "unsupported", "insufficient_evidence"])


def test_7_conflict_resolution_status_enum_values():
    values = ResearchEvidenceContract.model_json_schema()["$defs"]["ConflictResolutionStatus"]["enum"]
    assert sorted(values) == sorted(["unresolved", "context_dependent", "requires_domain_validation"])


def test_8_research_coverage_state_enum_values():
    values = ResearchEvidenceContract.model_json_schema()["$defs"]["ResearchCoverageState"]["enum"]
    assert sorted(values) == sorted(["addressed", "partially_addressed", "unresolved"])


def test_9_priority_enum_is_inherited_from_director_boundary():
    values = ResearchEvidenceContract.model_json_schema()["$defs"]["Priority"]["enum"]
    assert sorted(values) == sorted(member.value for member in Priority)


def test_10_model_dump_json_mode_is_json_safe(reference_contract):
    dumped = reference_contract.model_dump(mode="json")
    assert isinstance(dumped, dict)
    assert dumped["sources"][0]["publication_date"] == "2026-08-01"
    assert isinstance(dumped["sources"][0]["accessed_at"], str)


def test_11_dumped_dict_is_json_serializable(reference_contract):
    assert isinstance(json.dumps(raw_contract(reference_contract)), str)


def test_12_model_dump_json_produces_valid_json(reference_contract):
    assert isinstance(reference_contract.model_dump_json(), str)


def test_13_json_loads_model_dump_json(reference_contract):
    assert json.loads(reference_contract.model_dump_json())["agent"] == "research_agent"


def test_14_json_round_trip_preserves_semantic_equality(reference_contract):
    assert ResearchEvidenceContract.model_validate_json(reference_contract.model_dump_json()) == reference_contract


def test_15_dict_round_trip_preserves_semantic_equality(reference_contract):
    assert ResearchEvidenceContract.model_validate(raw_contract(reference_contract)) == reference_contract


def test_16_unknown_top_level_field_rejected_after_deserialization(reference_contract):
    payload = raw_contract(reference_contract); payload["unknown"] = True
    assert_json_invalid(payload, "unknown")


def test_17_unknown_nested_field_rejected_after_deserialization(reference_contract):
    payload = raw_contract(reference_contract); payload["sources"][0]["unknown"] = True
    assert_json_invalid(payload, "unknown")


def test_18_invalid_source_reference_rejected_after_deserialization(reference_contract):
    payload = raw_contract(reference_contract); payload["findings"][0]["source_ids"] = ["missing"]
    assert_json_invalid(payload, "unknown source")


def test_19_invalid_material_unknown_reference_rejected_after_deserialization(reference_contract):
    payload = raw_contract(reference_contract); payload["findings"][0]["related_material_unknown_parameters"] = [{"entity_id": "crystal_1", "parameter": "density"}]
    assert_json_invalid(payload, "unknown Director material parameter")


def test_20_invalid_physical_parameter_provenance_subset_rejected(reference_contract):
    payload = raw_contract(reference_contract); payload["findings"][0]["source_ids"] = ["source_1"]; payload["findings"][0]["physical_parameters"][0]["source_ids"] = ["source_2"]
    assert_json_invalid(payload, "sources must be a subset")


def test_21_incomplete_coverage_rejected_after_deserialization(reference_contract):
    payload = raw_contract(reference_contract); payload["coverage"] = []
    assert_json_invalid(payload, "exactly one entry")


def test_22_invalid_evidence_conflict_rejected_after_deserialization(reference_contract):
    payload = raw_contract(reference_contract); payload["conflicts"][0]["source_ids"] = []
    assert_json_invalid(payload, "at least two evidence references")


def test_23_date_datetime_round_trip_preserves_semantic_values(reference_contract):
    reconstructed = ResearchEvidenceContract.model_validate_json(reference_contract.model_dump_json())
    source = reconstructed.sources[0]
    assert source.publication_date == date(2026, 8, 1)
    assert source.accessed_at == datetime(2026, 8, 11, 12, 30, tzinfo=timezone.utc)


def test_24_non_scalar_value_text_round_trips_exactly(reference_contract):
    value_text = reference_contract.findings[0].physical_parameters[0].value_text
    reconstructed = ResearchEvidenceContract.model_validate_json(reference_contract.model_dump_json())
    assert reconstructed.findings[0].physical_parameters[0].value_text == value_text


def test_25_checked_in_schema_matches_independent_canonical_generation():
    schema_path = Path(__file__).resolve().parent.parent / "schemas" / "research-evidence-contract-v0.1.schema.json"
    expected = (
        json.dumps(
            ResearchEvidenceContract.model_json_schema(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")
    assert schema_path.read_bytes() == expected


def test_26_canonical_schema_generation_is_deterministic_and_has_one_newline():
    first = canonical_schema_text()
    second = canonical_schema_text()
    schema_path = Path(__file__).resolve().parent.parent / "schemas" / "research-evidence-contract-v0.1.schema.json"
    artifact = schema_path.read_bytes()
    assert first == second
    assert first.endswith("\n")
    assert not first.endswith("\n\n")
    assert artifact.endswith(b"\n")
    assert not artifact.endswith(b"\n\n")
