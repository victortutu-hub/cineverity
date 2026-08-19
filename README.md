# CineVerity

**An agentic AI technical director for physically grounded cinematic scene planning.**

> Development build for the **Agentic Cinema: The Blockbuster Hackathon 2026**.

## Vision

CineVerity helps filmmakers and technical artists turn a creative brief into a traceable, physically aware scene plan. It distinguishes evidence-grounded constraints, unresolved uncertainty, and deliberate artistic deviations—so reality can be bent intentionally rather than accidentally.

It is not a movie generator or a replacement for artistic direction.

## Core question

> **Can an AI system help filmmakers bend reality intentionally, rather than accidentally?**

## Implemented workflow stages

```text
Creative Intent
→ Director Agent
→ Research Retrieval via Parallel Search API
→ Gemini Research Synthesis
→ Physical Constraints Agent
→ Scene Planning Agent
→ Validation Readiness Agent
```

Each stage has its own controlled runner and validated contract boundary. A single automatic end-to-end orchestrator is not implemented yet.

**Validation Readiness Agent** is preflight/readiness only. It does not mean rendering, simulation, measurement, scientific validation, or any other validation execution has occurred.

## Implemented today

- Director structured intent contract, schema boundary, and Gemini/ADK runtime.
- Research Evidence contract, bounded Parallel Search API retrieval with deterministic search planning, Gemini research synthesis, and provenance preservation.
- Physical Constraints contract, canonical serialization boundary, closed-input runtime, and cross-contract fidelity gates.
- Scene Planning contract, canonical serialization boundary, closed-input runtime, and runtime-owned canonical SHA-256 snapshot fingerprints.
- Validation Readiness contract, canonical serialization boundary, and closed-input preflight runtime.
- Deterministic cross-contract scope/fingerprint derivation, exact candidate fidelity checks, and offline automated tests.

### Acceptance principle

```text
validated upstream contracts
→ deterministic scope/fingerprint derivation
→ one model candidate
→ Pydantic validation
→ exact provenance/scope fidelity gate
→ accept or explicit reject
```

This keeps model generation bounded while deterministic code owns provenance, identifiers, scope, and snapshot binding.

## Implemented stack

- Python
- Gemini on Google Cloud / Vertex AI
- Google ADK and ADK app runtime
- Parallel Search API via its official Python SDK
- Pydantic
- HTML, CSS, and JavaScript development landing page

## Planned / deployment direction

- Full end-to-end orchestration across the complete pipeline
- Hosted functional MVP and deployment services
- Renderer, simulation, measurement, and executed validation systems
- Demo and final hackathon submission assets

## Local setup

Verified with Python 3.11.9.

```text
python -m venv .venv
python -m pip install -r requirements-dev.txt
gcloud auth application-default login
python -m pytest -q
```

Set the required Google Cloud environment variables in your shell; CineVerity does not automatically load `.env`. See [`docs/setup.md`](docs/setup.md) for authentication, environment examples, offline tests, and the manual stage-by-stage workflow.

## Repository status

CineVerity is a **new project created during the hackathon period**. The repository deliberately keeps its implementation history visible and auditable.

- [x] Public repository, MIT license, and project documentation
- [x] Development landing page
- [x] Director Agent runtime
- [x] Parallel runtime research integration
- [x] Gemini research synthesis and provenance boundary
- [x] Physical Constraints
- [x] Scene Planning
- [x] Validation Readiness
- [ ] Full end-to-end orchestration
- [ ] Hosted functional MVP
- [ ] Executed renderer/simulation/measurement validation
- [ ] Demo and final submission assets

## Architecture

See [`docs/architecture.md`](docs/architecture.md).

## Hackathon notes

See [`docs/hackathon.md`](docs/hackathon.md).

## Development landing page

The root [`index.html`](index.html) is a static development landing page. It is not a hosted functional MVP.

## License

MIT License. See [`LICENSE`](LICENSE).
