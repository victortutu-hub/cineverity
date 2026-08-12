"""Offline boundary tests for the controlled Physical Constraints runner."""

import asyncio
import builtins
import importlib
import json
import sys
from types import SimpleNamespace

import pytest

from tests.test_physical_constraints_runtime import candidate_payload, director, research


def runner_module():
    return importlib.import_module("scripts.run_physical_constraints_agent")


def test_1_emit_json_reconfigures_stdout_as_utf8_without_mutation(monkeypatch):
    runner = runner_module(); writes = []
    class Stdout:
        def reconfigure(self, **kwargs): assert kwargs == {"encoding": "utf-8"}
        def write(self, value): writes.append(value)
    monkeypatch.setattr(runner.sys, "stdout", Stdout())
    payload = '{"summary": "λ μ Å 漢字 refracție fizică și lumină coerentă"}'
    runner.emit_physical_constraints_json(payload)
    assert "".join(writes) == payload + "\n"

@pytest.mark.parametrize(("supplied_location", "expected_location"), [(None, "global"), ("europe-west4", "europe-west4")])
def test_2_runner_initializes_vertex_before_agent_import(monkeypatch, supplied_location, expected_location):
    runner = runner_module(); events = []
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "cineverity-hackathon-2026")
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    monkeypatch.setenv("CINEVERITY_GEMINI_MODEL", "gemini-3.5-flash")
    if supplied_location is None: monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    else: monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", supplied_location)
    monkeypatch.setattr(runner.vertexai, "init", lambda *, project, location: events.append(("vertexai.init", project, location)))
    original_import = builtins.__import__
    class StopAtAgentImport(Exception): pass
    def tracked_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "src.agents.physical_constraints_agent":
            events.append(("agent_import",)); raise StopAtAgentImport()
        return original_import(name, globals, locals, fromlist, level)
    monkeypatch.setattr(builtins, "__import__", tracked_import)
    with pytest.raises(StopAtAgentImport):
        asyncio.run(runner.run_physical_constraints(runner.Path("missing-director.json"), runner.Path("missing-research.json")))
    assert events == [("vertexai.init", "cineverity-hackathon-2026", expected_location), ("agent_import",)]
    assert runner.os.environ["GOOGLE_CLOUD_LOCATION"] == expected_location


def test_3_invalid_enterprise_environment_fails_before_agent_import(monkeypatch):
    runner = runner_module()
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "False")
    monkeypatch.setattr(runner.vertexai, "init", lambda **kwargs: None)
    with pytest.raises(SystemExit, match="GOOGLE_GENAI_USE_ENTERPRISE"):
        asyncio.run(runner.run_physical_constraints(runner.Path("unused-a.json"), runner.Path("unused-b.json")))


def test_4_missing_input_file_fails_without_synthesis(monkeypatch):
    runner = runner_module(); calls = []
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    monkeypatch.setattr(runner.vertexai, "init", lambda **kwargs: None)
    fake_agent_module = SimpleNamespace(physical_constraints_app=object())
    fake_runtime_module = SimpleNamespace(
        validate_runtime_inputs=lambda *args: calls.append("validate"),
        synthesize_physical_constraints=lambda *args: calls.append("synthesize"),
    )
    monkeypatch.setitem(sys.modules, "src.agents.physical_constraints_agent", fake_agent_module)
    monkeypatch.setitem(sys.modules, "src.services.physical_constraints_runtime", fake_runtime_module)
    with pytest.raises(FileNotFoundError):
        asyncio.run(runner.run_physical_constraints(runner.Path("missing-a.json"), runner.Path("missing-b.json")))
    assert calls == []


def test_5_runner_passes_validated_inputs_to_one_synthesis_call(monkeypatch, tmp_path):
    runner = runner_module(); d, r = director(), research(); output = SimpleNamespace(model_dump_json=lambda **kwargs: '{"ok": "λ"}')
    director_path = tmp_path / "director.json"; research_path = tmp_path / "research.json"
    director_path.write_text(d.model_dump_json(), encoding="utf-8"); research_path.write_text(r.model_dump_json(), encoding="utf-8")
    calls = []
    async def fake_synthesize(app, supplied_director, supplied_research):
        calls.append((app, supplied_director, supplied_research)); return output
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    monkeypatch.setattr(runner.vertexai, "init", lambda **kwargs: None)
    monkeypatch.setattr(runner, "emit_physical_constraints_json", lambda text: calls.append(text))
    monkeypatch.setitem(sys.modules, "src.agents.physical_constraints_agent", SimpleNamespace(physical_constraints_app="fake-app"))
    monkeypatch.setitem(sys.modules, "src.services.physical_constraints_runtime", SimpleNamespace(validate_runtime_inputs=lambda a, b: (d, r), synthesize_physical_constraints=fake_synthesize))
    asyncio.run(runner.run_physical_constraints(director_path, research_path))
    assert calls[0][0] == "fake-app" and calls[0][1:] == (d, r)
    assert calls[1] == '{"ok": "λ"}'