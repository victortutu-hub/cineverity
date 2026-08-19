# Validation Readiness Agent Runtime v0.1

## Boundary

Phase 5 Step 5.3 is a closed-input preflight transformation:

```text
DirectorIntentContract + PhysicalConstraintsContract + ScenePlanningContract
→ ValidationReadinessContract
```

It is not executed validation. No renderer, simulation, measurement, scientific verification, PASS/FAIL executor, or external validation runs in this step.

## Exact upstream chain

The runtime validates Director and Physical Constraints, applies the existing exact Director ↔ Physical gate, validates Scene Planning, then applies the existing exact Director + Physical ↔ Scene Planning scope/fingerprint gate. A mismatched upstream snapshot fails before packet construction or model invocation.

## Runtime-owned scope and fingerprints

`ValidationReadinessScope` is derived exclusively by the runtime from the three validated snapshots. It preserves ordered Director IDs, Physical status/reference bindings, Scene Planning hooks, dependencies, and dependency ↔ hook bindings. Scene Planning provides no authoritative dependency satisfied/unsatisfied/blocking state, so the runtime never invents one.

Each complete validated snapshot is fingerprinted with UTF-8 SHA-256 over:

```python
json.dumps(contract.model_dump(mode="json"), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
```

The final LF is hashed. Lists keep their original order; only object keys are sorted. Raw file bytes, stdout, packet text, schemas, and model output are never hash inputs.

## Packet and model boundary

```json
{
  "authoritative_runtime": {"expected_input_scope": {}},
  "validated_context": {"director": {}, "physical_constraints": {}, "scene_planning": {}}
}
```

Contexts are `model_dump(mode="json")` outputs from validated objects, never raw JSON. Natural-language context is data, not instructions. The agent uses `tools=[]`, has no Research input, and cannot browse, retrieve, call Parallel, follow URLs, or acquire external evidence.

There is exactly one ADK model call. Thought and metadata-only events are ignored; non-thought text fragments are concatenated in stream order. Empty usable text, malformed JSON, validation failure, or scope mismatch fails explicitly. There is no retry, repair, fallback, critique, or partial acceptance.

## Acceptance and non-escalation

Candidate JSON is first parsed with `ValidationReadinessContract.model_validate_json()`, then its `input_scope` must equal the independently derived runtime scope exactly. This makes fingerprints, statuses, artist-acceptance flags, hooks, dependencies, and structured bindings runtime-authoritative.

Frozen Pydantic validators guarantee typed readiness/execution states, exhaustive coverage, local cross-references, and structural ceilings for unsupported, indeterminate, conditional, conflicting, unresolved, and acceptance-required subjects. Runtime fidelity guarantees the candidate belongs to the supplied snapshots.

Arbitrary prose entailment remains outside v0.1: no NLP/LLM semantic gate proves every sentence. The instruction forbids claims that execution occurred, and the contract has no executed result state, but the runtime does not claim general prose-level scientific or execution verification.

## Runner and offline verification

The runner accepts `--director-contract`, `--physical-constraints-contract`, and `--scene-planning-contract`; reads UTF-8; resolves environment defaults; calls `vertexai.init()` before importing the agent; and emits accepted UTF-8 JSON. Automated tests use fake apps only and cover canonical hashes, Unicode, pre-model zero-call failures, wrong snapshots, exact scope fidelity, event extraction, one-call behavior, and runner import order. No live Gemini, Vertex, Parallel, retrieval, or network call is required for the offline suite.
