"""
Tests for JSON Schema generation, serialization, deserialization, and boundary determinism for DirectorIntentContract v0.1.
"""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from src.contracts.director_intent import (
    AmbiguityResolution,
    DirectorIntentContract,
    Priority,
    RealityMode,
)


@pytest.fixture
def reference_contract_fixture() -> DirectorIntentContract:
    """Fixture providing a valid DirectorIntentContract based on the reference case."""
    payload = {
        "contract_version": "0.1",
        "agent": "director_agent",
        "creative_intent": {
            "core_idea": "A transparent crystal monolith levitating above a dark basalt surface with three narrow colored lights passing through it",
            "desired_emotion": ["alien", "scientifically_believable"],
            "visual_priorities": ["internal_refraction", "caustics"],
            "reality_mode": "physically_grounded_artistic",
        },
        "scene_entities": [
            {
                "id": "monolith_1",
                "type": "transparent_crystal_monolith",
                "description": "Levitating transparent crystal monolith",
            },
            {
                "id": "surface_1",
                "type": "basalt_surface",
                "description": "Dark basalt surface below monolith",
            },
        ],
        "material_intent": [
            {
                "entity_id": "monolith_1",
                "material_family": "crystal",
                "desired_properties": ["transparent", "refractive", "caustics_producing"],
                "unknown_parameters": ["refractive_index", "dispersion_formula"],
            },
            {
                "entity_id": "surface_1",
                "material_family": "basalt",
                "desired_properties": ["dark", "matte_rough"],
                "unknown_parameters": ["roughness_value"],
            },
        ],
        "lighting_intent": [
            {
                "id": "light_1",
                "role": "narrow_beam_1",
                "color_intent": "colored_beam_1",
                "interaction_target": "monolith_1",
            },
            {
                "id": "light_2",
                "role": "narrow_beam_2",
                "color_intent": "colored_beam_2",
                "interaction_target": "monolith_1",
            },
            {
                "id": "light_3",
                "role": "narrow_beam_3",
                "color_intent": "colored_beam_3",
                "interaction_target": "monolith_1",
            },
        ],
        "environment_intent": {
            "setting": "alien_landscape",
            "surface": "dark_basalt",
            "atmosphere": "clear",
            "background_priority": "subdued",
            "environmental_effects": [],
        },
        "cinematic_intent": {
            "visual_style": ["alien_sci_fi"],
            "subject_priority": "monolith_1",
            "contrast_strategy": "focused_lighting",
            "camera_requirements": ["medium_shot"],
            "motion_requirements": ["static"],
            "temporal_requirements": ["realtime"],
        },
        "physical_questions": [
            {
                "id": "pq_crystal_ior",
                "domain": "optics",
                "question": "What is the physical refractive index of the crystal?",
                "related_entities": ["monolith_1"],
                "priority": "high",
            }
        ],
        "research_required": [
            {
                "id": "rr_dispersion",
                "topic": "crystal_dispersion_data",
                "reason": "Need dispersion values to produce plausible caustics",
                "desired_evidence": ["ior_table"],
                "priority": "medium",
            }
        ],
        "artistic_freedoms": [
            {
                "aspect": "levitation",
                "reason": "Monolith levitation requested for alien aesthetic",
            }
        ],
        "hard_constraints": ["Must maintain three distinct narrow colored light beams"],
        "ambiguities": [],
        "validation_targets": [
            {
                "id": "vt_caustics",
                "target": "internal_refraction_and_caustics",
                "domain": "optics",
            }
        ],
        "director_summary": "Reference scene: levitating transparent crystal monolith over dark basalt illuminated by three colored lights.",
    }
    return DirectorIntentContract(**payload)


def test_1_model_json_schema_produces_valid_dict():
    """Test 1: model_json_schema() produces a valid Python dictionary."""
    schema = DirectorIntentContract.model_json_schema()
    assert isinstance(schema, dict)
    assert "$defs" in schema or "properties" in schema


def test_2_schema_contains_expected_model_identity():
    """Test 2: Generated schema contains the expected top-level model title/identity."""
    schema = DirectorIntentContract.model_json_schema()
    assert schema.get("title") == "DirectorIntentContract"


def test_3_contract_version_restricted_to_0_1():
    """Test 3: contract_version schema is restricted to '0.1'."""
    schema = DirectorIntentContract.model_json_schema()
    contract_version_prop = schema["properties"]["contract_version"]
    # In Pydantic v2 Literal["0.1"] generates enum: ["0.1"] or const: "0.1"
    assert contract_version_prop.get("enum") == ["0.1"] or contract_version_prop.get("const") == "0.1"


def test_4_agent_schema_restricted_to_director_agent():
    """Test 4: agent schema is restricted to 'director_agent'."""
    schema = DirectorIntentContract.model_json_schema()
    agent_prop = schema["properties"]["agent"]
    assert agent_prop.get("enum") == ["director_agent"] or agent_prop.get("const") == "director_agent"


def test_5_reality_mode_exposes_exact_values():
    """Test 5: RealityMode exposes exact enum values."""
    schema = DirectorIntentContract.model_json_schema()
    reality_mode_schema = schema["$defs"]["RealityMode"]
    expected_values = [
        "strict_physical",
        "physically_grounded_artistic",
        "speculative_but_coherent",
        "explicitly_nonphysical",
    ]
    assert sorted(reality_mode_schema["enum"]) == sorted(expected_values)


