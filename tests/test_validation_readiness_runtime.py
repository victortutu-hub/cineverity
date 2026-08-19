"""Offline deterministic and adversarial tests for Validation Readiness runtime."""

import asyncio
from copy import deepcopy
import json
import re

import pytest
from pydantic import ValidationError

from src.contracts.scene_planning import ScenePlanningContract
from src.contracts.validation_readiness import ValidationReadinessContract
from src.services.scene_planning_runtime import derive_scene_planning_scope
from src.services.validation_readiness_runtime import (
    ValidationReadinessScopeValidationError,
    accept_validation_readiness_candidate,
    build_validation_readiness_packet,
    derive_validation_readiness_scope,
    extract_validation_readiness_text_from_adk_events,
    query_validation_readiness_once,
    render_validation_readiness_packet,
    synthesize_validation_readiness,
    validate_runtime_inputs,
)
from tests.test_scene_planning_runtime import director, director_payload, physical, physical_data
from tests.test_scene_planning_serialization import valid_payload as unrelated_scene_payload


def scene() -> ScenePlanningContract:
    """A scope-faithful in-memory scene fixture; runtime scope uses only hooks/dependencies."""
    supplied_director, supplied_physical = director(), physical()
    return ScenePlanningContract.model_construct(
        input_scope=derive_scene_planning_scope(supplied_director, supplied_physical),
        dependencies=[],
        validation_hooks=[],
    )


def candidate_data(director_value= None, physical_value=None, scene_value=None) -> dict:
    director_value = director_value or director()
    physical_value = physical_value or physical()
    scene_value = scene_value or scene()
    scope = derive_validation_readiness_scope(director_value, physical_value, scene_value)
    target = [
        {
            "director_validation_target_id": item,
            "state": "structurally_checkable",
            "execution_state": "not_required",
            "validation_hook_ids": [], "physical_constraint_ids": [], "physical_conflict_ids": [],
            "unresolved_physical_constraint_ids": [], "artistic_deviation_ids": [], "dependency_ids": [],
            "prerequisites": [], "limitations": [],
        }
        for item in scope.director_validation_target_ids
    ]
    subjects = []
    for item in scope.physical_constraint_references:
        state = "structurally_checkable" if item.status == "supported" else "blocked"
        subjects.append({"subject_kind": "physical_constraint", "subject_id": item.physical_constraint_id,
            "state": state, "execution_state": "not_required" if state == "structurally_checkable" else "unavailable",
            "director_validation_target_ids": [], "validation_hook_ids": [], "dependency_ids": [], "prerequisites": [], "limitations": []})
    for item in scope.physical_conflict_references:
        subjects.append({"subject_kind": "physical_conflict", "subject_id": item.physical_conflict_id,
            "state": "blocked", "execution_state": "unavailable", "director_validation_target_ids": [], "validation_hook_ids": [], "dependency_ids": [], "prerequisites": [], "limitations": []})
    for item in scope.unresolved_physical_constraint_references:
        subjects.append({"subject_kind": "unresolved_physical_constraint", "subject_id": item.unresolved_physical_constraint_id,
            "state": "cannot_validate_yet", "execution_state": "unavailable", "director_validation_target_ids": [], "validation_hook_ids": [], "dependency_ids": [], "prerequisites": [], "limitations": []})
    for item in scope.artistic_deviation_references:
        subjects.append({"subject_kind": "artistic_deviation", "subject_id": item.artistic_deviation_id,
            "state": "blocked", "execution_state": "unavailable", "director_validation_target_ids": [], "validation_hook_ids": [], "dependency_ids": [], "prerequisites": [], "limitations": []})
    hooks = [
        {
            "scene_validation_hook_id": item.scene_validation_hook_id,
            "state": "structurally_checkable", "execution_state": "not_required",
            "director_validation_target_ids": list(item.director_validation_target_ids),
            "physical_constraint_ids": list(item.physical_constraint_ids),
            "physical_conflict_ids": list(item.physical_conflict_ids),
            "unresolved_physical_constraint_ids": list(item.unresolved_physical_constraint_ids),
            "artistic_deviation_ids": list(item.artistic_deviation_ids),
            "dependency_ids": list(item.dependency_ids), "prerequisites": [], "limitations": [],
        }
        for item in scope.scene_validation_hook_references
    ]
    coverage = [
        {"scene_dependency_id": item.scene_dependency_id, "validation_hook_ids": list(item.validation_hook_ids), "prerequisites": [], "limitations": []}
        for item in scope.scene_dependency_references
    ]
    return {
        "contract_version": "0.1", "agent": "validation_readiness_agent",
        "input_scope": scope.model_dump(mode="json"), "target_readiness": target,
        "hook_readiness": hooks, "subject_readiness": subjects, "dependency_coverage": coverage,
        "required_execution_classes": ["contract_preflight"],
        "readiness_summary": "Preflight only λ μ Å 漢字; no execution occurred.",
        "limitations": ["No renderer, simulation, measurement, or scientific execution occurred."],
    }


