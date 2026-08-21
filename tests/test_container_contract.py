"""Static contract checks for the credential-safe hosted Linux container."""

from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE_PATH = PROJECT_ROOT / "Dockerfile"
DOCKERIGNORE_PATH = PROJECT_ROOT / ".dockerignore"
LOCK_PATH = PROJECT_ROOT / "requirements-container.lock"
DIRECT_RUNTIME_PACKAGES = {
    "google-genai", "google-cloud-aiplatform", "parallel-web", "pydantic", "fastapi", "uvicorn",
}


def _non_comment_lock_lines() -> list[str]:
    return [line.strip() for line in LOCK_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def _dockerfile_instructions(instruction: str) -> list[str]:
    return [
        line.strip()
        for line in DOCKERFILE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip().upper().startswith(f"{instruction} ")
    ]


def test_dockerfile_pins_the_required_linux_python_base_by_digest() -> None:
    dockerfile = DOCKERFILE_PATH.read_text(encoding="utf-8")
    assert re.search(r"^FROM python:3\.11\.9-slim-bookworm@sha256:[0-9a-f]{64}$", dockerfile, re.MULTILINE)


def test_dockerfile_uses_only_the_runtime_lock_and_exact_bounded_copy_contract() -> None:
    dockerfile = DOCKERFILE_PATH.read_text(encoding="utf-8")
    assert "requirements-container.lock" in dockerfile
    assert "requirements-dev.txt" not in dockerfile
    assert "python -m pip check" in dockerfile
    assert _dockerfile_instructions("COPY") == [
        "COPY requirements-container.lock ./",
        "COPY --chown=cineverity:cineverity src/ ./src/",
    ]
    assert _dockerfile_instructions("ADD") == []


def test_dockerfile_uses_a_non_root_single_worker_port_aware_runtime() -> None:
    dockerfile = DOCKERFILE_PATH.read_text(encoding="utf-8")
    assert re.search(r"^USER (?!root$|0$)\S+$", dockerfile, re.MULTILINE)
    assert "src.backend.app:app" in dockerfile
    assert "0.0.0.0" in dockerfile
    assert "$PORT" in dockerfile
    assert "--workers 1" in dockerfile
    assert "exec python -m uvicorn" in dockerfile


def test_dockerfile_contains_no_credential_configuration_or_private_material() -> None:
    dockerfile = DOCKERFILE_PATH.read_text(encoding="utf-8")
    forbidden = ("PARALLEL_API_KEY=", "GOOGLE_APPLICATION_CREDENTIALS=", "GOOGLE_CLOUD_PROJECT=", "BEGIN PRIVATE KEY", "service-account")
    assert not any(token in dockerfile for token in forbidden)


def test_dockerignore_is_the_exact_ordered_build_context_allowlist() -> None:
    entries = [
        line.strip()
        for line in DOCKERIGNORE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert entries == ["**", "!Dockerfile", "!requirements-container.lock", "!src/", "!src/**"]


def test_runtime_lock_is_exact_and_contains_the_validated_direct_dependencies() -> None:
    lines = _non_comment_lock_lines()
    exact_pin = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*==[^\s<>=~@]+$")
    assert lines
    assert all(line.count("==") == 1 for line in lines)
    assert all(exact_pin.fullmatch(line) for line in lines)
    assert not any(
        ">=" in line
        or "<=" in line
        or "~=" in line
        or line.startswith(("-r", "-e", "git+", "http://", "https://"))
        or "://" in line
        or "@" in line
        or "@ file:" in line
        for line in lines
    )
    names = [line.split("==", 1)[0].lower() for line in lines]
    values = [line.split("==", 1)[1] for line in lines]
    assert len(names) == len(set(names))
    assert not any("/" in value or "\\" in value for value in values)
    assert DIRECT_RUNTIME_PACKAGES <= set(names)