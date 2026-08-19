"""Offline structural tests for Validation Readiness Contract v0.1."""

from copy import deepcopy
import json

import pytest
from pydantic import ValidationError

from src.contracts.validation_readiness import ValidationReadinessContract

H = "a" * 64


def payload():
    return {
        "contract_version": "0.1", "agent": "validation_readiness_agent",
        "input_scope": {
            "director_contract_sha256": H, "physical_constraints_contract_sha256": "b" * 64, "scene_planning_contract_sha256": "c" * 64,
            "director_validation_target_ids": ["vt_optics", "vt_disclosure"], "director_scene_entity_ids": ["crystal_1"], "director_physical_question_ids": ["pq_optics"],
            "physical_constraint_references": [{"physical_constraint_id": "pc_supported", "status": "supported", "director_scene_entity_ids": ["crystal_1"], "director_physical_question_ids": ["pq_optics"]}, {"physical_constraint_id": "pc_conditional", "status": "conditionally_supported", "director_scene_entity_ids": ["crystal_1"], "director_physical_question_ids": ["pq_optics"]}],
            "physical_conflict_references": [{"physical_conflict_id": "cf_1", "resolution_status": "unresolved", "physical_constraint_ids": ["pc_supported"], "director_physical_question_ids": ["pq_optics"]}],
            "unresolved_physical_constraint_references": [{"unresolved_physical_constraint_id": "uc_1", "director_scene_entity_ids": ["crystal_1"], "director_physical_question_ids": ["pq_optics"]}],
            "artistic_deviation_references": [{"artistic_deviation_id": "ad_1", "deviation_type": "artistic_amplification", "requires_explicit_artist_acceptance": True, "director_scene_entity_ids": ["crystal_1"], "director_physical_question_ids": ["pq_optics"]}],
            "scene_validation_hook_references": [{"scene_validation_hook_id": "hook_optics", "kind": "director_target_check", "director_validation_target_ids": ["vt_optics"], "physical_constraint_ids": ["pc_supported"], "physical_conflict_ids": [], "unresolved_physical_constraint_ids": [], "artistic_deviation_ids": [], "dependency_ids": []}, {"scene_validation_hook_id": "hook_disclosure", "kind": "artistic_deviation_disclosure_check", "director_validation_target_ids": ["vt_disclosure"], "physical_constraint_ids": [], "physical_conflict_ids": [], "unresolved_physical_constraint_ids": [], "artistic_deviation_ids": ["ad_1"], "dependency_ids": ["dep_accept"]}],
            "scene_dependency_references": [{"scene_dependency_id": "dep_accept", "validation_hook_ids": ["hook_disclosure"]}],
        },
        "target_readiness": [{"director_validation_target_id": "vt_optics", "state": "structurally_checkable", "execution_state": "not_required", "validation_hook_ids": ["hook_optics"], "physical_constraint_ids": ["pc_supported"], "physical_conflict_ids": [], "unresolved_physical_constraint_ids": [], "artistic_deviation_ids": [], "dependency_ids": [], "prerequisites": [], "limitations": []}, {"director_validation_target_id": "vt_disclosure", "state": "blocked", "execution_state": "unavailable", "validation_hook_ids": ["hook_disclosure"], "physical_constraint_ids": [], "physical_conflict_ids": [], "unresolved_physical_constraint_ids": [], "artistic_deviation_ids": ["ad_1"], "dependency_ids": ["dep_accept"], "prerequisites": ["Authorized artist acceptance is not supplied."], "limitations": ["Acceptance has not been executed or supplied."]}],
        "hook_readiness": [{"scene_validation_hook_id": "hook_optics", "state": "structurally_checkable", "execution_state": "not_required", "director_validation_target_ids": ["vt_optics"], "physical_constraint_ids": ["pc_supported"], "physical_conflict_ids": [], "unresolved_physical_constraint_ids": [], "artistic_deviation_ids": [], "dependency_ids": [], "prerequisites": [], "limitations": []}, {"scene_validation_hook_id": "hook_disclosure", "state": "blocked", "execution_state": "unavailable", "director_validation_target_ids": ["vt_disclosure"], "physical_constraint_ids": [], "physical_conflict_ids": [], "unresolved_physical_constraint_ids": [], "artistic_deviation_ids": ["ad_1"], "dependency_ids": ["dep_accept"], "prerequisites": ["Acceptance source required."], "limitations": []}],
        "subject_readiness": [{"subject_kind": "physical_constraint", "subject_id": "pc_supported", "state": "structurally_checkable", "execution_state": "not_required", "director_validation_target_ids": ["vt_optics"], "validation_hook_ids": ["hook_optics"], "dependency_ids": [], "prerequisites": [], "limitations": []}, {"subject_kind": "physical_constraint", "subject_id": "pc_conditional", "state": "blocked", "execution_state": "unavailable", "director_validation_target_ids": [], "validation_hook_ids": [], "dependency_ids": [], "prerequisites": ["Condition remains active."], "limitations": []}, {"subject_kind": "physical_conflict", "subject_id": "cf_1", "state": "blocked", "execution_state": "unavailable", "director_validation_target_ids": [], "validation_hook_ids": [], "dependency_ids": [], "prerequisites": ["Conflict unresolved."], "limitations": []}, {"subject_kind": "unresolved_physical_constraint", "subject_id": "uc_1", "state": "cannot_validate_yet", "execution_state": "unavailable", "director_validation_target_ids": [], "validation_hook_ids": [], "dependency_ids": [], "prerequisites": ["Evidence absent."], "limitations": []}, {"subject_kind": "artistic_deviation", "subject_id": "ad_1", "state": "blocked", "execution_state": "unavailable", "director_validation_target_ids": ["vt_disclosure"], "validation_hook_ids": ["hook_disclosure"], "dependency_ids": ["dep_accept"], "prerequisites": ["Artist acceptance required."], "limitations": []}],
        "dependency_coverage": [{"scene_dependency_id": "dep_accept", "validation_hook_ids": ["hook_disclosure"], "prerequisites": ["Acceptance source required."], "limitations": []}],
        "required_execution_classes": ["contract_preflight"], "readiness_summary": "Structural readiness λ μ Å 漢字; no execution has occurred.", "limitations": ["No renderer, simulation, measurement, or scientific execution occurred."],
    }