def candidate() -> ValidationReadinessContract:
    return ValidationReadinessContract.model_validate(candidate_data())


class FakeApp:
    def __init__(self, events): self.events = events; self.calls = []
    async def async_stream_query(self, *, user_id, message):
        self.calls.append((user_id, message))
        for event in self.events: yield event


def test_1_scope_derives_all_runtime_owned_fingerprints_and_ordered_references():
    scope = derive_validation_readiness_scope(director(), physical(), scene())
    assert all(re.fullmatch(r"[0-9a-f]{64}", value) for value in (
        scope.director_contract_sha256, scope.physical_constraints_contract_sha256, scope.scene_planning_contract_sha256))
    assert scope.director_scene_entity_ids == ["crystal_1", "surface_1"]
    assert [item.physical_constraint_id for item in scope.physical_constraint_references] == ["constraint_optics", "constraint_caustics"]
    assert [item.physical_conflict_id for item in scope.physical_conflict_references] == ["physical_conflict_1"]
    assert [item.unresolved_physical_constraint_id for item in scope.unresolved_physical_constraint_references] == ["unresolved_magnitude"]
    assert [item.artistic_deviation_id for item in scope.artistic_deviation_references] == ["deviation_rainbow"]


def test_2_scope_and_fingerprints_are_deterministic_unicode_safe_and_immutable():
    supplied_director, supplied_physical, supplied_scene = director(), physical(), scene()
    before = (deepcopy(supplied_director.model_dump(mode="json")), deepcopy(supplied_physical.model_dump(mode="json")))
    assert derive_validation_readiness_scope(supplied_director, supplied_physical, supplied_scene) == derive_validation_readiness_scope(supplied_director, supplied_physical, supplied_scene)
    packet = build_validation_readiness_packet(supplied_director, supplied_physical, supplied_scene)
    rendered = render_validation_readiness_packet(packet)
    assert "λ μ Å 漢字" in rendered and "\\u03bb" not in rendered
    assert before == (supplied_director.model_dump(mode="json"), supplied_physical.model_dump(mode="json"))


def test_3_packet_has_exact_trust_separation_and_no_raw_inputs():
    packet = build_validation_readiness_packet(director(), physical(), scene())
    assert set(packet) == {"authoritative_runtime", "validated_context"}
    assert set(packet["validated_context"]) == {"director", "physical_constraints", "scene_planning"}
    assert packet["authoritative_runtime"]["expected_input_scope"] == derive_validation_readiness_scope(director(), physical(), scene()).model_dump(mode="json")
    assert "research_context" not in packet and "raw_json" not in packet


@pytest.mark.parametrize("raw_director,raw_physical,raw_scene", [
    ("{}", physical().model_dump_json(), unrelated_scene_payload()),
    (director().model_dump_json(), "{}", unrelated_scene_payload()),
    (director().model_dump_json(), physical().model_dump_json(), "{}"),
])
def test_4_invalid_json_inputs_are_rejected_before_model(raw_director, raw_physical, raw_scene):
    with pytest.raises(ValidationError): validate_runtime_inputs(raw_director, raw_physical, json.dumps(raw_scene) if isinstance(raw_scene, dict) else raw_scene)


def test_5_direct_synthesis_rejects_invalid_director_before_app_call():
    app = FakeApp([])
    with pytest.raises(Exception): asyncio.run(synthesize_validation_readiness(app, director().model_construct(), physical(), scene()))
    assert app.calls == []


def other_director_and_physical():
    other = director_payload(); other["physical_questions"][0]["id"] = "pq_other"
    other_director = type(director()).model_validate(other)
    other_physical = physical_data(); other_physical["input_scope"]["director_physical_question_ids"] = ["pq_other", "pq_caustic"]
    other_physical["constraints"][0]["director_physical_question_ids"] = ["pq_other"]
    other_physical["artistic_deviations"][0]["director_physical_question_ids"] = ["pq_other"]
    other_physical["coverage"][0]["director_physical_question_id"] = "pq_other"
    return other_director, type(physical()).model_validate(other_physical)


