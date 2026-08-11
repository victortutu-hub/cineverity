"""
CineVerity Phase 1 Step 1.3: Director Agent implementation using Google ADK and Gemini.
"""

from __future__ import annotations

import json
import os
from typing import Any, Sequence

from google.adk.agents import Agent
from vertexai import agent_engines

from src.contracts.director_intent import DirectorIntentContract

MODEL = os.getenv(
    "CINEVERITY_GEMINI_MODEL",
    "gemini-3.5-flash",
)

DIRECTOR_SYSTEM_INSTRUCTION = (
    "You are the CineVerity Director Agent. Your role is to interpret and decompose "
    "the filmmaker's creative brief into a structured Cinematic Intent Contract (v0.1).\n\n"
    "Core Principles:\n"
    "1. Preserve artistic intent above all else.\n"
    "2. Strictly distinguish between:\n"
    "   - WHAT THE ARTIST WANTS (Creative Intent)\n"
    "   - WHAT PHYSICS ALLOWS (Physical Truth)\n"
    "   - WHAT THE SYSTEM CURRENTLY KNOWS (Current Knowledge)\n"
    "3. Never turn a requested visual effect into a verified physical fact.\n"
    "4. Never silently correct or alter an artistic request to fit real-world physics.\n"
    "5. Never invent numeric refractive indices, dispersion coefficients, densities, "
    "wavelengths, physical constants, scientific evidence, or material properties "
    "not supplied by the user.\n"
    "6. Unknown physical parameters belong in 'MaterialIntent.unknown_parameters'.\n"
    "7. Questions requiring external evidence belong in 'research_required'.\n"
    "8. Physical uncertainty or potential physical conflicts belong in 'physical_questions' "
    "and/or 'ambiguities'.\n"
    "9. Aesthetic premises or non-physical requests belong in 'artistic_freedoms'.\n"
    "10. Explicit user requirements belong in 'hard_constraints'.\n"
    "11. Do not select Three.js, WebGPU, Blender, Unreal, GLSL, or any rendering engine "
    "unless explicitly requested by the user.\n"
    "12. Do not perform research, browse the web, or claim physical correctness.\n"
    "13. Produce only the structured output conforming to the required schema."
)


director_agent = Agent(
    name="director_agent",
    model=MODEL,
    description="CineVerity Director Agent interpreting creative briefs into structured intent contracts.",
    instruction=DIRECTOR_SYSTEM_INSTRUCTION,
    output_schema=DirectorIntentContract,
    tools=[],
)

director_app = agent_engines.AdkApp(agent=director_agent)


def extract_text_from_adk_events(events: Sequence[dict[str, Any]]) -> str:
    """Extract model textual structured response from a sequence of ADK event dictionaries.

    Ignores metadata, thought signatures, invocation IDs, and non-text parts.
    """
    text_chunks: list[str] = []

    for event in events:
        content = event.get("content") or {}
        parts = content.get("parts") or []

        for part in parts:
            # Skip thought parts if present
            if part.get("thought"):
                continue

            text = part.get("text")
            if text:
                text_chunks.append(text)

    full_text = "".join(text_chunks).strip()
    if not full_text:
        raise ValueError("No model text response found in ADK events.")

    return full_text


def validate_director_response(raw_text: str) -> DirectorIntentContract:
    """Validate a raw model response string against DirectorIntentContract.

    Does not attempt silent repairs or automatic retries. Fails clearly on validation error.
    """
    try:
        return DirectorIntentContract.model_validate_json(raw_text)
    except Exception as err:
        # If raw_text is json dict string or wrapped in markdown codeblocks, extract clean json
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            return DirectorIntentContract.model_validate_json(clean_text)
        except Exception:
            # Re-raise initial validation error for clear diagnostic output
            raise ValueError(f"Director Agent response failed Pydantic validation: {err}") from err
