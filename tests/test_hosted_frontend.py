"""Offline static-boundary tests for the hosted no-build browser frontend."""

from fastapi.testclient import TestClient

from src.backend.app import create_app


class ProviderProbe:
    def __init__(self):
        self.calls = 0

    async def get(self):
        self.calls += 1
        raise AssertionError("Static frontend requests must not initialize runtime providers")


def frontend_files():
    base = __import__("pathlib").Path("src/frontend")
    return {
        "html": (base / "index.html").read_text(encoding="utf-8"),
        "js": (base / "app.js").read_text(encoding="utf-8"),
        "css": (base / "styles.css").read_text(encoding="utf-8"),
    }


def test_frontend_root_and_assets_are_same_origin_static_resources_without_runtime_initialization():
    provider = ProviderProbe()
    client = TestClient(create_app(runtime_provider=provider))
    root = client.get("/")
    script = client.get("/assets/app.js")
    styles = client.get("/assets/styles.css")
    assert root.status_code == 200
    assert root.headers["content-type"].startswith("text/html")
    assert script.status_code == 200
    assert "javascript" in script.headers["content-type"]
    assert styles.status_code == 200
    assert styles.headers["content-type"].startswith("text/css")
    assert provider.calls == 0


def test_frontend_html_has_strict_same_origin_security_headers_and_no_external_dependencies():
    response = TestClient(create_app(runtime_provider=ProviderProbe())).get("/")
    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "style-src 'self'" in csp
    assert "connect-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    html = response.text
    assert 'href="/assets/styles.css"' in html
    assert 'src="/assets/app.js"' in html
    assert "http://" not in html and "https://" not in html


def test_frontend_html_contains_required_composer_runtime_artifact_and_terminal_surfaces():
    html = frontend_files()["html"]
    assert '<form id="brief-form">' in html
    assert '<textarea id="brief"' in html
    assert 'maxlength="6000"' in html
    assert 'id="run-button"' in html
    assert 'id="stage-rail"' in html
    assert 'id="artifact-grid"' in html
    assert 'id="terminal-status"' in html
    assert 'role="status"' in html
    assert "Validation Readiness describes whether a scene plan is structured for later validation." in html


def test_frontend_script_declares_exact_stage_and_specialist_artifact_boundaries():
    script = frontend_files()["js"]
    for stage in (
        "director", "research_planning", "parallel_retrieval", "research",
        "physical_constraints", "scene_planning", "validation_readiness",
    ):
        assert f'"{stage}"' in script
    specialist_section = script.split("const SPECIALIST_ARTIFACT_STAGES = [", 1)[1].split("];", 1)[0]
    for stage in ("director", "research", "physical_constraints", "scene_planning", "validation_readiness"):
        assert f'"{stage}"' in specialist_section
    assert '"research_planning"' not in specialist_section
    assert '"parallel_retrieval"' not in specialist_section


def test_frontend_script_uses_incremental_ndjson_primitives_and_same_origin_api_only():
    script = frontend_files()["js"]
    for token in ("fetch(", '"/api/runs"', "response.body.getReader()", "TextDecoder", "JSON.parse", "buffer.indexOf(\"\\n\")"):
        assert token in script
    assert "EventSource" not in script
    assert "WebSocket" not in script
    assert "AbortController" not in script


def test_frontend_script_has_no_dangerous_data_execution_or_fake_progress_timers():
    script = frontend_files()["js"]
    for token in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function", "setInterval", "setTimeout"):
        assert token not in script
    assert "textContent" in script


def test_frontend_files_have_no_external_runtime_dependency_or_sensitive_configuration():
    files = frontend_files()
    combined = "\n".join(files.values())
    assert "http://" not in combined and "https://" not in combined
    for token in ("API_KEY", "GOOGLE_CLOUD_PROJECT", "credential", "run_id input", "model selection"):
        assert token not in combined
    assert "repository-root `index.html` remains" in (__import__("pathlib").Path("src/frontend/README.md").read_text(encoding="utf-8").lower())


def test_health_remains_independent_of_frontend_static_routes():
    provider = ProviderProbe()
    client = TestClient(create_app(runtime_provider=provider))
    assert client.get("/health").json() == {"status": "ok"}
    assert provider.calls == 0

def test_frontend_script_has_explicit_global_stage_and_terminal_protocol_guards():
    script = frontend_files()["js"]
    for token in (
        "nextStageIndex",
        "activeStage",
        "pendingFailure",
        "event.stage !== STAGES[state.nextStageIndex]",
        "event.stage !== state.activeStage",
        "state.nextStageIndex += 1",
        "state.pendingFailure = { stage: event.stage, code: event.error.code }",
        "state.pendingFailure ||",
        "state.activeStage !== null",
        "state.nextStageIndex !== STAGES.length",
        'Object.prototype.hasOwnProperty.call(event, "stage")',
        'event.stage !== "internal"',
        'event.error.code !== "internal_error"',
        "event.stage !== state.pendingFailure.stage",
        "event.error.code !== state.pendingFailure.code",
        'event.error.code === "run_timeout" && !hasStage',
    ):
        assert token in script