def valid(): return ValidationReadinessContract.model_validate(payload())
def invalid(mutate):
    value = payload(); mutate(value)
    with pytest.raises(ValidationError): ValidationReadinessContract.model_validate(value)


def test_1_minimal_full_valid_contract_and_unicode_round_trip():
    model = valid(); assert "λ μ Å 漢字" in model.readiness_summary
    assert ValidationReadinessContract.model_validate_json(model.model_dump_json()) == model


def test_2_json_safe_dump_and_json_round_trip_reruns_validators():
    model = valid(); dumped = model.model_dump(mode="json")
    assert isinstance(dumped["input_scope"]["director_contract_sha256"], str)
    dumped["target_readiness"].pop()
    with pytest.raises(ValidationError): ValidationReadinessContract.model_validate_json(json.dumps(dumped))


@pytest.mark.parametrize("field", ["director_validation_target_ids", "director_scene_entity_ids", "director_physical_question_ids", "scene_dependency_references"])
def test_3_scope_duplicate_ids_rejected(field): invalid(lambda p: p["input_scope"][field].append(p["input_scope"][field][0]))


@pytest.mark.parametrize("field", ["director_contract_sha256", "physical_constraints_contract_sha256", "scene_planning_contract_sha256"])
def test_4_invalid_fingerprint_shape_rejected(field): invalid(lambda p: p["input_scope"].__setitem__(field, "A" * 64))


def test_5_missing_target_coverage_rejected(): invalid(lambda p: p["target_readiness"].pop())
def test_6_extra_target_coverage_rejected(): invalid(lambda p: p["target_readiness"].append(deepcopy(p["target_readiness"][0])))
def test_7_target_outside_scope_rejected(): invalid(lambda p: p["target_readiness"][0].update({"director_validation_target_id": "other"}))
def test_8_target_hook_cross_reassignment_rejected(): invalid(lambda p: p["target_readiness"][0].update({"validation_hook_ids": ["hook_disclosure"]}))
def test_9_missing_hook_coverage_rejected(): invalid(lambda p: p["hook_readiness"].pop())
def test_10_extra_hook_coverage_rejected(): invalid(lambda p: p["hook_readiness"].append(deepcopy(p["hook_readiness"][0])))
def test_11_hook_cannot_mutate_authoritative_references(): invalid(lambda p: p["hook_readiness"][0].update({"physical_constraint_ids": []}))
def test_12_unknown_constraint_reference_rejected(): invalid(lambda p: p["target_readiness"][0].update({"physical_constraint_ids": ["unknown"]}))

def test_12a_subject_hook_reassignment_rejected(): invalid(lambda p: p["subject_readiness"][0].update({"validation_hook_ids": ["hook_disclosure"]}))

def test_12b_target_subject_hook_reassignment_rejected(): invalid(lambda p: p["target_readiness"][0].update({"physical_constraint_ids": ["pc_conditional"]}))
def test_13_unknown_conflict_reference_rejected(): invalid(lambda p: p["target_readiness"][0].update({"physical_conflict_ids": ["unknown"]}))
def test_14_unknown_unresolved_reference_rejected(): invalid(lambda p: p["target_readiness"][0].update({"unresolved_physical_constraint_ids": ["unknown"]}))
def test_15_unknown_deviation_reference_rejected(): invalid(lambda p: p["target_readiness"][0].update({"artistic_deviation_ids": ["unknown"]}))
def test_16_unknown_dependency_reference_rejected(): invalid(lambda p: p["target_readiness"][1].update({"dependency_ids": ["unknown"]}))

