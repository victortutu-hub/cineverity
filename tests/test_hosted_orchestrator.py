"""Offline orchestration tests using only injected fakes and existing runtime gates."""

import asyncio
import inspect
import threading
from types import SimpleNamespace

import pytest

import src.backend.orchestrator as orchestrator
from src.backend.orchestrator import HostedRuntimeDependencies, HostedStageError, run_hosted_pipeline
from src.services.scene_planning_runtime import DirectorPhysicalScopeValidationError
from tests.test_scene_planning_runtime import director as valid_director
from tests.test_scene_planning_runtime import physical as valid_physical
from tests.test_physical_constraints_runtime import research as valid_research


def dependencies():
    return HostedRuntimeDependencies(
        director_app=SimpleNamespace(), research_app=SimpleNamespace(),
        physical_constraints_app=SimpleNamespace(), scene_planning_app=SimpleNamespace(),
        validation_readiness_app=SimpleNamespace(), parallel_adapter=SimpleNamespace(),
    )


def install_successful_pipeline(monkeypatch, log):
    accepted = {name: object() for name in ("director", "research", "physical", "scene", "validation")}
    main_thread = threading.get_ident()

    async def director(app, brief):
        log.append("director"); return accepted["director"]
    def plans(value):
        assert value is accepted["director"]; log.append("plans"); return ["plan"]
    def retrieval(value, adapter):
        assert value == ["plan"]; assert threading.get_ident() != main_thread
        log.append("parallel"); return accepted["director"]
    async def research(app, director_value, registry):
        assert director_value is accepted["director"] and registry is accepted["director"]
        log.append("research"); return accepted["research"]
    async def physical(app, director_value, research_value):
        assert director_value is accepted["director"] and research_value is accepted["research"]
        log.append("physical"); return accepted["physical"]
    async def scene(app, director_value, physical_value):
        assert director_value is accepted["director"] and physical_value is accepted["physical"]
        log.append("scene"); return accepted["scene"]
    async def validation(app, director_value, physical_value, scene_value):
        assert director_value is accepted["director"] and physical_value is accepted["physical"] and scene_value is accepted["scene"]
        log.append("validation"); return accepted["validation"]

    monkeypatch.setattr(orchestrator, "synthesize_director", director)
    monkeypatch.setattr(orchestrator, "build_search_plans", plans)
    monkeypatch.setattr(orchestrator, "execute_search_plans", retrieval)
    monkeypatch.setattr(orchestrator, "synthesize_with_app", research)
    monkeypatch.setattr(orchestrator, "synthesize_physical_constraints", physical)
    monkeypatch.setattr(orchestrator, "synthesize_scene_planning", scene)
    monkeypatch.setattr(orchestrator, "synthesize_validation_readiness", validation)
    return accepted


def test_successful_pipeline_has_exact_order_identity_and_threaded_parallel(monkeypatch):
    log = []; accepted = install_successful_pipeline(monkeypatch, log)
    result = asyncio.run(run_hosted_pipeline("brief", dependencies()))
    assert log == ["director", "plans", "parallel", "research", "physical", "scene", "validation"]
    assert result.director is accepted["director"]
    assert result.research is accepted["research"]
    assert result.physical_constraints is accepted["physical"]
    assert result.scene_planning is accepted["scene"]
    assert result.validation_readiness is accepted["validation"]


def test_orchestrator_has_no_concrete_agent_imports():
    source = inspect.getsource(orchestrator)
    assert "src.agents." not in source