def test_6_other_valid_physical_pair_is_rejected_before_app_call():
    _, other_physical = other_director_and_physical(); app = FakeApp([])
    with pytest.raises(ValueError): asyncio.run(synthesize_validation_readiness(app, director(), other_physical, scene()))
    assert app.calls == []


def test_7_other_valid_scene_snapshot_is_rejected_before_app_call():
    app = FakeApp([])
    unrelated = ScenePlanningContract.model_validate(unrelated_scene_payload())
    with pytest.raises(ValueError): asyncio.run(synthesize_validation_readiness(app, director(), physical(), unrelated))
    assert app.calls == []


def test_8_changed_scene_fingerprint_is_rejected_before_app_call():
    bad_scene = scene().model_copy(deep=True); bad_scene.input_scope.director_contract_sha256 = "0" * 64
    app = FakeApp([])
    with pytest.raises(ValueError): asyncio.run(synthesize_validation_readiness(app, director(), physical(), bad_scene))
    assert app.calls == []


def test_9_candidate_acceptance_requires_pydantic_then_exact_scope():
    accepted = accept_validation_readiness_candidate(json.dumps(candidate_data()), director(), physical(), scene())
    assert accepted == candidate()
    with pytest.raises(ValidationError): accept_validation_readiness_candidate("{not-json", director(), physical(), scene())


@pytest.mark.parametrize("field, value", [
    ("director_contract_sha256", None), ("director_contract_sha256", "0" * 64),
    ("physical_constraints_contract_sha256", "1" * 64), ("scene_planning_contract_sha256", "2" * 64),
    ("director_contract_sha256", "A" * 64), ("director_contract_sha256", "malformed"),
])
def test_10_fingerprint_attacks_fail_validation_or_runtime_fidelity(field, value):
    data = candidate_data()
    if value is None: data["input_scope"].pop(field)
    else: data["input_scope"][field] = value
    with pytest.raises((ValidationError, ValidationReadinessScopeValidationError)):
        accept_validation_readiness_candidate(json.dumps(data), director(), physical(), scene())


@pytest.mark.parametrize("mutate", [
    lambda s: s["director_scene_entity_ids"].reverse(),
    lambda s: s["physical_constraint_references"].reverse(),
    lambda s: s["physical_constraint_references"][0].update({"status": "unsupported"}),
    lambda s: s["physical_conflict_references"][0].update({"resolution_status": "unresolved"}),
    lambda s: s["artistic_deviation_references"][0].update({"requires_explicit_artist_acceptance": False}),
    lambda s: s["physical_constraint_references"].pop(),
    lambda s: s["director_physical_question_ids"].append("extra"),
])
def test_11_correct_ids_but_changed_order_status_or_scope_fail(mutate):
    data = candidate_data(); mutate(data["input_scope"])
    with pytest.raises((ValidationError, ValidationReadinessScopeValidationError)):
        accept_validation_readiness_candidate(json.dumps(data), director(), physical(), scene())


@pytest.mark.parametrize("mutate", [
    lambda p: p["subject_readiness"][1].update({"state": "structurally_checkable", "execution_state": "not_required"}),
    lambda p: p["subject_readiness"][2].update({"state": "ready_for_execution", "execution_state": "not_executed"}),
    lambda p: p["subject_readiness"][3].update({"state": "ready_for_execution", "execution_state": "not_executed"}),
    lambda p: p["subject_readiness"][4].update({"state": "ready_for_execution", "execution_state": "not_executed"}),
])
def test_12_frozen_non_escalation_validators_rerun_before_scope_gate(mutate):
    data = candidate_data(); mutate(data)
    with pytest.raises(ValidationError): accept_validation_readiness_candidate(json.dumps(data), director(), physical(), scene())


@pytest.mark.parametrize("events, expected", [
    ([{"content": {"parts": [{"thought": True, "text": "ignore"}, {"text": "{"}, {"text": "}"}]}}], "{}"),
    ([{"content": {"parts": [{"text": "λ"}]}}, {"content": {"parts": [{"text": " μ Å 漢字"}]}}], "λ μ Å 漢字"),
])
def test_13_event_extraction_ignores_thoughts_and_preserves_stream_order(events, expected):
    assert extract_validation_readiness_text_from_adk_events(events) == expected


@pytest.mark.parametrize("events", [[], [{"content": {"parts": [{"thought": True, "text": "hidden"}]}}], [{"metadata": {"text": "not contract"}}]])
def test_14_event_extraction_rejects_empty_thought_only_or_metadata_only(events):
    with pytest.raises(ValueError): extract_validation_readiness_text_from_adk_events(events)


