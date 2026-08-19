# CineVerity — Architecture

## Purpose

CineVerity is an agentic technical-director system for cinema. It separates creative intent, external evidence, physical constraints, scene planning, and validation readiness so that creative freedom is preserved while technical claims, uncertainty, provenance, and artistic deviations remain explicit.

## Implemented specialist architecture

```text
Creative Brief
    ↓
Director Agent
    ↓
Research Retrieval
    ↓
Parallel Search API
    ↓
Gemini Research Synthesis
    ↓
Physical Constraints Agent
    ↓
Scene Planning Agent
    ↓
Validation Readiness Agent
```

These specialist stages and their controlled runners exist. This diagram does **not** represent one fully automated product pipeline: a single automatic end-to-end orchestrator across all stages does not exist yet.

## Contract → serialization → runtime

The mature stages follow a common boundary pattern:

```text
Frozen Pydantic contract
    ↓
Deterministic serialization boundary
    ↓
Agent/runtime boundary
    ↓
Validated candidate
```

Contracts define structural truth. Where a serialization boundary exists, JSON Schema is derived from the contract and canonical JSON provides a deterministic representation. Runtime code validates authoritative upstream inputs; model output is a candidate, not authority. Pydantic validation happens before runtime fidelity acceptance, and invalid output fails explicitly rather than being silently repaired.

## Acceptance and authority

**LLM generation is nondeterministic. Acceptance is deterministic.**

```text
validated upstream contracts
→ deterministic scope/fingerprint derivation where applicable
→ closed model packet
→ one model candidate
→ Pydantic validation
→ exact cross-contract provenance/scope fidelity gate
→ accept or explicit reject
```

The model does not own authoritative IDs, upstream scope, or runtime-derived fingerprints. Deterministic runtime code owns boundary acceptance. Runtime-owned SHA-256 snapshot fingerprints are implemented for Scene Planning and Validation Readiness; earlier stages use the scope/provenance mechanisms their boundaries define.

## Specialist stages

### Director

`DirectorIntentContract` is the structured interpretation boundary for a creative brief. It records creative intent and context, scene entities, physical questions, research requirements, material unknowns, and validation targets. The Director stage does not automatically orchestrate all downstream stages.

### Research retrieval and synthesis

Research has two separate responsibilities:

```text
Director research requirements
→ deterministic, bounded search planning
→ Parallel Search API runtime retrieval
→ provenance registry
→ Gemini Research synthesis
→ ResearchEvidenceContract
```

Parallel is used specifically for Research retrieval through the official SDK. Search planning is deterministic; external Parallel search results are not. Source identity and retrieval provenance are preserved, and Gemini synthesis must not fabricate provider provenance.

### Physical Constraints

The Physical Constraints runtime consumes validated Director and Research state. `PhysicalConstraintsContract` structures physical assessments (`supported`, `conditionally_supported`, `conflicting`, `unsupported`, and `indeterminate`), conflicts, unresolved physical constraints, artistic deviations, and evidence/provenance references.

Its epistemic boundary prevents structural escalation of unsupported, indeterminate, conditional, conflicting, or unresolved state. It does not independently prove arbitrary scientific truth and does not execute rendering or simulation.

### Scene Planning

Scene Planning bridges validated Director intent and Physical Constraints into a renderer-agnostic, production-oriented `ScenePlanningContract`. It has exact upstream fidelity gates, runtime-owned Director/Physical snapshot fingerprints, structured decisions, assignments, dependencies, validation hooks, and explicit artistic-deviation preservation.

It does not execute a renderer, select a shader/simulation engine, or claim renderer feasibility.

### Validation Readiness

**Validation Readiness** is structural preflight/readiness for future validation execution. It consumes Director, Physical Constraints, and Scene Planning, then derives authoritative scope and runtime-owned Director/Physical/Scene snapshot fingerprints from those validated inputs.

`ValidationReadinessContract` covers target and hook coverage, Physical subject readiness, dependency coverage/bindings, conflicts, unresolved constraints, and artistic deviations.

Validation Readiness is **not** an executed Validation Result. It does not mean rendering, simulation, measurement, or scientific validation occurred, and it has no PASS/FAIL execution result.

