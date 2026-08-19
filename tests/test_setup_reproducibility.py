"""Offline setup/reproducibility tests for public runtime entry points."""

import asyncio
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.contracts.director_intent import DirectorIntentContract
from tests.test_director_agent import make_sample_contract_payload


DIRECTOR_OUTPUT = "CineVerity Phase 1 — Director Agent Structured Output Integration v0.1"


def director_runner():
    return importlib.import_module("scripts.run_director_agent")


@pytest.mark.parametrize(
    ("module_name", "function_name", "paths"),
    [
        ("scripts.run_director_agent", "run_director", ("creative brief",)),
        ("scripts.run_research_agent", "run_research", (Path("director.json"),)),
        (
            "scripts.run_physical_constraints_agent",
            "run_physical_constraints",
            (Path("director.json"), Path("research.json")),
        ),
        (
            "scripts.run_scene_planning_agent",
            "run_scene_planning",
            (Path("director.json"), Path("physical.json")),
        ),
        (
            "scripts.run_validation_readiness_agent",
            "run_validation_readiness",
            (Path("director.json"), Path("physical.json"), Path("scene.json")),
        ),
    ],
)
def test_public_stage_runners_require_google_cloud_project_before_vertex_or_agent_import(
    monkeypatch, module_name, function_name, paths
):
    runner = importlib.import_module(module_name)
    vertex_calls = []
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    monkeypatch.setattr(runner.vertexai, "init", lambda **kwargs: vertex_calls.append(kwargs))

    with pytest.raises(SystemExit, match="GOOGLE_CLOUD_PROJECT must be set"):
        asyncio.run(getattr(runner, function_name)(*paths))

    assert vertex_calls == []


def test_director_output_writes_only_validated_clean_json(monkeypatch, tmp_path, capsys):
    runner = director_runner()
    payload = make_sample_contract_payload()
    accepted = DirectorIntentContract.model_validate(payload)
    output_path = tmp_path / "director.json"
    validation_calls = []

    class FakeDirectorApp:
        async def async_stream_query(self, **kwargs):
            yield {"content": {"parts": [{"text": json.dumps(payload)}]}}

    def validate(raw_text):
        validation_calls.append(raw_text)
        assert not output_path.exists()
        return accepted

    fake_agent_module = SimpleNamespace(
        director_app=FakeDirectorApp(),
        extract_text_from_adk_events=lambda events: events[0]["content"]["parts"][0]["text"],
        validate_director_response=validate,
    )
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    monkeypatch.setattr(runner.vertexai, "init", lambda **kwargs: None)
    monkeypatch.setitem(sys.modules, "src.agents.director_agent", fake_agent_module)

    asyncio.run(runner.run_director("brief", output_path))

    artifact = output_path.read_text(encoding="utf-8")
    assert json.loads(artifact) == accepted.model_dump(mode="json")
    assert DIRECTOR_OUTPUT not in artifact
    assert "[OK]" not in artifact
    assert validation_calls
    assert DIRECTOR_OUTPUT in capsys.readouterr().out


def test_invalid_director_candidate_never_writes_output_artifact(monkeypatch, tmp_path):
    runner = director_runner()
    output_path = tmp_path / "director.json"

    class FakeDirectorApp:
        async def async_stream_query(self, **kwargs):
            yield {"content": {"parts": [{"text": "{}"}]}}

    fake_agent_module = SimpleNamespace(
        director_app=FakeDirectorApp(),
        extract_text_from_adk_events=lambda events: "{}",
        validate_director_response=lambda raw_text: (_ for _ in ()).throw(ValueError("invalid candidate")),
    )
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    monkeypatch.setattr(runner.vertexai, "init", lambda **kwargs: None)
    monkeypatch.setitem(sys.modules, "src.agents.director_agent", fake_agent_module)

    with pytest.raises(ValueError, match="invalid candidate"):
        asyncio.run(runner.run_director("brief", output_path))

    assert not output_path.exists()


def test_env_example_contains_only_required_placeholders():
    text = Path(".env.example").read_text(encoding="utf-8")
    assert "GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID" in text
    assert "GOOGLE_CLOUD_LOCATION=global" in text
    assert "GOOGLE_GENAI_USE_ENTERPRISE=True" in text
    assert "CINEVERITY_GEMINI_MODEL=gemini-3.5-flash" in text
    assert "PARALLEL_API_KEY=" in text
    assert "cineverity-hackathon-2026" not in text
    assert "AIza" not in text
    assert "BEGIN PRIVATE KEY" not in text