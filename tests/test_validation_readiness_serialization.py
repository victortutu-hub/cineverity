"""Serialization boundary tests for ValidationReadinessContract v0.1."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.export_validation_readiness_schema import canonical_schema_text, export_schema
from src.contracts.validation_readiness import ValidationReadinessContract
from tests.test_validation_readiness_contract import payload


def contract() -> ValidationReadinessContract:
    data = payload()
    data["readiness_summary"] = "Readiness λ μ Å 漢字 remains unexecuted."
    return ValidationReadinessContract.model_validate(data)


def canonical_contract_json(model: ValidationReadinessContract) -> str:
    return json.dumps(model.model_dump(mode="json"), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def schema_path() -> Path:
    return Path(__file__).resolve().parent.parent / "schemas" / "validation-readiness-contract-v0.1.schema.json"


def test_1_schema_generation_has_validation_readiness_identity():
    schema = ValidationReadinessContract.model_json_schema()
    assert schema["title"] == "ValidationReadinessContract"
    assert schema["properties"]["contract_version"].get("const", schema["properties"]["contract_version"].get("enum")) in ("0.1", ["0.1"])
    assert schema["properties"]["agent"].get("const", schema["properties"]["agent"].get("enum")) in ("validation_readiness_agent", ["validation_readiness_agent"])


def test_2_schema_has_enums_strict_bool_and_sha_shape():
    schema = ValidationReadinessContract.model_json_schema(); defs = schema["$defs"]
    assert set(defs["ValidationReadinessState"]["enum"]) == {"structurally_checkable", "ready_for_execution", "blocked", "cannot_validate_yet"}
    assert set(defs["ValidationExecutionState"]["enum"]) == {"not_required", "not_executed", "unavailable"}
    scope = defs["ValidationReadinessScope"]["properties"]
    assert scope["director_contract_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert defs["ValidationArtisticDeviationReference"]["properties"]["requires_explicit_artist_acceptance"]["type"] == "boolean"


def test_3_schema_has_dependency_and_binding_models_and_is_strict():
    defs = ValidationReadinessContract.model_json_schema()["$defs"]
    assert "ValidationDependencyReference" in defs and "ValidationDependencyCoverage" in defs
    assert ValidationReadinessContract.model_json_schema()["additionalProperties"] is False
    assert defs["ValidationHookReference"]["additionalProperties"] is False


def test_4_checked_in_schema_equals_independent_expected_bytes():
    expected = (json.dumps(ValidationReadinessContract.model_json_schema(), indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    assert schema_path().read_bytes() == expected


def test_5_schema_artifact_is_utf8_lf_only_and_exactly_one_final_lf():
    artifact = schema_path().read_bytes()
    assert not artifact.startswith(b"\xef\xbb\xbf") and b"\r" not in artifact
    assert artifact.endswith(b"\n") and not artifact.endswith(b"\n\n")


def test_6_exporter_is_deterministic_in_temporary_paths(tmp_path):
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    assert export_schema(first) == first and export_schema(second) == second
    assert first.read_bytes() == second.read_bytes() == canonical_schema_text().encode("utf-8")


def test_7_repeated_canonical_schema_text_is_identical():
    assert canonical_schema_text() == canonical_schema_text()


def test_8_model_dump_mode_json_is_json_safe():
    dumped = contract().model_dump(mode="json")
    assert isinstance(json.dumps(dumped, ensure_ascii=False), str)
    assert dumped["input_scope"]["director_contract_sha256"] == "a" * 64


def test_9_canonical_contract_json_is_deterministic_unicode_safe_and_lf_terminated():
    rendered = canonical_contract_json(contract())
    assert rendered == canonical_contract_json(contract())
    assert "λ μ Å 漢字" in rendered and "\\u03bb" not in rendered
    assert rendered.endswith("\n") and not rendered.endswith("\n\n") and "\r" not in rendered


def test_10_canonical_json_round_trip_preserves_semantics_and_bindings():
    original = contract(); reconstructed = ValidationReadinessContract.model_validate_json(canonical_contract_json(original))
    assert reconstructed == original
    assert reconstructed.input_scope.scene_dependency_references == original.input_scope.scene_dependency_references
    assert reconstructed.dependency_coverage == original.dependency_coverage
    assert reconstructed.input_scope.scene_validation_hook_references == original.input_scope.scene_validation_hook_references


def test_11_model_dump_json_round_trip_preserves_semantics():
    original = contract(); assert ValidationReadinessContract.model_validate_json(original.model_dump_json()) == original


def test_12_list_order_is_preserved_not_sorted():
    model = contract(); data = model.model_dump(mode="json")
    data["input_scope"]["director_validation_target_ids"].reverse()
    data["input_scope"]["scene_validation_hook_references"].reverse()
    data["dependency_coverage"].reverse()
    rebuilt = ValidationReadinessContract.model_validate_json(json.dumps(data, ensure_ascii=False))
    assert rebuilt.input_scope.director_validation_target_ids == ["vt_disclosure", "vt_optics"]
    assert [x.scene_validation_hook_id for x in rebuilt.input_scope.scene_validation_hook_references] == ["hook_disclosure", "hook_optics"]


@pytest.mark.parametrize("mutate", [
    lambda p: p["input_scope"]["director_validation_target_ids"].append("vt_optics"),
    lambda p: p["input_scope"].update({"director_contract_sha256": "bad"}),
    lambda p: p["target_readiness"].pop(),
    lambda p: p["target_readiness"].append(deepcopy(p["target_readiness"][0])),
    lambda p: p["hook_readiness"][0].update({"physical_constraint_ids": []}),
    lambda p: p["dependency_coverage"].pop(),
    lambda p: p["dependency_coverage"][0].update({"scene_dependency_id": "invented"}),
    lambda p: p["dependency_coverage"][0].update({"validation_hook_ids": []}),
    lambda p: p["subject_readiness"].pop(),
    lambda p: p["subject_readiness"][3].update({"state": "ready_for_execution", "execution_state": "not_executed"}),
    lambda p: p.update({"unexpected": True}),
])
def test_13_validator_reexecution_rejects_representative_mutated_json(mutate):
    data = contract().model_dump(mode="json"); mutate(data)
    with pytest.raises(ValidationError):
        ValidationReadinessContract.model_validate_json(json.dumps(data, ensure_ascii=False))


def test_14_hook_subject_and_target_binding_survive_round_trip():
    data = contract().model_dump(mode="json")
    data["subject_readiness"][0]["validation_hook_ids"] = ["hook_disclosure"]
    with pytest.raises(ValidationError, match="unrelated validation hook"):
        ValidationReadinessContract.model_validate_json(json.dumps(data))
    data = contract().model_dump(mode="json")
    data["subject_readiness"][0]["director_validation_target_ids"] = ["vt_disclosure"]
    with pytest.raises(ValidationError, match="targets must be bound"):
        ValidationReadinessContract.model_validate_json(json.dumps(data))


def test_15_extra_unknown_nested_field_is_rejected_after_deserialization():
    data = contract().model_dump(mode="json"); data["input_scope"]["scene_dependency_references"][0]["extra"] = "no"
    with pytest.raises(ValidationError):
        ValidationReadinessContract.model_validate_json(json.dumps(data))


def ordered_payload():
    data = contract().model_dump(mode="json")
    data["input_scope"]["scene_dependency_references"].append(
        {"scene_dependency_id": "dep_z", "validation_hook_ids": []}
    )
    data["dependency_coverage"].append(
        {"scene_dependency_id": "dep_z", "validation_hook_ids": [], "prerequisites": ["Optional λ prerequisite."], "limitations": []}
    )
    data["input_scope"]["artistic_deviation_references"].append(
        {"artistic_deviation_id": "ad_z", "deviation_type": "artistic_amplification", "requires_explicit_artist_acceptance": False, "director_scene_entity_ids": ["crystal_1"], "director_physical_question_ids": ["pq_optics"]}
    )
    data["subject_readiness"].append(
        {"subject_kind": "artistic_deviation", "subject_id": "ad_z", "state": "blocked", "execution_state": "unavailable", "director_validation_target_ids": [], "validation_hook_ids": [], "dependency_ids": [], "prerequisites": ["Deferred creative review."], "limitations": []}
    )
    data["input_scope"]["scene_dependency_references"].reverse()
    data["dependency_coverage"].reverse()
    data["subject_readiness"].reverse()
    data["input_scope"]["artistic_deviation_references"].reverse()
    return data


def test_16_semantic_list_order_is_preserved_for_dependencies_subjects_and_deviations():
    data = ordered_payload()
    before = {
        "dependencies": [item["scene_dependency_id"] for item in data["input_scope"]["scene_dependency_references"]],
        "coverage": [item["scene_dependency_id"] for item in data["dependency_coverage"]],
        "subjects": [(item["subject_kind"], item["subject_id"]) for item in data["subject_readiness"]],
        "deviations": [item["artistic_deviation_id"] for item in data["input_scope"]["artistic_deviation_references"]],
    }
    rebuilt = ValidationReadinessContract.model_validate_json(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )
    assert [item.scene_dependency_id for item in rebuilt.input_scope.scene_dependency_references] == before["dependencies"]
    assert [item.scene_dependency_id for item in rebuilt.dependency_coverage] == before["coverage"]
    assert [(item.subject_kind.value, item.subject_id) for item in rebuilt.subject_readiness] == before["subjects"]
    assert [item.artistic_deviation_id for item in rebuilt.input_scope.artistic_deviation_references] == before["deviations"]


def test_17_duplicate_dependency_coverage_is_rejected_after_json_deserialization():
    data = contract().model_dump(mode="json")
    data["dependency_coverage"].append(deepcopy(data["dependency_coverage"][0]))
    with pytest.raises(ValidationError, match="Duplicate or blank dependency coverage IDs"):
        ValidationReadinessContract.model_validate_json(json.dumps(data))


@pytest.mark.parametrize(("status", "subject_index"), [("unsupported", 0), ("indeterminate", 0)])
def test_18_unsupported_or_indeterminate_cannot_escalate_after_json(status, subject_index):
    data = contract().model_dump(mode="json")
    data["input_scope"]["physical_constraint_references"][0]["status"] = status
    data["subject_readiness"][subject_index].update({"state": "ready_for_execution", "execution_state": "not_executed"})
    with pytest.raises(ValidationError, match="cannot be validation-ready"):
        ValidationReadinessContract.model_validate_json(json.dumps(data))


def test_19_conditional_constraint_cannot_become_unconditionally_checkable_after_json():
    data = contract().model_dump(mode="json")
    data["subject_readiness"][1].update({"state": "structurally_checkable", "execution_state": "not_required"})
    with pytest.raises(ValidationError, match="Conditional constraint cannot be unconditionally preflight-checkable"):
        ValidationReadinessContract.model_validate_json(json.dumps(data))


def test_20_conflict_cannot_become_positive_readiness_after_json():
    data = contract().model_dump(mode="json")
    data["subject_readiness"][2].update({"state": "ready_for_execution", "execution_state": "not_executed"})
    with pytest.raises(ValidationError, match="Physical conflict cannot be validation-ready"):
        ValidationReadinessContract.model_validate_json(json.dumps(data))