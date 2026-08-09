"""
Deterministic unit tests for Director Agent configuration and runtime validation boundary.

These tests run locally without making live Gemini network calls.
"""

import json
import pytest
from pydantic import ValidationError

from src.agents.director_agent import (
    director_agent,
    extract_text_from_adk_events,
    validate_director_response,
)
from src.contracts.director_intent import DirectorIntentContract


def make_sample_contract_payload() -> dict:
    """Return a minimal valid DirectorIntentContract dictionary."""
    return {
        "contract_version": "0.1",
        "agent": "director_agent",
        "creative_intent": {
            "core_idea": "A floating crystal",
            "desired_emotion": ["mysterious"],
            "visual_priorities": ["refraction"],
            "reality_mode": "physically_grounded_artistic",
        },
        "scene_entities": [
            {
                "id": "crystal_1",
                "type": "crystal",
                "description": "Quartz monolith",
            }
        ],
        "material_intent": [
            {
                "entity_id": "crystal_1",
                "material_family": "crystal",
                "desired_properties": ["transparent"],
                "unknown_parameters": ["refractive_index"],
            }
        ],
        "lighting_intent": [
            {
                "id": "light_1",
                "role": "key",
                "color_intent": "white",
                "interaction_target": "crystal_1",
            }
        ],
        "environment_intent": {
            "setting": "void",
            "surface": None,
            "atmosphere": None,
            "background_priority": None,
            "environmental_effects": [],
        },
        "cinematic_intent": {
            "visual_style": ["macro"],
            "subject_priority": "crystal_1",
            "contrast_strategy": "high",
            "camera_requirements": [],
            "motion_requirements": [],
            "temporal_requirements": [],
        },
        "physical_questions": [],
        "research_required": [],
        "artistic_freedoms": [],
        "hard_constraints": [],
        "ambiguities": [],
        "validation_targets": [],
        "director_summary": "Minimal valid director intent contract",
    }


def test_1_director_agent_name():
    """Test 1: Director Agent is configured with the expected name."""
    assert director_agent.name == "director_agent"


def test_2_director_agent_has_no_tools():
    """Test 2: Director Agent has no tools."""
    assert director_agent.tools == [] or len(director_agent.tools) == 0


def test_3_director_agent_output_schema():
    """Test 3: Director Agent uses DirectorIntentContract as structured output schema."""
    assert director_agent.output_schema == DirectorIntentContract


def test_4_runtime_validation_accepts_valid_json():
    """Test 4: Runtime validation accepts valid Director JSON."""
    payload = make_sample_contract_payload()
    json_str = json.dumps(payload)

    validated = validate_director_response(json_str)
    assert isinstance(validated, DirectorIntentContract)
    assert validated.contract_version == "0.1"
    assert validated.scene_entities[0].id == "crystal_1"


def test_5_runtime_validation_rejects_unknown_field():
    """Test 5: Runtime validation rejects an unknown top-level field."""
    payload = make_sample_contract_payload()
    payload["unexpected_field"] = "bad_val"
    json_str = json.dumps(payload)

    with pytest.raises(ValueError) as exc_info:
        validate_director_response(json_str)

    assert "unexpected_field" in str(exc_info.value)


def test_6_runtime_validation_rejects_invalid_cross_entity_references():
    """Test 6: Runtime validation rejects invalid cross-entity references."""
    payload = make_sample_contract_payload()
    payload["material_intent"][0]["entity_id"] = "unknown_entity"
    json_str = json.dumps(payload)

    with pytest.raises(ValueError) as exc_info:
        validate_director_response(json_str)

    assert "unknown entity_id: 'unknown_entity'" in str(exc_info.value)


def test_7_event_response_extraction_ignores_metadata_and_extracts_text():
    """Test 7: Event-response extraction ignores metadata/thoughts and extracts text."""
    sample_events = [
        {
            "metadata": {"invocation_id": "inv_123", "step": 1},
            "content": {
                "role": "model",
                "parts": [
                    {"thought": True, "text": "Reasoning step internal thought"},
                    {"text": '{"contract_version": '},
                ],
            },
        },
        {
            "metadata": {"invocation_id": "inv_123", "step": 2},
            "content": {
                "role": "model",
                "parts": [
                    {"text": '"0.1"}'},
                ],
            },
        },
    ]

    extracted_text = extract_text_from_adk_events(sample_events)
    assert extracted_text == '{"contract_version": "0.1"}'
    assert "Reasoning step internal thought" not in extracted_text


def test_8_event_response_extraction_handles_adk_event_shape():
    """Test 8: Event-response extraction handles standard ADK event dictionary shape."""
    payload = make_sample_contract_payload()
    json_str = json.dumps(payload)

    sample_events = [
        {
            "id": "event_1",
            "content": {
                "parts": [{"text": json_str}]
            },
        }
    ]

    text = extract_text_from_adk_events(sample_events)
    validated = validate_director_response(text)
    assert validated.agent == "director_agent"


def test_9_validation_errors_fail_clearly_without_repair():
    """Test 9: Validation errors fail clearly with ValueError without silent repair."""
    malformed_json = '{"contract_version": "0.1", "agent": "director_agent"}'  # missing required fields

    with pytest.raises(ValueError) as exc_info:
        validate_director_response(malformed_json)

    assert "Director Agent response failed Pydantic validation" in str(exc_info.value)