def test_6_priority_exposes_exact_values():
    """Test 6: Priority exposes exact enum values."""
    schema = DirectorIntentContract.model_json_schema()
    priority_schema = schema["$defs"]["Priority"]
    expected_values = ["low", "medium", "high", "critical"]
    assert sorted(priority_schema["enum"]) == sorted(expected_values)


def test_7_ambiguity_resolution_exposes_exact_values():
    """Test 7: AmbiguityResolution exposes exact enum values."""
    schema = DirectorIntentContract.model_json_schema()
    resolution_schema = schema["$defs"]["AmbiguityResolution"]
    expected_values = [
        "defer_to_research_or_user",
        "art_directable",
        "requires_validation",
        "user_input_required",
    ]
    assert sorted(resolution_schema["enum"]) == sorted(expected_values)


def test_8_model_dump_mode_json_serialization(reference_contract_fixture: DirectorIntentContract):
    """Test 8: A valid DirectorIntentContract can be serialized with model_dump(mode='json')."""
    dumped = reference_contract_fixture.model_dump(mode="json")
    assert isinstance(dumped, dict)
    assert dumped["contract_version"] == "0.1"
    assert dumped["agent"] == "director_agent"
    assert dumped["creative_intent"]["reality_mode"] == "physically_grounded_artistic"


def test_9_model_dump_returns_json_safe_data(reference_contract_fixture: DirectorIntentContract):
    """Test 9: model_dump(mode='json') returns JSON-safe primitive data."""
    dumped = reference_contract_fixture.model_dump(mode="json")
    # Verify serializability via json.dumps without error
    json_str = json.dumps(dumped)
    assert isinstance(json_str, str)


def test_10_model_dump_json_serialization(reference_contract_fixture: DirectorIntentContract):
    """Test 10: A valid contract can be serialized with model_dump_json()."""
    json_str = reference_contract_fixture.model_dump_json()
    assert isinstance(json_str, str)
    assert '"contract_version":"0.1"' in json_str or '"contract_version": "0.1"' in json_str


def test_11_model_dump_json_output_parseable_by_json_module(
    reference_contract_fixture: DirectorIntentContract,
):
    """Test 11: model_dump_json() output can be parsed by Python's json module."""
    json_str = reference_contract_fixture.model_dump_json()
    parsed_dict = json.loads(json_str)
    assert isinstance(parsed_dict, dict)
    assert parsed_dict["director_summary"].startswith("Reference scene")


def test_12_round_trip_preserves_semantic_equality(
    reference_contract_fixture: DirectorIntentContract,
):
    """Test 12: Round trip DirectorIntentContract -> model_dump_json() -> model_validate_json() succeeds."""
    json_str = reference_contract_fixture.model_dump_json()
    reconstructed = DirectorIntentContract.model_validate_json(json_str)
    assert reconstructed == reference_contract_fixture


def test_13_unknown_fields_rejected_after_deserialization(
    reference_contract_fixture: DirectorIntentContract,
):
    """Test 13: Unknown fields are rejected when deserializing JSON."""
    raw_dict = reference_contract_fixture.model_dump(mode="json")
    raw_dict["unexpected_unknown_field"] = "invalid"
    json_str = json.dumps(raw_dict)

    with pytest.raises(ValidationError) as exc_info:
        DirectorIntentContract.model_validate_json(json_str)

    assert "unexpected_unknown_field" in str(exc_info.value)


def test_14_invalid_cross_entity_references_rejected_after_deserialization(
    reference_contract_fixture: DirectorIntentContract,
):
    """Test 14: Invalid cross-entity references are rejected after deserialization."""
    raw_dict = reference_contract_fixture.model_dump(mode="json")
    # Break material intent entity reference
    raw_dict["material_intent"][0]["entity_id"] = "non_existent_id"
    json_str = json.dumps(raw_dict)

    with pytest.raises(ValidationError) as exc_info:
        DirectorIntentContract.model_validate_json(json_str)

    assert "unknown entity_id: 'non_existent_id'" in str(exc_info.value)


def test_15_checked_in_schema_artifact_matches_canonical_generation():
    """Test 15: Checked-in JSON Schema artifact matches canonical schema generation byte-for-byte."""
    project_root = Path(__file__).resolve().parent.parent
    schema_path = project_root / "schemas" / "director-intent-contract-v0.1.schema.json"

    assert schema_path.exists(), f"Schema artifact missing at {schema_path}"

    checked_in_content = schema_path.read_text(encoding="utf-8")

    # Canonical serialization rule
    schema_dict = DirectorIntentContract.model_json_schema()
    canonical_generated_content = (
        json.dumps(
            schema_dict,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )

    assert (
        checked_in_content == canonical_generated_content
    ), "Checked-in schema artifact does not match canonical schema generation."


def test_16_schema_generation_repeatedly_produces_identical_output():
    """Test 16: Running schema generation repeatedly produces byte-identical output."""
    schema_1 = DirectorIntentContract.model_json_schema()
    output_1 = (
        json.dumps(
            schema_1,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )

    schema_2 = DirectorIntentContract.model_json_schema()
    output_2 = (
        json.dumps(
            schema_2,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )

    assert output_1 == output_2