def test_15_query_uses_one_call_exact_packet_and_no_retry():
    app = FakeApp([{"content": {"parts": [{"text": "{not-json"}]}}])
    assert asyncio.run(query_validation_readiness_once(app, director(), physical(), scene())) == "{not-json"
    assert len(app.calls) == 1
    assert app.calls[0] == ("cineverity-local-validation-readiness", render_validation_readiness_packet(build_validation_readiness_packet(director(), physical(), scene())))


def test_16_wrong_candidate_snapshot_fails_after_exactly_one_call_without_retry():
    wrong = candidate_data(); wrong["input_scope"]["director_contract_sha256"] = "f" * 64
    app = FakeApp([{"content": {"parts": [{"text": json.dumps(wrong)}]}}])
    with pytest.raises(ValidationReadinessScopeValidationError):
        asyncio.run(synthesize_validation_readiness(app, director(), physical(), scene()))
    assert len(app.calls) == 1


def test_17_runtime_has_one_query_call_site_and_no_runner_or_repair_path():
    source = open("src/services/validation_readiness_runtime.py", encoding="utf-8").read()
    assert source.count("async_stream_query(") == 1
    assert "scripts.run_validation_readiness_agent" not in source
    assert "retry" not in source and "repair" not in source


def scene_for(director_value, physical_value) -> ScenePlanningContract:
    return ScenePlanningContract.model_construct(
        input_scope=derive_scene_planning_scope(director_value, physical_value),
        dependencies=[],
        validation_hooks=[],
    )


def bound_scene_for(director_value, physical_value) -> ScenePlanningContract:
    hooks = [
        ("hook_target_a", "director_target_check", ["vt_optics"], [], [], [], [], []),
        ("hook_target_b", "director_target_check", ["vt_second"], [], [], [], [], []),
        ("hook_constraint_a", "physical_constraint_check", [], ["constraint_optics"], [], [], [], []),
        ("hook_constraint_b", "physical_constraint_check", [], ["constraint_caustics"], [], [], [], []),
        ("hook_conflict", "physical_conflict_check", [], [], ["physical_conflict_1"], [], [], []),
        ("hook_unresolved", "unresolved_dependency_check", [], [], [], ["unresolved_magnitude"], [], ["dep_unresolved"]),
        ("hook_artist", "artistic_deviation_disclosure_check", [], [], [], [], ["deviation_rainbow"], ["dep_artist"]),
    ]
    return ScenePlanningContract.model_construct(
        input_scope=derive_scene_planning_scope(director_value, physical_value),
        dependencies=[type("Dependency", (), {"id": "dep_unresolved"})(), type("Dependency", (), {"id": "dep_artist"})()],
        validation_hooks=[
            type("Hook", (), {
                "id": hook_id, "kind": kind, "director_validation_target_ids": targets,
                "physical_constraint_ids": constraints, "physical_conflict_ids": conflicts,
                "unresolved_physical_constraint_ids": unresolved, "artistic_deviation_ids": deviations,
                "dependency_ids": dependencies,
            })()
            for hook_id, kind, targets, constraints, conflicts, unresolved, deviations, dependencies in hooks
        ],
    )


def director_and_physical_with_two_targets():
    value = director_payload()
    value["validation_targets"].append({"id": "vt_second", "target": "second", "domain": "optics"})
    director_value = type(director()).model_validate(value)
    physical_value = physical_data()
    physical_value["input_scope"]["director_validation_target_ids"].append("vt_second")
    return director_value, type(physical()).model_validate(physical_value)


def post_model_rejection(data, director_value, physical_value, scene_value):
    app = FakeApp([{"content": {"parts": [{"text": json.dumps(data)}]}}])
    with pytest.raises((ValidationError, ValidationReadinessScopeValidationError)):
        asyncio.run(synthesize_validation_readiness(app, director_value, physical_value, scene_value))
    assert len(app.calls) == 1


def test_18_invalid_physical_direct_synthesis_fails_before_transport():
    app = FakeApp([])
    invalid_physical = type(physical()).model_construct()
    with pytest.raises(Exception):
        asyncio.run(synthesize_validation_readiness(app, director(), invalid_physical, scene()))
    assert app.calls == []


def test_19_invalid_scene_direct_synthesis_fails_before_transport():
    app = FakeApp([])
    invalid_scene = ScenePlanningContract.model_construct()
    with pytest.raises(Exception):
        asyncio.run(synthesize_validation_readiness(app, director(), physical(), invalid_scene))
    assert app.calls == []


def test_20_scene_from_another_director_fails_before_transport():
    other_director, other_physical = other_director_and_physical()
    app = FakeApp([])
    with pytest.raises(ValueError):
        asyncio.run(synthesize_validation_readiness(app, director(), physical(), scene_for(other_director, other_physical)))
    assert app.calls == []


