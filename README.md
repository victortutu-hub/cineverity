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

Each stage has a controlled runtime and validated contract boundary. The hosted application now coordinates these stages automatically through a FastAPI NDJSON API and the functional frontend under `src/frontend/`.

**Validation Readiness Agent** is preflight/readiness only. It does not mean rendering, simulation, measurement, scientific validation, or any other validation execution has occurred.

## Implemented today

- Director structured intent contract, schema boundary, and Gemini/ADK runtime.
- Research Evidence contract, bounded Parallel Search API retrieval with deterministic search planning, Gemini research synthesis, and provenance preservation.
- Physical Constraints contract, canonical serialization boundary, closed-input runtime, and cross-contract fidelity gates.
- Scene Planning contract, canonical serialization boundary, closed-input runtime, and runtime-owned canonical SHA-256 snapshot fingerprints.
- Validation Readiness contract, canonical serialization boundary, and closed-input preflight runtime.
- Deterministic cross-contract scope/fingerprint derivation, exact candidate fidelity checks, and offline automated tests.
- Deterministic hosted orchestration, a FastAPI NDJSON API, timeout/cancellation hardening, and a no-build hosted frontend.
- Docker runtime packaging with a digest-pinned Python base, exact-version runtime lock, bounded build context, and a non-root single-worker startup contract.

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
- FastAPI and Uvicorn
- HTML, CSS, and JavaScript hosted frontend

## Planned / deployment direction

- Cloud Run deployment services
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
- [x] Hosted orchestration and functional frontend
- [x] Docker runtime packaging
- [ ] Cloud Run deployment
- [ ] Executed renderer/simulation/measurement validation
- [ ] Demo and final submission assets

## Architecture

See [`docs/architecture.md`](docs/architecture.md).

## Hackathon notes

See [`docs/hackathon.md`](docs/hackathon.md).

## Development landing page

The root [`index.html`](index.html) is a static GitHub Pages development landing page. The hosted functional frontend is under `src/frontend/` and is served by FastAPI; Cloud Run deployment remains future work.

## License

MIT License. See [`LICENSE`](LICENSE).
