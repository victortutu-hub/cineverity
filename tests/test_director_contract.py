"""
Deterministic tests for Director Agent Contract v0.1 schema boundary validation.
"""

import pytest
from pydantic import ValidationError

from src.contracts.director_intent import (
    Ambiguity,
    AmbiguityResolution,
    ArtisticFreedom,
    CinematicIntent,
    CreativeIntent,
    DirectorIntentContract,
    EnvironmentIntent,
    LightingIntent,
    MaterialIntent,
    PhysicalQuestion,
    Priority,
    RealityMode,
    ResearchRequirement,
    SceneEntity,
    ValidationTarget,
)


def make_valid_contract_payload() -> dict:
    """Helper function to create a minimal valid DirectorIntentContract dictionary."""
    return {
        "contract_version": "0.1",
        "agent": "director_agent",
        "creative_intent": {
            "core_idea": "A crystal monolith floating in a cavern",
            "desired_emotion": ["mysterious", "awe"],
            "visual_priorities": ["refraction", "atmosphere"],
            "reality_mode": "physically_grounded_artistic",
        },
        "scene_entities": [
            {
                "id": "monolith_1",
                "type": "crystal_monolith",
                "description": "Large semi-transparent quartz monolith",
            },
            {
                "id": "ground_1",
                "type": "basalt_surface",
                "description": "Dark reflective basalt ground plane",
            },
        ],
        "material_intent": [
            {
                "entity_id": "monolith_1",
                "material_family": "crystal",
                "desired_properties": ["transparent", "high_dispersion"],
                "unknown_parameters": ["refractive_index"],
            }
        ],
        "lighting_intent": [
            {
                "id": "key_light",
                "role": "main_illumination",
                "color_intent": "cyan_glow",
                "interaction_target": "monolith_1",
            }
        ],
        "environment_intent": {
            "setting": "subterranean_cavern",
            "surface": "basalt_rock",
            "atmosphere": "light_fog",
            "background_priority": "dark",
            "environmental_effects": ["volumetric_dust"],
        },
        "cinematic_intent": {
            "visual_style": ["cinematic_macro"],
            "subject_priority": "monolith_1",
            "contrast_strategy": "high_key_subject_dark_background",
            "camera_requirements": ["35mm_prime"],
            "motion_requirements": ["slow_orbit"],
            "temporal_requirements": ["realtime"],
        },
        "physical_questions": [
            {
                "id": "pq_1",
                "domain": "optics",
                "question": "What is the refractive index of this crystal?",
                "related_entities": ["monolith_1"],
                "priority": "high",
            }
        ],
        "research_required": [
            {
                "id": "rr_1",
                "topic": "crystal_dispersion",
                "reason": "Need dispersion values for realistic caustics",
                "desired_evidence": ["cauchy_coefficients"],
                "priority": "medium",
            }
        ],
        "artistic_freedoms": [
            {
                "aspect": "levitation",
                "reason": "Antigravity monolith desired by artist",
            }
        ],
        "hard_constraints": ["Must maintain cyan lighting tint"],
        "ambiguities": [
            {
                "id": "amb_1",
                "topic": "exact_scale",
                "description": "Monolith size not quantitatively specified",
                "impact": "Framing and camera distance dependent",
                "resolution": "art_directable",
            }
        ],
        "validation_targets": [
            {
                "id": "vt_1",
                "target": "refraction_plausibility",
                "domain": "optics",
            }
        ],
        "director_summary": "Monolith in cavern with cyan lighting and internal refraction.",
    }


def test_1_valid_contract_accepted():
    """Test 1: Valid contract accepted."""
    payload = make_valid_contract_payload()
    contract = DirectorIntentContract(**payload)

    assert contract.contract_version == "0.1"
    assert contract.agent == "director_agent"
    assert contract.creative_intent.reality_mode == RealityMode.physically_grounded_artistic
    assert len(contract.scene_entities) == 2
    assert contract.scene_entities[0].id == "monolith_1"
    assert contract.material_intent[0].entity_id == "monolith_1"


def test_2_unknown_top_level_field_rejected():
    """Test 2: Unknown top-level field rejected due to extra='forbid'."""
    payload = make_valid_contract_payload()
    payload["unexpected_extra_field"] = "should_fail"

    with pytest.raises(ValidationError) as exc_info:
        DirectorIntentContract(**payload)

    assert "unexpected_extra_field" in str(exc_info.value)


def test_3_wrong_contract_version_rejected():
    """Test 3: Wrong contract_version rejected."""
    payload = make_valid_contract_payload()
    payload["contract_version"] = "0.2"

    with pytest.raises(ValidationError) as exc_info:
        DirectorIntentContract(**payload)

    assert "contract_version" in str(exc_info.value)


def test_4_wrong_agent_value_rejected():
    """Test 4: Wrong agent value rejected."""
    payload = make_valid_contract_payload()
    payload["agent"] = "wrong_agent"

    with pytest.raises(ValidationError) as exc_info:
        DirectorIntentContract(**payload)

    assert "agent" in str(exc_info.value)


def test_5_duplicate_scene_entity_ids_rejected():
    """Test 5: Duplicate SceneEntity IDs rejected."""
    payload = make_valid_contract_payload()
    payload["scene_entities"] = [
        {"id": "entity_A", "type": "type_1", "description": "desc_1"},
        {"id": "entity_A", "type": "type_2", "description": "desc_2"},
    ]
    # Update references to point to entity_A
    payload["material_intent"][0]["entity_id"] = "entity_A"
    payload["lighting_intent"][0]["interaction_target"] = "entity_A"
    payload["physical_questions"][0]["related_entities"] = ["entity_A"]

    with pytest.raises(ValidationError) as exc_info:
        DirectorIntentContract(**payload)

    assert "Duplicate SceneEntity IDs found" in str(exc_info.value)


