"""CineVerity Phase 0: first Google ADK agent."""

from __future__ import annotations

import os

from google.adk.agents import Agent
from vertexai import agent_engines


MODEL = os.getenv("CINEVERITY_GEMINI_MODEL", "gemini-3.5-flash")


hello_agent = Agent(
    name="cineverity_hello_agent",
    model=MODEL,
    description="First CineVerity ADK agent used to verify Gemini + Google Cloud.",
    instruction=(
        "You are CineVerity's first infrastructure-validation agent. "
        "Be concise. Explain that your role is to confirm that the Google ADK "
        "agent layer is operational on Gemini through Google Cloud. "
        "Do not claim that the full CineVerity system is implemented."
    ),
)

hello_app = agent_engines.AdkApp(agent=hello_agent)
