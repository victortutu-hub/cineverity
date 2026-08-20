"""Offline tests for lazy hosted runtime bootstrap."""

import asyncio
import importlib
import inspect
import os

import pytest

from src.backend.bootstrap import HostedRuntimeBootstrapError, HostedRuntimeProvider


def configured_environ():
    return {"GOOGLE_CLOUD_PROJECT": "test-project", "PARALLEL_API_KEY": "test-key"}


def test_missing_project_fails_before_vertex_initialization():
    calls = []
    provider = HostedRuntimeProvider(
        environ={"PARALLEL_API_KEY": "test-key"},
        vertex_initializer=lambda **kwargs: calls.append(kwargs),
    )
    with pytest.raises(HostedRuntimeBootstrapError):
        asyncio.run(provider.get())
    assert calls == []


def test_missing_parallel_key_fails_before_vertex_initialization():
    calls = []
    provider = HostedRuntimeProvider(
        environ={"GOOGLE_CLOUD_PROJECT": "test-project"},
        vertex_initializer=lambda **kwargs: calls.append(kwargs),
    )
    with pytest.raises(HostedRuntimeBootstrapError):
        asyncio.run(provider.get())
    assert calls == []


def test_non_enterprise_mode_fails_before_vertex_initialization():
    calls = []
    environment = configured_environ() | {"GOOGLE_GENAI_USE_ENTERPRISE": "false"}
    provider = HostedRuntimeProvider(environ=environment, vertex_initializer=lambda **kwargs: calls.append(kwargs))
    with pytest.raises(HostedRuntimeBootstrapError):
        asyncio.run(provider.get())
    assert calls == []


def test_bootstrap_order_defaults_and_successful_bundle():
    events = []
    environment = configured_environ()
    apps = tuple(object() for _ in range(5))

    def vertex(**kwargs):
        events.append(("vertex", kwargs, environment["CINEVERITY_GEMINI_MODEL"]))
    def loader():
        events.append(("agents", environment["CINEVERITY_GEMINI_MODEL"]))
        return apps
    def adapter():
        events.append(("parallel",))
        return object()

    provider = HostedRuntimeProvider(
        environ=environment,
        vertex_initializer=vertex,
        agent_loader=loader,
        parallel_adapter_factory=adapter,
    )
    runtime = asyncio.run(provider.get())
    assert environment["GOOGLE_CLOUD_LOCATION"] == "global"
    assert environment["GOOGLE_GENAI_USE_ENTERPRISE"] == "True"
    assert environment["CINEVERITY_GEMINI_MODEL"] == "gemini-3.5-flash"
    assert events == [
        ("vertex", {"project": "test-project", "location": "global"}, "gemini-3.5-flash"),
        ("agents", "gemini-3.5-flash"),
        ("parallel",),
    ]
    assert runtime.director_app is apps[0]
    assert runtime.validation_readiness_app is apps[4]


def test_successful_runtime_is_cached_and_concurrent_first_access_initializes_once():
    calls = []
    provider = HostedRuntimeProvider(
        environ=configured_environ(),
        vertex_initializer=lambda **kwargs: calls.append("vertex"),
        agent_loader=lambda: (object(), object(), object(), object(), object()),
        parallel_adapter_factory=lambda: calls.append("parallel") or object(),
    )

    async def get_twice():
        return await asyncio.gather(provider.get(), provider.get())

    first, second = asyncio.run(get_twice())
    assert first is second
    assert calls == ["vertex", "parallel"]


def test_import_is_credential_safe_and_has_no_top_level_concrete_agent_imports(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("PARALLEL_API_KEY", raising=False)
    import src.backend.bootstrap as bootstrap
    source = inspect.getsource(bootstrap)
    assert "from src.agents" not in source.split("def _default_agent_loader")[0]
    assert "from src.services.parallel_search" not in source.split("def _default_parallel_adapter_factory")[0]
    assert os.getenv("GOOGLE_CLOUD_PROJECT") is None

def test_app_import_is_credential_safe_without_bootstrapping(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("PARALLEL_API_KEY", raising=False)
    import src.backend.app as app_module

    reloaded = importlib.reload(app_module)
    assert reloaded.app is not None
    assert os.getenv("GOOGLE_CLOUD_PROJECT") is None
