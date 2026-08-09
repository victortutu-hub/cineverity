# CineVerity

**Agentic AI technical director for physically grounded cinematic scene planning, research, and validation.**

> Development build for the **Agentic Cinema: The Blockbuster Hackathon 2026**.

## Vision

CineVerity explores an agentic workflow that bridges creative cinematic intent and physical reality.

A filmmaker or technical artist describes the scene they want to create. The system is intended to:

1. interpret the creative goal,
2. research relevant evidence at runtime,
3. extract physical and technical constraints,
4. convert those constraints into a production-oriented scene specification,
5. validate the result for contradictions, uncertainty, and unsupported assumptions.

The goal is **not** to replace artistic direction or automatically generate a movie.

CineVerity is designed to help creators understand what should be physically true, what is uncertain, which recommendations are evidence-grounded, and where reality is being intentionally bent for artistic reasons.

## Core question

> **Can an AI system help filmmakers bend reality intentionally, rather than accidentally?**

## Planned agentic workflow

```text
Creative Intent
      |
      v
Director Agent
      |
      +--> Research Agent ------> Parallel Search API
      |
      +--> Physical Constraints Agent
      |
      +--> Scene Planning Agent
      |
      +--> Validation Agent
      |
      v
Evidence-grounded Cinematic Production Plan
```

## Planned stack

- Python
- FastAPI
- Gemini on Google Cloud
- Google Agent Development Kit / Gemini Enterprise Agent Platform
- Parallel Search API
- MCP-based integrations where appropriate
- JavaScript, HTML and CSS
- Google Cloud deployment services

Only technologies that are actually implemented in the final build will be claimed in the hackathon submission.

## Repository status

CineVerity is a **new project created during the hackathon period**. The repository intentionally starts from a minimal baseline so that its implementation history remains clear and auditable.

Current stage:

- [x] Public repository initialized
- [x] MIT open-source license
- [x] Initial project documentation
- [x] Development landing page
- [ ] Agent orchestration layer
- [ ] Parallel runtime research integration
- [ ] Physical-constraint extraction
- [ ] Scene-plan schema
- [ ] Validation pipeline
- [ ] Hosted functional MVP
- [ ] Demo and final submission assets

## Architecture

See [`docs/architecture.md`](docs/architecture.md).

## Hackathon notes

See [`docs/hackathon.md`](docs/hackathon.md).

## Development landing page

The root [`index.html`](index.html) is a static development landing page intended for GitHub Pages while the functional application is being built.

It intentionally does **not** claim unfinished features as implemented.

## License

MIT License. See [`LICENSE`](LICENSE).
