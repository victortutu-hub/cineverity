# Validation Readiness Serialization Boundary v0.1

Phase 5 Step 5.2 provides deterministic serialization for `ValidationReadinessContract`. The frozen Pydantic contract remains the semantic source of truth. The checked-in schema is generated only from `ValidationReadinessContract.model_json_schema()`; it is never manually maintained.

## Canonical representations

Canonical contract JSON is `json.dumps(contract.model_dump(mode="json"), indent=2, sort_keys=True, ensure_ascii=False) + "\n"`. Canonical schema text uses the identical options over `model_json_schema()`. Object keys are sorted; lists are never sorted, deduplicated, normalized, repaired, or semantically reinterpreted.

The exporter writes `canonical_schema_text().encode("utf-8")` through `write_bytes()`. The artifact is UTF-8 without BOM, literal LF-only, and exactly one final LF. Tests compare `read_bytes()` with expected bytes independently constructed from `model_json_schema()`; this remains authoritative despite Windows text translation or Git autocrlf behavior.

## Round-trip and validation

`model_dump(mode="json")` and `model_dump_json()` are JSON-safe and require no custom serializer. Both canonical JSON and `model_dump_json()` round-trip through `model_validate_json()`, which reruns strict coverage, dependency propagation, hook/subject/target bindings, conflict/unresolved handling, artistic-acceptance, duplicate/blank, and non-escalation validators.

Dependency references, dependency coverage, hook bindings, Physical references, and artist-acceptance requirements are ordinary nested contract data and survive serialization exactly. Serialization does not repair invalid references or make candidate scope authoritative.

## Scope limits

The three SHA fields are shape-only in Steps 5.1 and 5.2. Step 5.3 must derive authoritative Director, Physical Constraints, and Scene Planning fingerprints and require exact upstream snapshot fidelity. This boundary neither establishes that fidelity nor executes validation, rendering, simulation, measurement, scientific testing, Gemini, ADK, Vertex, Parallel, retrieval, network access, runtime, or repair/retry logic.
