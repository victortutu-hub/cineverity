"""Offline boundary tests for the controlled Research runner."""

import asyncio
import builtins
import importlib

import pytest


def runner_module():
    return importlib.import_module("scripts.run_research_agent")


def test_1_emit_research_json_reconfigures_stdout_as_utf8_without_mutation(monkeypatch):
    runner = runner_module()
    writes = []

    class Stdout:
        def reconfigure(self, **kwargs):
            assert kwargs == {"encoding": "utf-8"}

        def write(self, value):
            writes.append(value)

    monkeypatch.setattr(runner.sys, "stdout", Stdout())
    runner.emit_research_json('{"title": "Î» Âµ Ã… Ω 漢字"}')
    assert "".join(writes) == '{"title": "Î» Âµ Ã… Ω 漢字"}\n'


@pytest.mark.parametrize(("supplied_location", "expected_location"), [(None, "global"), ("europe-west4", "europe-west4")])
def test_2_runner_initializes_vertex_before_research_agent_import(monkeypatch, supplied_location, expected_location):
    runner = runner_module()
    events = []

    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    monkeypatch.setenv("CINEVERITY_GEMINI_MODEL", "gemini-3.5-flash")
    if supplied_location is None:
        monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    else:
        monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", supplied_location)

    def fake_init(*, project, location):
        events.append(("vertexai.init", project, location))

    class StopAtResearchImport(Exception):
        pass

    original_import = builtins.__import__

    def tracked_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "src.agents.research_agent":
            events.append(("research_agent_import",))
            raise StopAtResearchImport()
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(runner.vertexai, "init", fake_init)
    monkeypatch.setattr(builtins, "__import__", tracked_import)
    with pytest.raises(StopAtResearchImport):
        asyncio.run(runner.run_research(runner.Path("unused.json")))

    assert events == [
        ("vertexai.init", "test-project", expected_location),
        ("research_agent_import",),
    ]
    assert runner.os.environ["GOOGLE_CLOUD_LOCATION"] == expected_location