@pytest.mark.parametrize(
    ("failing_stage", "expected_log", "expected_error_stage"),
    [
        ("director", [], "director"),
        ("parallel", ["director", "plans"], "parallel_retrieval"),
        ("research", ["director", "plans", "parallel"], "research"),
        ("physical", ["director", "plans", "parallel", "research"], "physical_constraints"),
        ("scene", ["director", "plans", "parallel", "research", "physical"], "scene_planning"),
        ("validation", ["director", "plans", "parallel", "research", "physical", "scene"], "validation_readiness"),
    ],
)
def test_first_failure_stops_downstream_without_retry(monkeypatch, failing_stage, expected_log, expected_error_stage):
    log = []; install_successful_pipeline(monkeypatch, log)
    original = {
        "director": orchestrator.synthesize_director,
        "parallel": orchestrator.execute_search_plans,
        "research": orchestrator.synthesize_with_app,
        "physical": orchestrator.synthesize_physical_constraints,
        "scene": orchestrator.synthesize_scene_planning,
        "validation": orchestrator.synthesize_validation_readiness,
    }[failing_stage]

    if failing_stage == "parallel":
        def fail(*args, **kwargs):
            raise RuntimeError("offline failure")
    else:
        async def fail(*args, **kwargs):
            raise RuntimeError("offline failure")
    monkeypatch.setattr(orchestrator, {
        "director": "synthesize_director", "parallel": "execute_search_plans", "research": "synthesize_with_app",
        "physical": "synthesize_physical_constraints", "scene": "synthesize_scene_planning",
        "validation": "synthesize_validation_readiness",
    }[failing_stage], fail)

    with pytest.raises(HostedStageError) as error:
        asyncio.run(run_hosted_pipeline("brief", dependencies()))
    assert error.value.stage == expected_error_stage
    assert log == expected_log
    assert original is not None


def test_real_scene_fidelity_gate_rejects_wrong_director_physical_pair_before_model(monkeypatch):
    director = valid_director()
    physical = valid_physical().model_copy(deep=True)
    changed = physical.model_dump(mode="json")
    changed["input_scope"]["director_physical_question_ids"] = ["wrong_question", "pq_caustic"]
    changed["constraints"][0]["director_physical_question_ids"] = ["wrong_question"]
    changed["artistic_deviations"][0]["director_physical_question_ids"] = ["wrong_question"]
    changed["coverage"][0]["director_physical_question_id"] = "wrong_question"
    from src.contracts.physical_constraints import PhysicalConstraintsContract
    wrong_physical = PhysicalConstraintsContract.model_validate(changed)
    class FakeSceneApp:
        def __init__(self):
            self.calls = 0

        async def async_stream_query(self, **kwargs):
            self.calls += 1
            raise AssertionError("Scene app must not run after fidelity rejection")
            yield  # pragma: no cover

    scene_app = FakeSceneApp()

    async def director_stage(app, brief): return director
    def plans(value): return []
    def retrieval(plans_value, adapter): return object()
    async def research_stage(app, director_value, registry): return object()
    async def physical_stage(app, director_value, research_value): return wrong_physical
    monkeypatch.setattr(orchestrator, "synthesize_director", director_stage)
    monkeypatch.setattr(orchestrator, "build_search_plans", plans)
    monkeypatch.setattr(orchestrator, "execute_search_plans", retrieval)
    monkeypatch.setattr(orchestrator, "synthesize_with_app", research_stage)
    monkeypatch.setattr(orchestrator, "synthesize_physical_constraints", physical_stage)

    with pytest.raises(HostedStageError) as error:
        asyncio.run(run_hosted_pipeline("brief", dependencies().__class__(
            dependencies().director_app, dependencies().research_app, dependencies().physical_constraints_app,
            scene_app, dependencies().validation_readiness_app, dependencies().parallel_adapter,
        )))
    assert error.value.stage == "scene_planning"
    assert isinstance(error.value.__cause__, DirectorPhysicalScopeValidationError)
    assert scene_app.calls == 0


