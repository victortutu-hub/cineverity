"""Offline tests for the FastAPI NDJSON transport foundation."""

import asyncio
import json
import threading
from types import SimpleNamespace

import pytest

from fastapi.testclient import TestClient
from starlette.requests import Request

from src.backend.app import ProcessRunGate, RunRequest, _run_with_owned_gate, create_app
from src.backend.bootstrap import HostedRuntimeBootstrapError
from src.backend.orchestrator import HostedRuntimeDependencies, HostedStageError
import src.backend.app as app_module
import src.backend.orchestrator as orchestrator


class FakeProvider:
    def __init__(self):
        self.calls = 0
        self.dependencies = HostedRuntimeDependencies(*(object() for _ in range(6)))

    async def get(self):
        self.calls += 1
        return self.dependencies


class Artifact:
    def __init__(self, value):
        self.value = value

    def model_dump(self, *, mode):
        assert mode == "json"
        return {"value": self.value}


SPECIALIST_STAGES = {
    "director", "research", "physical_constraints", "scene_planning", "validation_readiness"
}
ALL_STAGES = (
    "director", "research_planning", "parallel_retrieval", "research",
    "physical_constraints", "scene_planning", "validation_readiness",
)


def successful_pipeline(captured):
    async def pipeline(brief, dependencies, observer):
        captured.append(brief)
        for stage in ALL_STAGES:
            await observer(stage, "running", None)
            await observer(stage, "accepted", Artifact("λ 漢字") if stage in SPECIALIST_STAGES else None)
        return object()
    return pipeline


def stream_events(response):
    assert response.headers["content-type"].startswith("application/x-ndjson")
    lines = [line for line in response.content.decode("utf-8").splitlines() if line]
    return [json.loads(line) for line in lines]


def test_healthz_is_offline_and_provider_is_not_initialized():
    provider = FakeProvider()
    client = TestClient(create_app(runtime_provider=provider))
    assert client.get("/healthz").json() == {"status": "ok"}
    assert provider.calls == 0


def test_valid_run_stream_has_exact_event_order_constant_run_id_and_safe_artifacts():
    captured = []
    client = TestClient(create_app(runtime_provider=FakeProvider(), pipeline_callable=successful_pipeline(captured)))
    response = client.post("/api/runs", json={"brief": "  λ cinematic brief  "})
    events = stream_events(response)
    assert captured == ["  λ cinematic brief  "]
    assert [event["type"] for event in events] == [
        "run_started",
        "stage_started", "stage_accepted",
        "stage_started", "stage_accepted",
        "stage_started", "stage_accepted",
        "stage_started", "stage_accepted",
        "stage_started", "stage_accepted",
        "stage_started", "stage_accepted",
        "stage_started", "stage_accepted",
        "run_completed",
    ]
    assert {event["run_id"] for event in events}.__len__() == 1
    accepted = [event for event in events if event["type"] == "stage_accepted"]
    assert [event["stage"] for event in accepted] == list(ALL_STAGES)
    assert all("artifact" not in event for event in accepted if event["stage"] in {"research_planning", "parallel_retrieval"})
    assert accepted[0]["artifact"] == {"value": "λ 漢字"}


def test_invalid_requests_fail_before_provider_or_pipeline():
    provider = FakeProvider()
    client = TestClient(create_app(runtime_provider=provider, pipeline_callable=successful_pipeline([])))
    assert client.post("/api/runs", json={"brief": "   "}).status_code == 422
    assert client.post("/api/runs", json={"brief": "x" * 6001}).status_code == 422
    assert client.post("/api/runs", json={"brief": "ok", "extra": True}).status_code == 422
    assert provider.calls == 0


def test_controlled_bootstrap_failure_is_sanitized_before_stream():
    captured = []

    class BrokenProvider:
        async def get(self):
            raise HostedRuntimeBootstrapError("PARALLEL_API_KEY=secret-value")

    response = TestClient(
        create_app(runtime_provider=BrokenProvider(), pipeline_callable=successful_pipeline(captured))
    ).post("/api/runs", json={"brief": "ok"})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "configuration_unavailable"
    assert "secret-value" not in response.text
    assert captured == []


def test_unexpected_provider_failure_is_sanitized_as_internal_error_before_stream():
    captured = []

    class BrokenProvider:
        async def get(self):
            raise RuntimeError("token=should-not-leak")

    response = TestClient(
        create_app(runtime_provider=BrokenProvider(), pipeline_callable=successful_pipeline(captured))
    ).post("/api/runs", json={"brief": "ok"})
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "internal_error"
    assert "should-not-leak" not in response.text
    assert captured == []


