"""Deterministic serialization tests for ScenePlanningContract v0.1."""

from copy import deepcopy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.export_scene_planning_schema import canonical_schema_text, export_schema
from src.contracts.scene_planning import (
    SceneDecisionStatus,
    SceneParameterValueKind,
    ScenePlanningContract,
)


DIRECTOR_SHA = "a" * 64
PHYSICAL_SHA = "b" * 64


def valid_payload() -> dict:
    return {
        "contract_version": "0.1", "agent": "scene_planning_agent",
        "input_scope": {
            "director_contract_sha256": DIRECTOR_SHA,
            "physical_constraints_contract_sha256": PHYSICAL_SHA,
            "director_scene_entity_ids": ["crystal_1"],
            "director_validation_target_ids": ["vt_1"],
            "director_physical_question_ids": ["pq_1"],
            "director_material_unknown_parameters": [{"entity_id": "crystal_1", "parameter": "refractive_index"}],
            "physical_constraint_references": [{"physical_constraint_id": "pc_1", "status": "supported", "director_scene_entity_ids": ["crystal_1"], "director_physical_question_ids": ["pq_1"], "related_material_unknown_parameters": []}],
            "physical_conflict_references": [],
            "unresolved_physical_constraint_references": [{"unresolved_physical_constraint_id": "uc_1", "director_scene_entity_ids": ["crystal_1"], "director_physical_question_ids": ["pq_1"], "related_material_unknown_parameters": [{"entity_id": "crystal_1", "parameter": "refractive_index"}]}],
            "artistic_deviation_references": [{"artistic_deviation_id": "ad_1", "deviation_type": "artistic_amplification", "requires_explicit_artist_acceptance": True, "director_scene_entity_ids": ["crystal_1"], "director_physical_question_ids": ["pq_1"], "related_material_unknown_parameters": [{"entity_id": "crystal_1", "parameter": "refractive_index"}]}],
            "material_identity_references": [{"physical_constraint_id": "pc_1", "scene_entity_id": "crystal_1", "status": "unresolved", "identity_label": None}],
        },
        "decisions": [
            {"id": "d_ground", "kind": "physically_grounded_realization", "status": "committed", "description": "Fizică, lumină, refracție — λ μ Å 漢字.", "target_scene_entity_ids": ["crystal_1"], "basis": {"director_physical_question_ids": ["pq_1"], "grounding_constraint_ids": ["pc_1"], "constraining_constraint_ids": [], "physical_conflict_ids": [], "artistic_deviation_ids": [], "unresolved_physical_constraint_ids": [], "implementation_rationale": None}, "conditions": [], "dependency_ids": []},
            {"id": "d_unknown", "kind": "unresolved_dependency_handling", "status": "deferred", "description": "Preserve unknown.", "target_scene_entity_ids": ["crystal_1"], "basis": {"director_physical_question_ids": ["pq_1"], "grounding_constraint_ids": [], "constraining_constraint_ids": [], "physical_conflict_ids": [], "artistic_deviation_ids": [], "unresolved_physical_constraint_ids": ["uc_1"], "implementation_rationale": None}, "conditions": [], "dependency_ids": ["dep_unknown", "dep_identity"]},
            {"id": "d_art", "kind": "artistic_deviation_realization", "status": "conditional", "description": "Artist decision required.", "target_scene_entity_ids": ["crystal_1"], "basis": {"director_physical_question_ids": ["pq_1"], "grounding_constraint_ids": [], "constraining_constraint_ids": [], "physical_conflict_ids": [], "artistic_deviation_ids": ["ad_1"], "unresolved_physical_constraint_ids": [], "implementation_rationale": None}, "conditions": ["artist accepts"], "dependency_ids": ["dep_accept"]},
        ],
        "parameter_assignments": [{"id": "pa_1", "decision_id": "d_unknown", "target_scene_entity_id": "crystal_1", "parameter_name": "refractive_index", "category": "material", "role": "unresolved", "value": {"kind": "unresolved", "numeric_value": None, "categorical_value": None, "descriptive_value": None, "boolean_value": None, "unit": None}, "dependency_ids": ["dep_unknown"]}],
        "material_plans": [{"id": "mp_1", "decision_id": "d_unknown", "scene_entity_id": "crystal_1", "identity_mode": "unresolved_abstract", "material_identity_selector": None, "identity_label": None, "limitation": None, "dependency_ids": ["dep_identity"]}],
        "dependencies": [
            {"id": "dep_unknown", "kind": "unresolved_physical_constraint", "unresolved_physical_constraint_id": "uc_1", "physical_conflict_id": None, "material_identity_selector": None, "artistic_deviation_id": None, "reason": "Missing scene value."},
            {"id": "dep_identity", "kind": "material_identity_uncertainty", "unresolved_physical_constraint_id": None, "physical_conflict_id": None, "material_identity_selector": {"physical_constraint_id": "pc_1", "scene_entity_id": "crystal_1"}, "artistic_deviation_id": None, "reason": "Identity unknown."},
            {"id": "dep_accept", "kind": "artist_acceptance", "unresolved_physical_constraint_id": None, "physical_conflict_id": None, "material_identity_selector": None, "artistic_deviation_id": "ad_1", "reason": "Await acceptance."},
        ],
        "artistic_deviation_realizations": [{"id": "ar_1", "artistic_deviation_id": "ad_1", "deviation_type": "artistic_amplification", "requires_explicit_artist_acceptance": True, "target_scene_entity_ids": ["crystal_1"], "decision_ids": ["d_art"], "status": "conditional", "dependency_ids": ["dep_accept"], "description": "Explicit artistic amplification."}],
        "shot_plan": [
            {"id": "shot_2", "sequence_index": 1, "purpose": "Second in input order.", "decision_ids": ["d_ground"], "temporal_beats": [{"id": "beat_2", "sequence_index": 1, "description": "Second beat first.", "decision_ids": ["d_ground"]}, {"id": "beat_1", "sequence_index": 0, "description": "First beat second.", "decision_ids": ["d_ground"]}]},
            {"id": "shot_1", "sequence_index": 0, "purpose": "First in input order.", "decision_ids": ["d_unknown", "d_art"], "temporal_beats": []},
        ],
        "validation_hooks": [
            {"id": "hook_target", "kind": "director_target_check", "description": "Check target.", "decision_ids": ["d_ground"], "dependency_ids": [], "director_validation_target_ids": ["vt_1"], "physical_constraint_ids": [], "artistic_deviation_ids": [], "unresolved_physical_constraint_ids": [], "physical_conflict_ids": []},
            {"id": "hook_pc", "kind": "physical_constraint_check", "description": "Check constraint.", "decision_ids": ["d_ground"], "dependency_ids": [], "director_validation_target_ids": [], "physical_constraint_ids": ["pc_1"], "artistic_deviation_ids": [], "unresolved_physical_constraint_ids": [], "physical_conflict_ids": []},
            {"id": "hook_u", "kind": "unresolved_dependency_check", "description": "Check uncertainty.", "decision_ids": ["d_unknown"], "dependency_ids": ["dep_unknown", "dep_identity"], "director_validation_target_ids": [], "physical_constraint_ids": [], "artistic_deviation_ids": [], "unresolved_physical_constraint_ids": ["uc_1"], "physical_conflict_ids": []},
            {"id": "hook_a", "kind": "artistic_deviation_disclosure_check", "description": "Check disclosure.", "decision_ids": ["d_art"], "dependency_ids": ["dep_accept"], "director_validation_target_ids": [], "physical_constraint_ids": [], "artistic_deviation_ids": ["ad_1"], "unresolved_physical_constraint_ids": [], "physical_conflict_ids": []},
        ],
        "coverage": [
            {"subject_kind": "physical_constraint", "subject_id": "pc_1", "state": "realized", "decision_ids": ["d_ground"], "dependency_ids": [], "validation_hook_ids": ["hook_pc"], "reason": None},
            {"subject_kind": "unresolved_physical_constraint", "subject_id": "uc_1", "state": "deferred", "decision_ids": ["d_unknown"], "dependency_ids": ["dep_unknown"], "validation_hook_ids": ["hook_u"], "reason": "Value unresolved."},
            {"subject_kind": "artistic_deviation", "subject_id": "ad_1", "state": "conditional", "decision_ids": ["d_art"], "dependency_ids": ["dep_accept"], "validation_hook_ids": ["hook_a"], "reason": None},
        ],
        "scene_plan_summary": "fizică, lumină, refracție — λ μ Å 漢字",
    }