def test_accepted_pydantic_director_and_research_objects_cross_boundaries_unchanged(monkeypatch):
    director = valid_director()
    research = valid_research()
    physical = valid_physical()
    scene = object()
    validation = object()

    async def director_stage(app, brief): return director
    def plans(received_director):
        assert received_director is director
        return ["plan"]
    def retrieval(plans_value, adapter):
        assert plans_value == ["plan"]
        return object()
    async def research_stage(app, received_director, registry):
        assert received_director is director
        return research
    async def physical_stage(app, received_director, received_research):
        assert received_director is director
        assert received_research is research
        return physical
    async def scene_stage(app, received_director, received_physical):
        assert received_director is director
        assert received_physical is physical
        return scene
    async def validation_stage(app, received_director, received_physical, received_scene):
        assert received_director is director
        assert received_physical is physical
        assert received_scene is scene
        return validation

    monkeypatch.setattr(orchestrator, "synthesize_director", director_stage)
    monkeypatch.setattr(orchestrator, "build_search_plans", plans)
    monkeypatch.setattr(orchestrator, "execute_search_plans", retrieval)
    monkeypatch.setattr(orchestrator, "synthesize_with_app", research_stage)
    monkeypatch.setattr(orchestrator, "synthesize_physical_constraints", physical_stage)
    monkeypatch.setattr(orchestrator, "synthesize_scene_planning", scene_stage)
    monkeypatch.setattr(orchestrator, "synthesize_validation_readiness", validation_stage)

    result = asyncio.run(run_hosted_pipeline("brief", dependencies()))
    assert result.director is director
    assert result.research is research
    assert result.physical_constraints is physical


def test_research_planning_failure_stops_before_parallel_and_preserves_cause(monkeypatch):
    calls = {name: 0 for name in ("parallel", "research", "physical", "scene", "validation")}
    original_error = RuntimeError("planning failure")

    async def director_stage(app, brief): return object()
    def planning_stage(director): raise original_error
    def retrieval(*args): calls["parallel"] += 1
    async def research_stage(*args): calls["research"] += 1
    async def physical_stage(*args): calls["physical"] += 1
    async def scene_stage(*args): calls["scene"] += 1
    async def validation_stage(*args): calls["validation"] += 1

    monkeypatch.setattr(orchestrator, "synthesize_director", director_stage)
    monkeypatch.setattr(orchestrator, "build_search_plans", planning_stage)
    monkeypatch.setattr(orchestrator, "execute_search_plans", retrieval)
    monkeypatch.setattr(orchestrator, "synthesize_with_app", research_stage)
    monkeypatch.setattr(orchestrator, "synthesize_physical_constraints", physical_stage)
    monkeypatch.setattr(orchestrator, "synthesize_scene_planning", scene_stage)
    monkeypatch.setattr(orchestrator, "synthesize_validation_readiness", validation_stage)

    with pytest.raises(HostedStageError) as error:
        asyncio.run(run_hosted_pipeline("brief", dependencies()))
    assert error.value.stage == "research_planning"
    assert error.value.__cause__ is original_error
    assert calls == {name: 0 for name in calls}


def test_parallel_failure_is_distinct_after_successful_planning(monkeypatch):
    calls = {name: 0 for name in ("planning", "parallel", "research", "physical", "scene", "validation")}
    original_error = RuntimeError("parallel failure")

    async def director_stage(app, brief): return object()
    def planning_stage(director): calls["planning"] += 1; return ["plan"]
    def retrieval(*args): calls["parallel"] += 1; raise original_error
    async def research_stage(*args): calls["research"] += 1
    async def physical_stage(*args): calls["physical"] += 1
    async def scene_stage(*args): calls["scene"] += 1
    async def validation_stage(*args): calls["validation"] += 1

    monkeypatch.setattr(orchestrator, "synthesize_director", director_stage)
    monkeypatch.setattr(orchestrator, "build_search_plans", planning_stage)
    monkeypatch.setattr(orchestrator, "execute_search_plans", retrieval)
    monkeypatch.setattr(orchestrator, "synthesize_with_app", research_stage)
    monkeypatch.setattr(orchestrator, "synthesize_physical_constraints", physical_stage)
    monkeypatch.setattr(orchestrator, "synthesize_scene_planning", scene_stage)
    monkeypatch.setattr(orchestrator, "synthesize_validation_readiness", validation_stage)

    with pytest.raises(HostedStageError) as error:
        asyncio.run(run_hosted_pipeline("brief", dependencies()))
    assert error.value.stage == "parallel_retrieval"
    assert error.value.__cause__ is original_error
    assert calls == {"planning": 1, "parallel": 1, "research": 0, "physical": 0, "scene": 0, "validation": 0}

