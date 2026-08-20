"""Offline tests for the FastAPI NDJSON transport foundation."""

import asyncio
import json

import pytest

from fastapi.testclient import TestClient

from src.backend.app import ProcessRunGate, _run_with_owned_gate, create_app
from src.backend.bootstrap import HostedRuntimeBootstrapError
from src.backend.orchestrator import HostedRuntimeDependencies, HostedStageError


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