@pytest.fixture
def reference_contract() -> ScenePlanningContract:
    return ScenePlanningContract.model_validate(valid_payload())


def canonical_contract_text(contract: ScenePlanningContract) -> str:
    return json.dumps(contract.model_dump(mode="json"), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def assert_invalid_json(payload: dict) -> None:
    with pytest.raises(ValidationError):
        ScenePlanningContract.model_validate_json(json.dumps(payload))


def test_1_model_json_schema_returns_dict(): assert isinstance(ScenePlanningContract.model_json_schema(), dict)
def test_2_schema_identity_title(): assert ScenePlanningContract.model_json_schema()["title"] == "ScenePlanningContract"
def test_3_contract_version_is_restricted():
    field = ScenePlanningContract.model_json_schema()["properties"]["contract_version"]
    assert field.get("enum") == ["0.1"] or field.get("const") == "0.1"
def test_4_agent_is_restricted():
    field = ScenePlanningContract.model_json_schema()["properties"]["agent"]
    assert field.get("enum") == ["scene_planning_agent"] or field.get("const") == "scene_planning_agent"
def test_5_important_enums_are_exact():
    schema = ScenePlanningContract.model_json_schema()["$defs"]
    assert schema["SceneDecisionStatus"]["enum"] == [member.value for member in SceneDecisionStatus]
    assert schema["SceneParameterValueKind"]["enum"] == [member.value for member in SceneParameterValueKind]


def test_6_model_dump_mode_json_is_json_safe(reference_contract): assert json.dumps(reference_contract.model_dump(mode="json"))
def test_7_canonical_contract_keys_are_sorted(reference_contract): assert canonical_contract_text(reference_contract).startswith('{\n  "agent": "scene_planning_agent",')
def test_8_canonical_contract_rendering_is_deterministic(reference_contract): assert canonical_contract_text(reference_contract) == canonical_contract_text(reference_contract)
def test_9_unicode_is_literal_and_utf8_exact(reference_contract):
    rendered = canonical_contract_text(reference_contract); artifact = rendered.encode("utf-8")
    assert "fizică, lumină, refracție — λ μ Å 漢字" in rendered
    assert "\\u03bb" not in rendered and artifact.decode("utf-8") == rendered
def test_10_canonical_contract_is_lf_only_with_one_final_lf(reference_contract):
    rendered = canonical_contract_text(reference_contract); assert "\r" not in rendered and rendered.endswith("\n") and not rendered.endswith("\n\n")
def test_11_canonical_bytes_are_utf8_without_bom(reference_contract):
    artifact = canonical_contract_text(reference_contract).encode("utf-8"); assert not artifact.startswith(b"\xef\xbb\xbf") and artifact.endswith(b"\n") and not artifact.endswith(b"\n\n")
def test_12_canonical_json_round_trip_is_semantically_equal(reference_contract): assert ScenePlanningContract.model_validate_json(canonical_contract_text(reference_contract)) == reference_contract
def test_13_canonical_bytes_round_trip_is_byte_identical(reference_contract):
    first = canonical_contract_text(reference_contract).encode("utf-8")
    reconstructed = ScenePlanningContract.model_validate_json(first.decode("utf-8"))
    assert canonical_contract_text(reconstructed).encode("utf-8") == first
def test_14_repeated_round_trip_is_stable(reference_contract):
    rendered = canonical_contract_text(reference_contract)
    for _ in range(3): rendered = canonical_contract_text(ScenePlanningContract.model_validate_json(rendered))
    assert rendered == canonical_contract_text(reference_contract)
def test_15_model_dump_json_is_only_semantic_round_trip(reference_contract): assert ScenePlanningContract.model_validate_json(reference_contract.model_dump_json()) == reference_contract
def test_16_rendering_does_not_mutate_model(reference_contract):
    before = deepcopy(reference_contract.model_dump(mode="json")); canonical_contract_text(reference_contract); assert reference_contract.model_dump(mode="json") == before
def test_17_list_order_is_preserved(reference_contract):
    dumped = json.loads(canonical_contract_text(reference_contract))
    assert [item["id"] for item in dumped["shot_plan"]] == ["shot_2", "shot_1"]
    assert [item["id"] for item in dumped["shot_plan"][0]["temporal_beats"]] == ["beat_2", "beat_1"]
    assert [item["id"] for item in dumped["dependencies"]] == ["dep_unknown", "dep_identity", "dep_accept"]
    assert [item["id"] for item in dumped["validation_hooks"]] == ["hook_target", "hook_pc", "hook_u", "hook_a"]
    assert [item["subject_id"] for item in dumped["coverage"]] == ["pc_1", "uc_1", "ad_1"]
    assert dumped["input_scope"]["director_scene_entity_ids"] == ["crystal_1"]
@pytest.mark.parametrize("lexical", ["1.5", "1.50", "01.5", "1.5e0"])
def test_18_numeric_lexical_form_is_preserved(lexical):
    payload = valid_payload(); value = payload["parameter_assignments"][0]["value"]
    payload["parameter_assignments"][0]["role"] = "provisional_placeholder"
    value.update({"kind": "numeric", "numeric_value": lexical, "unit": "m"})
    contract = ScenePlanningContract.model_validate(payload)
    assert json.loads(canonical_contract_text(contract))["parameter_assignments"][0]["value"]["numeric_value"] == lexical
def test_19_distinct_numeric_lexical_forms_have_distinct_bytes():
    payload_a = valid_payload(); payload_b = valid_payload()
    for payload, lexical in ((payload_a, "1.5"), (payload_b, "1.50")):
        payload["parameter_assignments"][0]["role"] = "provisional_placeholder"
        payload["parameter_assignments"][0]["value"].update({"kind": "numeric", "numeric_value": lexical, "unit": "m"})
    assert canonical_contract_text(ScenePlanningContract.model_validate(payload_a)).encode() != canonical_contract_text(ScenePlanningContract.model_validate(payload_b)).encode()
def test_20_sha_values_are_preserved_exactly(reference_contract):
    scope = json.loads(canonical_contract_text(reference_contract))["input_scope"]
    assert scope["director_contract_sha256"] == DIRECTOR_SHA and scope["physical_constraints_contract_sha256"] == PHYSICAL_SHA
def test_21_json_types_follow_pydantic_conventions(reference_contract):
    dumped = json.loads(canonical_contract_text(reference_contract))
    assert dumped["input_scope"]["artistic_deviation_references"][0]["requires_explicit_artist_acceptance"] is True
    assert dumped["material_plans"][0]["identity_label"] is None
    assert dumped["decisions"][0]["status"] == "committed"
def test_22_invalid_json_is_rejected():
    with pytest.raises(ValidationError): ScenePlanningContract.model_validate_json("{")
def test_23_unknown_top_level_field_is_rejected(reference_contract):
    payload = reference_contract.model_dump(mode="json"); payload["unknown"] = True; assert_invalid_json(payload)
def test_24_unknown_nested_field_is_rejected(reference_contract):
    payload = reference_contract.model_dump(mode="json"); payload["decisions"][0]["unknown"] = True; assert_invalid_json(payload)
def test_25_invalid_cross_reference_is_rejected(reference_contract):
    payload = reference_contract.model_dump(mode="json"); payload["parameter_assignments"][0]["decision_id"] = "missing"; assert_invalid_json(payload)
def test_26_invalid_coverage_relationship_is_rejected(reference_contract):
    payload = reference_contract.model_dump(mode="json"); payload["coverage"][0]["decision_ids"] = ["d_unknown"]; assert_invalid_json(payload)
def test_27_invalid_dependency_relationship_is_rejected(reference_contract):
    payload = reference_contract.model_dump(mode="json"); payload["decisions"][0]["dependency_ids"] = ["dep_unknown"]; assert_invalid_json(payload)
def test_28_checked_in_schema_matches_independent_canonical_bytes():
    path = Path(__file__).resolve().parent.parent / "schemas" / "scene-planning-contract-v0.1.schema.json"
    expected = (json.dumps(ScenePlanningContract.model_json_schema(), indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    assert path.read_bytes() == expected
def test_29_canonical_schema_text_is_deterministic_lf_only_and_one_final_lf():
    first = canonical_schema_text(); assert first == canonical_schema_text() and "\r" not in first and first.endswith("\n") and not first.endswith("\n\n")
def test_30_exported_schema_is_utf8_without_bom_and_valid_json(tmp_path):
    artifact = export_schema(tmp_path / "schema.json").read_bytes()
    assert json.loads(artifact.decode("utf-8"))["title"] == "ScenePlanningContract"
    assert not artifact.startswith(b"\xef\xbb\xbf") and artifact.endswith(b"\n") and not artifact.endswith(b"\n\n")
def test_31_repeated_schema_export_is_byte_identical(tmp_path):
    path = tmp_path / "schema.json"; export_schema(path); first = path.read_bytes(); export_schema(path); assert path.read_bytes() == first
