"""Offline boundary tests for the controlled Scene Planning runner."""

import asyncio
import builtins
import importlib
import sys
from types import SimpleNamespace

import pytest

from tests.test_scene_planning_runtime import physical, rich_director


def runner_module():
    return importlib.import_module("scripts.run_scene_planning_agent")


def test_1_emit_json_reconfigures_stdout_as_utf8_without_mutation(monkeypatch):
    runner = runner_module(); writes = []

    class Stdout:
        def reconfigure(self, **kwargs): assert kwargs == {"encoding": "utf-8"}
        def write(self, value): writes.append(value)

    monkeypatch.setattr(runner.sys, "stdout", Stdout())
    payload = '{"summary":"fizică, lumină, refracție — λ μ Å 漢字"}'
    runner.emit_scene_planning_json(payload)
    assert "".join(writes) == payload + "\n"


@pytest.mark.parametrize(("location", "expected"), [(None, "global"), ("europe-west4", "europe-west4")])
def test_2_vertex_initializes_before_lazy_agent_import(monkeypatch, location, expected):
    runner = runner_module(); events = []
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("CINEVERITY_GEMINI_MODEL", raising=False)
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    if location is None: monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    else: monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", location)
    monkeypatch.setattr(runner.vertexai, "init", lambda *, project, location: events.append(("vertexai.init", project, location)))
    original_import = builtins.__import__
    class StopAtAgentImport(Exception): pass
    def tracked_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "src.agents.scene_planning_agent":
            events.append(("agent_import",)); raise StopAtAgentImport()
        return original_import(name, globals, locals, fromlist, level)
    monkeypatch.setattr(builtins, "__import__", tracked_import)
    with pytest.raises(StopAtAgentImport):
        asyncio.run(runner.run_scene_planning(runner.Path("missing-a.json"), runner.Path("missing-b.json")))
    assert events == [("vertexai.init", "cineverity-hackathon-2026", expected), ("agent_import",)]
    assert runner.os.environ["GOOGLE_CLOUD_LOCATION"] == expected
    assert runner.os.environ["CINEVERITY_GEMINI_MODEL"] == "gemini-3.5-flash"


def test_3_invalid_enterprise_fails_before_agent_import(monkeypatch):
    runner = runner_module()
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "False")
    monkeypatch.setattr(runner.vertexai, "init", lambda **kwargs: None)
    with pytest.raises(SystemExit, match="GOOGLE_GENAI_USE_ENTERPRISE"):
        asyncio.run(runner.run_scene_planning(runner.Path("unused-a.json"), runner.Path("unused-b.json")))


def test_4_missing_file_fails_before_synthesis(monkeypatch):
    runner = runner_module(); calls = []
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    monkeypatch.setattr(runner.vertexai, "init", lambda **kwargs: None)
    monkeypatch.setitem(sys.modules, "src.agents.scene_planning_agent", SimpleNamespace(scene_planning_app=object()))
    monkeypatch.setitem(sys.modules, "src.services.scene_planning_runtime", SimpleNamespace(validate_runtime_inputs=lambda *args: calls.append("validate"), synthesize_scene_planning=lambda *args: calls.append("synthesize")))
    with pytest.raises(FileNotFoundError):
        asyncio.run(runner.run_scene_planning(runner.Path("missing-a.json"), runner.Path("missing-b.json")))
    assert calls == []


def test_5_valid_runner_flow_validates_then_synthesizes_once(monkeypatch, tmp_path):
    runner = runner_module(); supplied_director, supplied_physical = rich_director(), physical()
    director_path = tmp_path / "director.json"; physical_path = tmp_path / "physical.json"
    director_path.write_text(supplied_director.model_dump_json(), encoding="utf-8")
    physical_path.write_text(supplied_physical.model_dump_json(), encoding="utf-8")
    output = SimpleNamespace(model_dump_json=lambda **kwargs: '{"accepted":"λ"}')
    calls = []
    async def fake_synthesize(app, director, physical): calls.append(("synthesize", app, director, physical)); return output
    def fake_validate(director_json, physical_json): calls.append(("validate", director_json, physical_json)); return supplied_director, supplied_physical
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    monkeypatch.setattr(runner.vertexai, "init", lambda **kwargs: None)
    monkeypatch.setattr(runner, "emit_scene_planning_json", lambda text: calls.append(("emit", text)))
    monkeypatch.setitem(sys.modules, "src.agents.scene_planning_agent", SimpleNamespace(scene_planning_app="fake-app"))
    monkeypatch.setitem(sys.modules, "src.services.scene_planning_runtime", SimpleNamespace(validate_runtime_inputs=fake_validate, synthesize_scene_planning=fake_synthesize))
    asyncio.run(runner.run_scene_planning(director_path, physical_path))
    assert calls[0][0] == "validate"
    assert calls[1] == ("synthesize", "fake-app", supplied_director, supplied_physical)
    assert calls[2] == ("emit", '{"accepted":"λ"}')


def test_6_preflight_or_synthesis_failure_propagates_without_emit(monkeypatch, tmp_path):
    runner = runner_module(); director_path = tmp_path / "director.json"; physical_path = tmp_path / "physical.json"
    director_path.write_text("{}", encoding="utf-8"); physical_path.write_text("{}", encoding="utf-8")
    calls = []
    def fail_validate(*args): raise ValueError("scope mismatch")
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    monkeypatch.setattr(runner.vertexai, "init", lambda **kwargs: None)
    monkeypatch.setitem(sys.modules, "src.agents.scene_planning_agent", SimpleNamespace(scene_planning_app="fake-app"))
    monkeypatch.setitem(sys.modules, "src.services.scene_planning_runtime", SimpleNamespace(validate_runtime_inputs=fail_validate, synthesize_scene_planning=lambda *args: calls.append("synthesize")))
    monkeypatch.setattr(runner, "emit_scene_planning_json", lambda text: calls.append("emit"))
    with pytest.raises(ValueError, match="scope mismatch"):
        asyncio.run(runner.run_scene_planning(director_path, physical_path))
    assert calls == []


def test_7_cli_has_two_inputs_no_research_and_no_direct_model_access():
    source = runner_module().__file__
    text = open(source, encoding="utf-8").read()
    assert '"--director-contract"' in text
    assert '"--physical-constraints-contract"' in text
    assert "--research-contract" not in text
    assert "async_stream_query" not in text
    assert "synthesize_scene_planning" in text
