"""Controlled Step 2.3B runner from a validated Director contract JSON file."""

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

def emit_research_json(json_text: str) -> None:
    """Print contract JSON as UTF-8 when the current stdout supports reconfiguration."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json_text)


async def run_research(director_contract_path: Path) -> None:
    project = require_env_setting("GOOGLE_CLOUD_PROJECT")
    location = get_env_setting("GOOGLE_CLOUD_LOCATION", "global")
    enterprise = get_env_setting("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    get_env_setting("CINEVERITY_GEMINI_MODEL", "gemini-3.5-flash")
    vertexai.init(project=project, location=location)
    if enterprise.lower() not in {"true", "1", "yes"}:
        raise SystemExit("GOOGLE_GENAI_USE_ENTERPRISE must be True.")

    from src.agents.research_agent import research_app
    from src.contracts.director_intent import DirectorIntentContract
    from src.services.parallel_search import ParallelSearchAdapter
    from src.services.research_retrieval import build_search_plans, execute_search_plans
    from src.services.research_runtime import synthesize_with_app

    director = DirectorIntentContract.model_validate_json(director_contract_path.read_text(encoding="utf-8"))
    registry = execute_search_plans(build_search_plans(director), ParallelSearchAdapter())
    accepted = await synthesize_with_app(research_app, director, registry)
    emit_research_json(accepted.model_dump_json(indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CineVerity Research synthesis from Director JSON.")
    parser.add_argument("--director-contract", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run_research(args.director_contract))


if __name__ == "__main__":
    main()