def test_16a_missing_dependency_coverage_rejected(): invalid(lambda p: p["dependency_coverage"].pop())

def test_16b_invented_dependency_coverage_rejected(): invalid(lambda p: p["dependency_coverage"][0].update({"scene_dependency_id": "invented"}))

def test_16c_duplicate_dependency_coverage_rejected(): invalid(lambda p: p["dependency_coverage"].append(deepcopy(p["dependency_coverage"][0])))

def test_16d_dependency_hook_binding_must_be_preserved(): invalid(lambda p: p["dependency_coverage"][0].update({"validation_hook_ids": []}))
def test_17_missing_subject_coverage_rejected(): invalid(lambda p: p["subject_readiness"].pop())
def test_18_duplicate_subject_coverage_rejected(): invalid(lambda p: p["subject_readiness"].append(deepcopy(p["subject_readiness"][0])))
def test_19_unresolved_cannot_be_ready_or_passed(): invalid(lambda p: p["subject_readiness"][3].update({"state": "ready_for_execution", "execution_state": "not_executed"}))
def test_20_unresolved_cannot_be_structurally_validated(): invalid(lambda p: p["subject_readiness"][3].update({"state": "structurally_checkable", "execution_state": "not_required"}))
def test_21_conditional_constraint_cannot_be_unconditional(): invalid(lambda p: p["subject_readiness"][1].update({"state": "structurally_checkable", "execution_state": "not_required"}))
def test_22_unsupported_constraint_cannot_be_ready():
    def mutate(p):
        p["input_scope"]["physical_constraint_references"][0]["status"] = "unsupported"; p["subject_readiness"][0].update({"state": "ready_for_execution", "execution_state": "not_executed"})
    invalid(mutate)
def test_23_indeterminate_constraint_cannot_be_ready():
    def mutate(p):
        p["input_scope"]["physical_constraint_references"][0]["status"] = "indeterminate"; p["subject_readiness"][0].update({"state": "structurally_checkable", "execution_state": "not_required"})
    invalid(mutate)
def test_24_unresolved_conflict_cannot_be_cleared(): invalid(lambda p: p["subject_readiness"][2].update({"state": "ready_for_execution", "execution_state": "not_executed"}))
def test_25_artist_acceptance_cannot_be_fabricated(): invalid(lambda p: p["subject_readiness"][4].update({"state": "ready_for_execution", "execution_state": "not_executed"}))
@pytest.mark.parametrize(("state", "execution"), [("structurally_checkable", "not_executed"), ("ready_for_execution", "not_required"), ("blocked", "not_executed"), ("cannot_validate_yet", "not_required")])
def test_26_execution_state_cannot_claim_execution(state, execution): invalid(lambda p: p["target_readiness"][0].update({"state": state, "execution_state": execution}))
def test_27_extra_fields_forbidden():
    p = payload(); p["executed_pass"] = True
    with pytest.raises(ValidationError): ValidationReadinessContract.model_validate(p)
def test_28_meaningful_list_order_is_preserved():
    p = payload(); p["input_scope"]["director_validation_target_ids"].reverse()
    assert ValidationReadinessContract.model_validate(p).input_scope.director_validation_target_ids == ["vt_disclosure", "vt_optics"]
def test_29_blank_scope_reference_rejected(): invalid(lambda p: p["input_scope"]["scene_validation_hook_references"][0].update({"scene_validation_hook_id": ""}))
def test_30_duplicate_scope_reference_rejected(): invalid(lambda p: p["input_scope"]["physical_constraint_references"].append(deepcopy(p["input_scope"]["physical_constraint_references"][0])))


def test_31_dependency_presence_does_not_fabricate_blocking():
    p = payload()
    p["input_scope"]["scene_dependency_references"].append(
        {"scene_dependency_id": "dep_optional", "validation_hook_ids": []}
    )
    p["dependency_coverage"].append(
        {"scene_dependency_id": "dep_optional", "validation_hook_ids": [], "prerequisites": ["External execution remains optional."], "limitations": []}
    )
    p["target_readiness"][0].update(
        {"state": "ready_for_execution", "execution_state": "not_executed", "dependency_ids": ["dep_optional"]}
    )
    assert ValidationReadinessContract.model_validate(p).target_readiness[0].state.value == "ready_for_execution"


@pytest.mark.parametrize("index", [2, 3])
def test_32_subject_hook_reassignment_to_conflict_or_unresolved_rejected(index):
    invalid(lambda p: p["subject_readiness"][index].update({"validation_hook_ids": ["hook_disclosure"]}))


def test_33_subject_target_must_be_bound_by_its_hook():
    invalid(lambda p: p["subject_readiness"][0].update({"director_validation_target_ids": ["vt_disclosure"]}))


def test_34_dependency_scope_hook_binding_cannot_be_invented():
    invalid(lambda p: p["input_scope"]["scene_dependency_references"][0].update({"validation_hook_ids": []}))