## Cross-contract fidelity and structured bindings

Individually valid documents are insufficient. For example:

```text
valid Director A + valid Physical B
```

must fail when Physical B belongs to Director B. Likewise, Director plus Physical must reject Scene Planning from another snapshot. Where implemented, runtime gates verify these pairings before downstream model invocation.

Provenance is not merely flat ID existence. Structured relationships remain intact, including:

```text
dependency ↔ validation hook ↔ physical subject ↔ Director validation target
```

A candidate with valid individual IDs but an invalid reassignment is rejected.

## Deterministic and nondeterministic boundaries

| Deterministic where implemented | Intentionally nondeterministic |
| --- | --- |
| Pydantic validation, canonical serialization, scope derivation, SHA-256 fingerprint derivation, provenance/fidelity gates, packet rendering, candidate acceptance/rejection, offline fake-runtime tests | Gemini generation; external Parallel Search results |

Research, Physical Constraints, Scene Planning, and Validation Readiness runtime boundaries use one model candidate per synthesis attempt. They do not perform automatic repair, hidden retry-to-fix, or a second semantic validation-model pass; an invalid candidate fails explicitly.

## Component map

```text
src/contracts/  authoritative structured contracts
schemas/        generated JSON Schema artifacts
src/agents/     Gemini / ADK specialist agents
src/services/   deterministic runtime, retrieval, provenance, and fidelity logic
scripts/        stage runners and schema exporters
tests/          offline structural, serialization, and adversarial tests
docs/           stage-specific contracts, boundaries, and runtime notes
```

The test architecture verifies contract invariants, deterministic serialization, provenance, wrong-snapshot and valid-ID/wrong-binding attacks, zero model calls on preflight failure, one-call/no-retry behavior, Unicode/byte determinism, and offline fake-app behavior.

## External runtime dependencies

The implemented runtime uses Gemini on Google Cloud / Vertex AI, Google ADK, and Parallel Search API for Research retrieval. Parallel is not attached to every stage. This architecture does not claim Agent Engine deployment, FastAPI, or other external AI providers.

## Frontend and deployment

`index.html` is a static development landing page, not the functional product UI. The public development landing page is deployed through GitHub Pages from `main` / `(root)`. A hosted functional MVP, complete production deployment, and end-to-end orchestration service remain future work.

A future UI may expose brief input, evidence, constraints, scene-plan state, readiness, uncertainty, and artistic deviations; those panels are not claimed as implemented product UI.

## Current non-goals

The current architecture intentionally does not attempt to generate a complete movie, replace artistic direction, implement a full renderer, execute full simulation or scientific measurement, claim scientific validation from readiness, automate an entire studio pipeline, or perform arbitrary semantic truth checking of free prose.

## Epistemic limits

**Structurally provable:** contract shape, references, provenance relationships, snapshot identity, structured status constraints, coverage, and allowed non-escalation invariants.

**Not proven automatically:** arbitrary natural-language semantic truth, scientific correctness beyond available evidence/contracts, renderer/simulation results, or measurements that were not executed.

## Detailed documentation

For boundary-level detail, see:

- [Director contract](director-agent-contract-v0.1.md), [serialization](director-serialization-boundary-v0.1.md), and [runtime](director-agent-runtime-v0.1.md)
- [Research contract](research-agent-contract-v0.1.md), [serialization](research-serialization-boundary-v0.1.md), [retrieval](research-retrieval-runtime-v0.1.md), and [runtime](research-agent-runtime-v0.1.md)
- [Physical Constraints contract](physical-constraints-contract-v0.1.md), [serialization](physical-constraints-serialization-boundary-v0.1.md), and [runtime](physical-constraints-agent-runtime-v0.1.md)
- [Scene Planning contract](scene-planning-contract-v0.1.md), [serialization](scene-planning-serialization-boundary-v0.1.md), and [runtime](scene-planning-agent-runtime-v0.1.md)
- [Validation Readiness contract](validation-readiness-contract-v0.1.md), [serialization](validation-readiness-serialization-boundary-v0.1.md), and [runtime](validation-readiness-agent-runtime-v0.1.md)

## Architecture principle

**Scientific grounding should constrain the technical explanation, not suffocate the artistic decision.**