def test_21_scene_from_another_physical_snapshot_fails_before_transport():
    altered = physical_data(); altered["physical_summary"] = "A different, individually valid Physical snapshot."
    other_physical = type(physical()).model_validate(altered)
    app = FakeApp([])
    with pytest.raises(ValueError):
        asyncio.run(synthesize_validation_readiness(app, director(), physical(), scene_for(director(), other_physical)))
    assert app.calls == []


@pytest.mark.parametrize("binding", ["physical", "target", "dependency", "conflict", "unresolved", "deviation"])
def test_22_real_binding_reassignment_fails_after_one_model_call(binding):
    director_value, physical_value = director_and_physical_with_two_targets()
    scene_value = bound_scene_for(director_value, physical_value)
    data = candidate_data(director_value, physical_value, scene_value)
    scope = data["input_scope"]
    hooks = {item["scene_validation_hook_id"]: item for item in scope["scene_validation_hook_references"]}
    readiness = {item["scene_validation_hook_id"]: item for item in data["hook_readiness"]}
    dependencies = {item["scene_dependency_id"]: item for item in scope["scene_dependency_references"]}
    coverage = {item["scene_dependency_id"]: item for item in data["dependency_coverage"]}
    if binding == "physical":
        hooks["hook_constraint_a"]["physical_constraint_ids"], hooks["hook_constraint_b"]["physical_constraint_ids"] = hooks["hook_constraint_b"]["physical_constraint_ids"], hooks["hook_constraint_a"]["physical_constraint_ids"]
        readiness["hook_constraint_a"]["physical_constraint_ids"], readiness["hook_constraint_b"]["physical_constraint_ids"] = readiness["hook_constraint_b"]["physical_constraint_ids"], readiness["hook_constraint_a"]["physical_constraint_ids"]
    elif binding == "target":
        hooks["hook_target_a"]["director_validation_target_ids"], hooks["hook_target_b"]["director_validation_target_ids"] = hooks["hook_target_b"]["director_validation_target_ids"], hooks["hook_target_a"]["director_validation_target_ids"]
        readiness["hook_target_a"]["director_validation_target_ids"], readiness["hook_target_b"]["director_validation_target_ids"] = readiness["hook_target_b"]["director_validation_target_ids"], readiness["hook_target_a"]["director_validation_target_ids"]
    elif binding == "dependency":
        hooks["hook_unresolved"]["dependency_ids"], hooks["hook_artist"]["dependency_ids"] = hooks["hook_artist"]["dependency_ids"], hooks["hook_unresolved"]["dependency_ids"]
        readiness["hook_unresolved"]["dependency_ids"], readiness["hook_artist"]["dependency_ids"] = readiness["hook_artist"]["dependency_ids"], readiness["hook_unresolved"]["dependency_ids"]
        dependencies["dep_unresolved"]["validation_hook_ids"], dependencies["dep_artist"]["validation_hook_ids"] = dependencies["dep_artist"]["validation_hook_ids"], dependencies["dep_unresolved"]["validation_hook_ids"]
        coverage["dep_unresolved"]["validation_hook_ids"], coverage["dep_artist"]["validation_hook_ids"] = coverage["dep_artist"]["validation_hook_ids"], coverage["dep_unresolved"]["validation_hook_ids"]
    else:
        field, subject_hook, wrong_hook = {
            "conflict": ("physical_conflict_ids", "hook_conflict", "hook_target_a"),
            "unresolved": ("unresolved_physical_constraint_ids", "hook_unresolved", "hook_target_a"),
            "deviation": ("artistic_deviation_ids", "hook_artist", "hook_target_a"),
        }[binding]
        hooks[wrong_hook][field] = hooks[subject_hook][field]
        hooks[subject_hook][field] = []
        readiness[wrong_hook][field] = readiness[subject_hook][field]
        readiness[subject_hook][field] = []
    post_model_rejection(data, director_value, physical_value, scene_value)


@pytest.mark.parametrize("status", ["unsupported", "indeterminate"])
def test_23_unsupported_and_indeterminate_cannot_escalate_after_model_json(status):
    physical_payload = physical_data(); physical_payload["constraints"][0]["status"] = status
    physical_value = type(physical()).model_validate(physical_payload)
    scene_value = scene_for(director(), physical_value)
    data = candidate_data(director(), physical_value, scene_value)
    data["subject_readiness"][0].update({"state": "ready_for_execution", "execution_state": "not_executed"})
    post_model_rejection(data, director(), physical_value, scene_value)