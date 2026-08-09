"""Run CineVerity's first ADK agent locally."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Allow running this script from the repository root without installing CineVerity.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.agents.hello_agent import hello_app  # noqa: E402


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"[ERROR] Missing environment variable: {name}", file=sys.stderr)
        raise SystemExit(2)
    return value


async def main() -> None:
    project_id = require_env("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    enterprise = os.getenv("GOOGLE_GENAI_USE_ENTERPRISE", "")
    model = os.getenv("CINEVERITY_GEMINI_MODEL", "gemini-3.5-flash")

    if enterprise.lower() not in {"true", "1", "yes"}:
        print("[ERROR] GOOGLE_GENAI_USE_ENTERPRISE must be True.", file=sys.stderr)
        raise SystemExit(2)

    print("CineVerity Phase 0 — First ADK Agent")
    print(f"Project : {project_id}")
    print(f"Location: {location}")
    print(f"Model   : {model}")
    print("-" * 64)

    async for event in hello_app.async_stream_query(
        user_id="cineverity-phase0",
        message=(
            "Introduce yourself in three short sentences and confirm what "
            "this Phase 0 test proves. Do not describe unimplemented features."
        ),
    ):
        content = event.get("content") or {}

        for part in content.get("parts", []):
            text = part.get("text")
            if text:
                print(text)

    print("-" * 64)
    print("[OK] ADK agent execution completed.")


if __name__ == "__main__":
    asyncio.run(main())
