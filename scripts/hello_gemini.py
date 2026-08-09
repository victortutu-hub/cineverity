"""CineVerity Phase 0: minimal Gemini request through Google Cloud.

This script intentionally uses Google's Gen AI SDK and Application Default
Credentials. It does not use an API key and does not import any non-Google AI SDK.
"""

from __future__ import annotations

import os
import sys

from google import genai
from google.genai.types import HttpOptions


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"[ERROR] Missing environment variable: {name}", file=sys.stderr)
        raise SystemExit(2)
    return value


def main() -> None:
    project_id = require_env("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    enterprise = os.getenv("GOOGLE_GENAI_USE_ENTERPRISE", "")
    model = os.getenv("CINEVERITY_GEMINI_MODEL", "gemini-3.5-flash")

    if enterprise.lower() not in {"true", "1", "yes"}:
        print(
            "[ERROR] GOOGLE_GENAI_USE_ENTERPRISE must be True so CineVerity "
            "uses Google Cloud / Agent Platform rather than a developer API key.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    print("CineVerity Phase 0 — Hello Gemini")
    print(f"Project : {project_id}")
    print(f"Location: {location}")
    print(f"Model   : {model}")
    print("Backend : Google Cloud / Gemini Enterprise Agent Platform")
    print("-" * 64)

    client = genai.Client(http_options=HttpOptions(api_version="v1"))

    response = client.models.generate_content(
        model=model,
        contents=(
            "You are the first infrastructure test for CineVerity. "
            "Reply with exactly two short lines. "
            "Line 1: 'Hello from Gemini.' "
            "Line 2: state that CineVerity is connected to Google Cloud."
        ),
    )

    print(response.text)
    print("-" * 64)
    print("[OK] Gemini request completed successfully through Google Cloud.")


if __name__ == "__main__":
    main()
