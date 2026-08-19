"""
Run CineVerity Director Agent locally against Google Cloud Gemini infrastructure.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
import vertexai

# Allow running this script from the repository root without installing CineVerity
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


REFERENCE_PROMPT = (
    "A transparent crystal monolith levitates above a dark basalt surface while three "
    "narrow colored lights pass through it, producing physically plausible internal "
    "refraction and caustics. The mood should feel alien but scientifically believable."
)

ADVERSARIAL_PROMPT = (
    "Create a diamond where red light refracts twice as strongly as blue light. "
    "It must remain completely physically accurate."
)


def get_env_setting(name: str, default: str) -> str:
    """Retrieve environment variable or fallback to default."""
    val = os.getenv(name)
    if not val:
        val = default
        os.environ[name] = default
    return val


def require_env_setting(name: str) -> str:
    """Return a required environment setting without a project fallback."""
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"{name} must be set.")
    return value

def write_accepted_director_contract(contract: object, output_path: Path) -> None:
    """Write only an already-validated Director contract as UTF-8 JSON."""
    try:
        output_path.write_text(contract.model_dump_json(indent=2), encoding="utf-8")
    except OSError as err:
        raise RuntimeError(
            f"Could not write accepted Director contract to {output_path}: {err}"
        ) from err

async def run_director(prompt: str, output_path: Path | None = None) -> None:
    """Execute Director Agent query and validate output boundary."""
    project_id = require_env_setting("GOOGLE_CLOUD_PROJECT")
    location = get_env_setting("GOOGLE_CLOUD_LOCATION", "global")
    enterprise = get_env_setting("GOOGLE_GENAI_USE_ENTERPRISE", "True")
    model = get_env_setting("CINEVERITY_GEMINI_MODEL", "gemini-3.5-flash")

    vertexai.init(project=project_id, location=location)

    if enterprise.lower() not in {"true", "1", "yes"}:
        print("[ERROR] GOOGLE_GENAI_USE_ENTERPRISE must be True.", file=sys.stderr)
        raise SystemExit(2)

    from src.agents.director_agent import (
        director_app,
        extract_text_from_adk_events,
        validate_director_response,
    )

    print("CineVerity Phase 1 — Director Agent Structured Output Integration v0.1")
    print(f"Project : {project_id}")
    print(f"Location: {location}")
    print(f"Model   : {model}")
    print(f"Prompt  : {prompt}")
    print("-" * 64)

    events = []
    # Explicit user_id as requested for local execution boundary
    async for event in director_app.async_stream_query(
        user_id="cineverity-local-director",
        message=prompt,
    ):
        events.append(event)

    print("Query complete. Extracting textual structured response...")
    raw_text = extract_text_from_adk_events(events)

    print("Validating model output against DirectorIntentContract schema boundary...")
    validated_contract = validate_director_response(raw_text)

    if output_path is not None:
        write_accepted_director_contract(validated_contract, output_path)

    print("-" * 64)
    print("Validated Cinematic Intent Contract:")
    print(validated_contract.model_dump_json(indent=2))
    print("-" * 64)
    print("[OK] Director Agent produced a validated CineVerity contract.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CineVerity Director Agent v0.1.")
    parser.add_argument(
        "--prompt",
        type=str,
        default=REFERENCE_PROMPT,
        help="Creative scene prompt to interpret.",
    )
    parser.add_argument(
        "--adversarial",
        action="store_true",
        help="Run the preset adversarial test prompt.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the accepted DirectorIntentContract JSON artifact to this path.",
    )
    args = parser.parse_args()

    prompt = ADVERSARIAL_PROMPT if args.adversarial else args.prompt
    asyncio.run(run_director(prompt, args.output))


if __name__ == "__main__":
    main()