def test_hosted_stage_failure_streams_sanitized_terminal_events_without_completion():
    async def failing_pipeline(brief, dependencies, observer):
        await observer("director", "running", None)
        raise HostedStageError("research")
    response = TestClient(create_app(runtime_provider=FakeProvider(), pipeline_callable=failing_pipeline)).post("/api/runs", json={"brief": "ok"})
    events = stream_events(response)
    assert [event["type"] for event in events] == ["run_started", "stage_started", "stage_failed", "run_failed"]
    assert events[-1]["error"]["code"] == "stage_failed"
    assert "Hosted pipeline failed" not in response.text
    assert "run_completed" not in response.text


def test_unexpected_pipeline_failure_is_sanitized():
    async def failing_pipeline(brief, dependencies, observer):
        raise RuntimeError("token=should-not-leak")
    response = TestClient(create_app(runtime_provider=FakeProvider(), pipeline_callable=failing_pipeline)).post("/api/runs", json={"brief": "ok"})
    events = stream_events(response)
    assert events[-1]["type"] == "run_failed"
    assert events[-1]["error"]["code"] == "internal_error"
    assert "should-not-leak" not in response.text


def test_busy_gate_rejects_second_run_and_health_remains_available():
    gate = ProcessRunGate()
    assert gate.try_acquire()
    client = TestClient(create_app(runtime_provider=FakeProvider(), run_gate=gate))
    response = client.post("/api/runs", json={"brief": "ok"})
    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "run_in_progress"
    assert client.get("/healthz").status_code == 200
    gate.release()


def test_gate_releases_only_when_owned_pipeline_task_completes():
    gate = ProcessRunGate()
    assert gate.try_acquire()
    started = asyncio.Event()
    finish = asyncio.Event()

    async def blocked():
        started.set()
        await finish.wait()

    async def exercise():
        task = asyncio.create_task(_run_with_owned_gate(gate, blocked))
        await started.wait()
        assert not gate.try_acquire()
        finish.set()
        await task
        assert gate.try_acquire()
        gate.release()

    asyncio.run(exercise())

@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan"), True, "bad"])
def test_invalid_run_timeout_is_rejected_during_app_construction(timeout):
    with pytest.raises(ValueError):
        create_app(run_timeout_seconds=timeout)


def test_soft_timeout_streams_terminal_events_without_completion():
    async def slow_pipeline(brief, dependencies, observer):
        await observer("director", "running", None)
        await asyncio.Event().wait()

    response = TestClient(
        create_app(
            runtime_provider=FakeProvider(),
            pipeline_callable=slow_pipeline,
            run_timeout_seconds=0.01,
        )
    ).post("/api/runs", json={"brief": "ok"})
    events = stream_events(response)
    assert [event["type"] for event in events] == [
        "run_started", "stage_started", "stage_failed", "run_failed"
    ]
    assert events[-1]["error"]["code"] == "run_timeout"
    assert events[-1]["stage"] == "director"
    assert "run_completed" not in response.text


def test_owner_cancellation_keeps_gate_until_real_parallel_worker_drains(monkeypatch):
    started = threading.Event()
    release = threading.Event()
    calls = {name: 0 for name in ("parallel", "research", "physical", "scene", "validation")}
    dependencies = HostedRuntimeDependencies(*(SimpleNamespace() for _ in range(6)))

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
    gate = ProcessRunGate()
    assert gate.try_acquire()

    async def owner_operation():
        await orchestrator.run_hosted_pipeline("brief", dependencies)

    async def exercise():
        owner_task = asyncio.create_task(_run_with_owned_gate(gate, owner_operation))
        await asyncio.to_thread(started.wait)
        owner_task.cancel()
        await asyncio.sleep(0)
        assert not owner_task.done()
        assert not gate.try_acquire()
        owner_task.cancel()
        await asyncio.sleep(0)
        assert not owner_task.done()
        assert not gate.try_acquire()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await owner_task
        assert gate.try_acquire()
        gate.release()

    asyncio.run(exercise())
    assert calls == {"parallel": 1, "research": 0, "physical": 0, "scene": 0, "validation": 0}

