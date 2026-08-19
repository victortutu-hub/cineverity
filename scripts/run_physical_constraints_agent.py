"""Controlled Step 3.3 runner for Physical Constraints synthesis."""

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

def emit_physical_constraints_json(json_text: str) -> None:
    """Emit contract JSON through UTF-8 stdout without changing its content."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json_text)


async def run_physical_constraints(director_contract_path: Path, research_contract_path: Path) -> None:
    project = require_env_setting("GOOGLE_CLOUD_PROJECT")
    location = get_env_setting("GOOGLE_CLOUD_LOCATION", "global")
    enterprise = get_env_setting("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    get_env_setting("CINEVERITY_GEMINI_MODEL", "gemini-3.5-flash")
    vertexai.init(project=project, location=location)
    if enterprise.lower() not in {"true", "1", "yes"}:
        raise SystemExit("GOOGLE_GENAI_USE_ENTERPRISE must be True.")

    from src.agents.physical_constraints_agent import physical_constraints_app
    from src.services.physical_constraints_runtime import (
        synthesize_physical_constraints,
        validate_runtime_inputs,
    )

    director_json = director_contract_path.read_text(encoding="utf-8")
    research_json = research_contract_path.read_text(encoding="utf-8")
    director, research = validate_runtime_inputs(director_json, research_json)
    accepted = await synthesize_physical_constraints(physical_constraints_app, director, research)
    emit_physical_constraints_json(accepted.model_dump_json(indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CineVerity Physical Constraints synthesis from validated JSON.")
    parser.add_argument("--director-contract", type=Path, required=True)
    parser.add_argument("--research-contract", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run_physical_constraints(args.director_contract, args.research_contract))


if __name__ == "__main__":
    main()