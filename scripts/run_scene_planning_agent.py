"""Controlled Step 4.3 Scene Planning synthesis runner."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import vertexai

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def get_env_setting(name: str, default: str) -> str:
    value = os.getenv(name)
    if not value:
        value = default
        os.environ[name] = default
    return value


def require_env_setting(name: str) -> str:
    """Return a required environment setting without a project fallback."""
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"{name} must be set.")
    return value

def emit_scene_planning_json(json_text: str) -> None:
    """Emit accepted contract JSON as UTF-8 stdout without altering its content."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json_text)


async def run_scene_planning(
    director_contract_path: Path,
    physical_constraints_contract_path: Path,
) -> None:
    project = require_env_setting("GOOGLE_CLOUD_PROJECT")
    location = get_env_setting("GOOGLE_CLOUD_LOCATION", "global")
    enterprise = get_env_setting("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    get_env_setting("CINEVERITY_GEMINI_MODEL", "gemini-3.5-flash")
    vertexai.init(project=project, location=location)
    if enterprise.lower() not in {"true", "1", "yes"}:
        raise SystemExit("GOOGLE_GENAI_USE_ENTERPRISE must be True.")

    from src.agents.scene_planning_agent import scene_planning_app
    from src.services.scene_planning_runtime import (
        synthesize_scene_planning,
        validate_runtime_inputs,
    )

    director_json = director_contract_path.read_text(encoding="utf-8")
    physical_json = physical_constraints_contract_path.read_text(encoding="utf-8")
    director, physical = validate_runtime_inputs(director_json, physical_json)
    accepted = await synthesize_scene_planning(scene_planning_app, director, physical)
    emit_scene_planning_json(accepted.model_dump_json(indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CineVerity Scene Planning synthesis from validated JSON.")
    parser.add_argument("--director-contract", type=Path, required=True)
    parser.add_argument("--physical-constraints-contract", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run_scene_planning(args.director_contract, args.physical_constraints_contract))


if __name__ == "__main__":
    main()