def test_6_material_intent_unknown_entity_rejected():
    """Test 6: MaterialIntent unknown entity rejected."""
    payload = make_valid_contract_payload()
    payload["material_intent"][0]["entity_id"] = "non_existent_entity"

    with pytest.raises(ValidationError) as exc_info:
        DirectorIntentContract(**payload)

    assert "unknown entity_id: 'non_existent_entity'" in str(exc_info.value)


def test_7_physical_question_unknown_entity_rejected():
    """Test 7: PhysicalQuestion unknown entity rejected."""
    payload = make_valid_contract_payload()
    payload["physical_questions"][0]["related_entities"] = ["non_existent_entity"]

    with pytest.raises(ValidationError) as exc_info:
        DirectorIntentContract(**payload)

    assert "unknown related_entity: 'non_existent_entity'" in str(exc_info.value)


def test_8_lighting_intent_unknown_interaction_target_rejected():
    """Test 8: LightingIntent unknown interaction target rejected."""
    payload = make_valid_contract_payload()
    payload["lighting_intent"][0]["interaction_target"] = "non_existent_entity"

    with pytest.raises(ValidationError) as exc_info:
        DirectorIntentContract(**payload)

    assert "unknown interaction_target: 'non_existent_entity'" in str(exc_info.value)


def test_9_valid_cross_entity_references_accepted():
    """Test 9: Valid cross-entity references accepted (including interaction_target=None)."""
    payload = make_valid_contract_payload()
    # Test interaction_target = None
    payload["lighting_intent"][0]["interaction_target"] = None

    contract = DirectorIntentContract(**payload)
    assert contract.lighting_intent[0].interaction_target is None

    # Test interaction_target = valid entity id
    payload["lighting_intent"][0]["interaction_target"] = "ground_1"
    contract_2 = DirectorIntentContract(**payload)
    assert contract_2.lighting_intent[0].interaction_target == "ground_1"


def test_reference_case_schema_representation():
    """Verify schema can correctly represent the reference case structure."""
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

    contract = DirectorIntentContract(**payload)
    assert len(contract.scene_entities) == 2
    assert len(contract.lighting_intent) == 3
    assert contract.artistic_freedoms[0].aspect == "levitation"


def test_adversarial_case_schema_representation():
    """Verify schema can correctly represent the adversarial case structure and flag physical questions."""
    payload = {
        "contract_version": "0.1",
        "agent": "director_agent",
        "creative_intent": {
            "core_idea": "Diamond where red light refracts twice as strongly as blue light",
            "desired_emotion": ["surreal"],
            "visual_priorities": ["anomalous_dispersion"],
            "reality_mode": "physically_grounded_artistic",
        },
        "scene_entities": [
            {
                "id": "diamond_1",
                "type": "diamond",
                "description": "Diamond with custom requested red/blue dispersion behavior",
            }
        ],
        "material_intent": [
            {
                "entity_id": "diamond_1",
                "material_family": "diamond",
                "desired_properties": ["red_refracts_twice_as_strongly_as_blue"],
                "unknown_parameters": ["physical_compatibility"],
            }
        ],
        "lighting_intent": [
            {
                "id": "white_light",
                "role": "illumination",
                "color_intent": "pure_white",
                "interaction_target": "diamond_1",
            }
        ],
        "environment_intent": {
            "setting": "studio_void",
            "surface": "none",
            "atmosphere": "vacuum",
            "background_priority": "black",
            "environmental_effects": [],
        },
        "cinematic_intent": {
            "visual_style": ["macro"],
            "subject_priority": "diamond_1",
            "contrast_strategy": "high",
            "camera_requirements": ["macro_lens"],
            "motion_requirements": [],
            "temporal_requirements": [],
        },
        "physical_questions": [
            {
                "id": "pq_dispersion_conflict",
                "domain": "optics",
                "question": "Can diamond physically exhibit stronger red refraction than blue refraction under standard optics?",
                "related_entities": ["diamond_1"],
                "priority": "critical",
            }
        ],
        "research_required": [
            {
                "id": "rr_diamond_dispersion",
                "topic": "diamond_dispersion_curve",
                "reason": "Determine real diamond dispersion vs requested red/blue dispersion behavior",
                "desired_evidence": ["dispersion_data"],
                "priority": "high",
            }
        ],
        "artistic_freedoms": [
            {
                "aspect": "inverted_dispersion_spectrum",
                "reason": "Artist explicitly requested red refraction twice as strong as blue",
            }
        ],
        "hard_constraints": ["Red refraction strength must double blue refraction strength"],
        "ambiguities": [
            {
                "id": "amb_accuracy_conflict",
                "topic": "physical_accuracy_vs_artistic_dispersion",
                "description": "Potential conflict between requested dispersion and physical accuracy claim",
                "impact": "Physical validation step will report incompatibility",
                "resolution": "requires_validation",
            }
        ],
        "validation_targets": [
            {
                "id": "vt_dispersion",
                "target": "dispersion_order_check",
                "domain": "optics",
            }
        ],
        "director_summary": "Adversarial case: diamond with custom red/blue dispersion and explicit physical accuracy requirement.",
    }

    contract = DirectorIntentContract(**payload)
    assert contract.creative_intent.core_idea.startswith("Diamond where red light")
    assert contract.ambiguities[0].resolution == AmbiguityResolution.requires_validation
    assert contract.physical_questions[0].priority == Priority.critical