def test_timeout_never_enqueues_run_completed_after_the_stream_sentinel(monkeypatch):
    original_queue = asyncio.Queue
    queue_records = []

    class TrackingQueue(original_queue):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.record = []
            queue_records.append(self.record)

        async def put(self, value):
            self.record.append(value)
            await super().put(value)

    async def slow_pipeline(brief, dependencies, observer):
        await observer("director", "running", None)
        await asyncio.Event().wait()

    monkeypatch.setattr(app_module.asyncio, "Queue", TrackingQueue)
    response = TestClient(
        create_app(
            runtime_provider=FakeProvider(),
            pipeline_callable=slow_pipeline,
            run_timeout_seconds=0.01,
        )
    ).post("/api/runs", json={"brief": "ok"})
    assert response.status_code == 200
    record = next(record for record in queue_records if any(
        isinstance(value, dict) and value.get("type") == "run_started" for value in record
    ))
    sentinel_index = record.index(None)
    assert all(
        not isinstance(value, dict) or value.get("type") != "run_completed"
        for value in record
    )
    assert record[sentinel_index + 1:] == []


def test_owner_cancellation_after_timeout_drains_real_worker_before_gate_release(monkeypatch):
    started = threading.Event()
    release = threading.Event()
    calls = {name: 0 for name in ("parallel", "research", "physical", "scene", "validation")}
    dependencies = HostedRuntimeDependencies(*(SimpleNamespace() for _ in range(6)))

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
    app = create_app(
        runtime_provider=FakeProvider(),
        pipeline_callable=orchestrator.run_hosted_pipeline,
        run_timeout_seconds=0.01,
    )
    app.state.runtime_provider.dependencies = dependencies
    endpoint = next(route.endpoint for route in app.routes if route.path == "/api/runs")
    request = Request({"type": "http", "method": "POST", "path": "/api/runs", "headers": [(b"content-type", b"application/json")]})

    async def exercise():
        response = await endpoint(request, RunRequest(brief="ok"))
        chunks = [chunk async for chunk in response.body_iterator]
        events = [json.loads(chunk.decode("utf-8")) for chunk in chunks]
        assert events[0]["type"] == "run_started"
        assert any(
            event["type"] == "stage_started" and event["stage"] == "parallel_retrieval"
            for event in events
        )
        assert [event["type"] for event in events[-2:]] == ["stage_failed", "run_failed"]
        assert events[-1]["error"]["code"] == "run_timeout"
        await asyncio.to_thread(started.wait)
        owner_task = next(iter(app.state.active_tasks))
        assert not owner_task.done()
        assert not app.state.run_gate.try_acquire()
        owner_task.cancel()
        await asyncio.sleep(0)
        assert not owner_task.done()
        assert not app.state.run_gate.try_acquire()
        owner_task.cancel()
        await asyncio.sleep(0)
        assert not owner_task.done()
        assert not app.state.run_gate.try_acquire()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await owner_task
        assert app.state.run_gate.try_acquire()
        app.state.run_gate.release()

    asyncio.run(exercise())
    assert calls == {"parallel": 1, "research": 0, "physical": 0, "scene": 0, "validation": 0}

def test_normal_timeout_drains_real_parallel_worker_without_cancelling_owner(monkeypatch):
    started = threading.Event()
    release = threading.Event()
    calls = {name: 0 for name in ("parallel", "research", "physical", "scene", "validation")}
    dependencies = HostedRuntimeDependencies(*(SimpleNamespace() for _ in range(6)))

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
    app = create_app(
        runtime_provider=FakeProvider(),
        pipeline_callable=orchestrator.run_hosted_pipeline,
        run_timeout_seconds=0.01,
    )
    app.state.runtime_provider.dependencies = dependencies
    endpoint = next(route.endpoint for route in app.routes if route.path == "/api/runs")
    request = Request({"type": "http", "method": "POST", "path": "/api/runs", "headers": [(b"content-type", b"application/json")]})

    async def exercise():
        response = await endpoint(request, RunRequest(brief="ok"))
        chunks = [chunk async for chunk in response.body_iterator]
        events = [json.loads(chunk.decode("utf-8")) for chunk in chunks]
        assert events[-1]["error"]["code"] == "run_timeout"
        assert all(event["type"] != "run_completed" for event in events)
        await asyncio.to_thread(started.wait)
        owner_task = next(iter(app.state.active_tasks))
        assert not owner_task.done()
        assert not app.state.run_gate.try_acquire()
        release.set()
        await owner_task
        assert app.state.run_gate.try_acquire()
        app.state.run_gate.release()

    asyncio.run(exercise())
    assert calls == {"parallel": 1, "research": 0, "physical": 0, "scene": 0, "validation": 0}