def test_observer_reports_real_stage_order_and_only_specialists_receive_artifacts(monkeypatch):
    log = []
    accepted = install_successful_pipeline(monkeypatch, log)
    observed = []

    async def observer(stage, status, artifact):
        observed.append((stage, status, artifact))

    result = asyncio.run(run_hosted_pipeline("brief", dependencies(), observer))
    assert result.director is accepted["director"]
    assert [(stage, status) for stage, status, _ in observed] == [
        ("director", "running"), ("director", "accepted"),
        ("research_planning", "running"), ("research_planning", "accepted"),
        ("parallel_retrieval", "running"), ("parallel_retrieval", "accepted"),
        ("research", "running"), ("research", "accepted"),
        ("physical_constraints", "running"), ("physical_constraints", "accepted"),
        ("scene_planning", "running"), ("scene_planning", "accepted"),
        ("validation_readiness", "running"), ("validation_readiness", "accepted"),
    ]
    artifacts = {stage: artifact for stage, status, artifact in observed if status == "accepted"}
    assert artifacts["director"] is accepted["director"]
    assert artifacts["research"] is accepted["research"]
    assert artifacts["physical_constraints"] is accepted["physical"]
    assert artifacts["scene_planning"] is accepted["scene"]
    assert artifacts["validation_readiness"] is accepted["validation"]
    assert artifacts["research_planning"] is None
    assert artifacts["parallel_retrieval"] is None


def test_observer_failure_isolated_from_pipeline_acceptance_without_retry(monkeypatch):
    log = []
    accepted = install_successful_pipeline(monkeypatch, log)

    def broken_observer(stage, status, artifact):
        raise RuntimeError("transport observer failure")

    result = asyncio.run(run_hosted_pipeline("brief", dependencies(), broken_observer))
    assert result.validation_readiness is accepted["validation"]
    assert log == ["director", "plans", "parallel", "research", "physical", "scene", "validation"]

def test_parallel_thread_drains_before_repeated_pipeline_cancellation_completes(monkeypatch):
    started = threading.Event()
    release = threading.Event()
    calls = {name: 0 for name in ("parallel", "research", "physical", "scene", "validation")}

    async def director_stage(app, brief):
        return object()

    def planning_stage(director):
        return ["plan"]

    def retrieval(plans, adapter):
        calls["parallel"] += 1
        started.set()
        assert release.wait(timeout=5)
        return object()

    async def research_stage(*args):
        calls["research"] += 1

    async def physical_stage(*args):
        calls["physical"] += 1

    async def scene_stage(*args):
        calls["scene"] += 1

    async def validation_stage(*args):
        calls["validation"] += 1

    monkeypatch.setattr(orchestrator, "synthesize_director", director_stage)
    monkeypatch.setattr(orchestrator, "build_search_plans", planning_stage)
    monkeypatch.setattr(orchestrator, "execute_search_plans", retrieval)
    monkeypatch.setattr(orchestrator, "synthesize_with_app", research_stage)
    monkeypatch.setattr(orchestrator, "synthesize_physical_constraints", physical_stage)
    monkeypatch.setattr(orchestrator, "synthesize_scene_planning", scene_stage)
    monkeypatch.setattr(orchestrator, "synthesize_validation_readiness", validation_stage)

    async def exercise():
        pipeline_task = asyncio.create_task(run_hosted_pipeline("brief", dependencies()))
        await asyncio.to_thread(started.wait)
        pipeline_task.cancel()
        await asyncio.sleep(0)
        assert not pipeline_task.done()
        pipeline_task.cancel()
        await asyncio.sleep(0)
        assert not pipeline_task.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await pipeline_task

    asyncio.run(exercise())
    assert calls == {"parallel": 1, "research": 0, "physical": 0, "scene": 0, "validation": 0}
