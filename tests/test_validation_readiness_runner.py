"""Offline boundary tests for the controlled Validation Readiness runner."""

import asyncio
import builtins
import importlib
import sys
from types import SimpleNamespace

import pytest

@pytest.fixture(autouse=True)
def configured_google_project(monkeypatch):
    """Keep runner-flow tests focused beyond the required-project preflight."""
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
def runner_module():
    return importlib.import_module("scripts.run_validation_readiness_agent")


def test_1_emit_json_reconfigures_stdout_as_utf8_without_mutation(monkeypatch):
    runner = runner_module(); writes = []
    class Stdout:
        def reconfigure(self, **kwargs): assert kwargs == {"encoding": "utf-8"}
        def write(self, value): writes.append(value)
    monkeypatch.setattr(runner.sys, "stdout", Stdout())
    payload = '{"summary":"fizică, lumină, refracție — λ μ Å 漢字"}'
    runner.emit_validation_readiness_json(payload)
    assert "".join(writes) == payload + "\n"


@pytest.mark.parametrize(("location", "expected"), [(None, "global"), ("europe-west4", "europe-west4")])
def test_2_vertex_initializes_before_lazy_agent_import(monkeypatch, location, expected):
    runner = runner_module(); events = []
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.delenv("CINEVERITY_GEMINI_MODEL", raising=False)
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    if location is None: monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    else: monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", location)
    monkeypatch.setattr(runner.vertexai, "init", lambda *, project, location: events.append(("vertexai.init", project, location)))
    original_import = builtins.__import__
    class StopAtAgentImport(Exception): pass
    def tracked_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "src.agents.validation_readiness_agent":
            events.append(("agent_import",)); raise StopAtAgentImport()
        return original_import(name, globals, locals, fromlist, level)
    monkeypatch.setattr(builtins, "__import__", tracked_import)
    with pytest.raises(StopAtAgentImport):
        asyncio.run(runner.run_validation_readiness(runner.Path("a.json"), runner.Path("b.json"), runner.Path("c.json")))
    assert events == [("vertexai.init", "test-project", expected), ("agent_import",)]
    assert runner.os.environ["GOOGLE_CLOUD_LOCATION"] == expected
    assert runner.os.environ["CINEVERITY_GEMINI_MODEL"] == "gemini-3.5-flash"


def test_3_invalid_enterprise_fails_before_agent_import(monkeypatch):
    runner = runner_module(); monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "False")
    monkeypatch.setattr(runner.vertexai, "init", lambda **kwargs: None)
    with pytest.raises(SystemExit, match="GOOGLE_GENAI_USE_ENTERPRISE"):
        asyncio.run(runner.run_validation_readiness(runner.Path("a"), runner.Path("b"), runner.Path("c")))


def test_4_missing_input_fails_before_validation_or_synthesis(monkeypatch):
    runner = runner_module(); calls = []
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    monkeypatch.setattr(runner.vertexai, "init", lambda **kwargs: None)
    monkeypatch.setitem(sys.modules, "src.agents.validation_readiness_agent", SimpleNamespace(validation_readiness_app=object()))
    monkeypatch.setitem(sys.modules, "src.services.validation_readiness_runtime", SimpleNamespace(validate_runtime_inputs=lambda *a: calls.append("validate"), synthesize_validation_readiness=lambda *a: calls.append("synthesize")))
    with pytest.raises(FileNotFoundError):
        asyncio.run(runner.run_validation_readiness(runner.Path("a"), runner.Path("b"), runner.Path("c")))
    assert calls == []


def test_5_valid_flow_preflights_then_synthesizes_once(monkeypatch, tmp_path):
    runner = runner_module(); calls = []; supplied = ("director", "physical", "scene")
    paths = [tmp_path / name for name in ("d.json", "p.json", "s.json")]
    for path in paths: path.write_text("{}", encoding="utf-8")
    output = SimpleNamespace(model_dump_json=lambda **kwargs: '{"accepted":"λ"}')
    def fake_validate(*values): calls.append(("validate", values)); return supplied
    async def fake_synthesize(*values): calls.append(("synthesize", values)); return output
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    monkeypatch.setattr(runner.vertexai, "init", lambda **kwargs: None)
    monkeypatch.setattr(runner, "emit_validation_readiness_json", lambda value: calls.append(("emit", value)))
    monkeypatch.setitem(sys.modules, "src.agents.validation_readiness_agent", SimpleNamespace(validation_readiness_app="fake-app"))
    monkeypatch.setitem(sys.modules, "src.services.validation_readiness_runtime", SimpleNamespace(validate_runtime_inputs=fake_validate, synthesize_validation_readiness=fake_synthesize))
    asyncio.run(runner.run_validation_readiness(*paths))
    assert calls[0][0] == "validate"
    assert calls[1] == ("synthesize", ("fake-app", *supplied))
    assert calls[2] == ("emit", '{"accepted":"λ"}')


def test_6_preflight_failure_propagates_without_emit(monkeypatch, tmp_path):
    runner = runner_module(); calls = []; paths = [tmp_path / name for name in ("d", "p", "s")]
    for path in paths: path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    monkeypatch.setattr(runner.vertexai, "init", lambda **kwargs: None)
    monkeypatch.setitem(sys.modules, "src.agents.validation_readiness_agent", SimpleNamespace(validation_readiness_app="fake"))
    monkeypatch.setitem(sys.modules, "src.services.validation_readiness_runtime", SimpleNamespace(validate_runtime_inputs=lambda *a: (_ for _ in ()).throw(ValueError("scope mismatch")), synthesize_validation_readiness=lambda *a: calls.append("synthesize")))
    monkeypatch.setattr(runner, "emit_validation_readiness_json", lambda value: calls.append("emit"))
    with pytest.raises(ValueError, match="scope mismatch"): asyncio.run(runner.run_validation_readiness(*paths))
    assert calls == []


def test_7_cli_has_exact_three_contract_inputs_and_no_direct_model_access():
    source = open(runner_module().__file__, encoding="utf-8").read()
    for flag in ("--director-contract", "--physical-constraints-contract", "--scene-planning-contract"):
        assert flag in source
    assert "--research-contract" not in source
    assert "async_stream_query" not in source


def test_8_runner_uses_utf8_reads_and_runtime_synthesis_boundary():
    source = open(runner_module().__file__, encoding="utf-8").read()
    assert source.count('encoding="utf-8"') >= 3
    assert "validate_runtime_inputs" in source and "synthesize_validation_readiness" in source
