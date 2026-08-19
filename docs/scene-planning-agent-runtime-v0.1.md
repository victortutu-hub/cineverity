# Scene Planning Agent Runtime v0.1

## Purpose and boundary

Phase 4 Step 4.3 provides a bounded runtime transformation:

```text
DirectorIntentContract + PhysicalConstraintsContract
→ ScenePlanningContract
```

`ResearchEvidenceContract` is not a direct Scene Planning input. The complete accepted `PhysicalConstraintsContract` can contain frozen Research-derived traceability, such as finding provenance, finding IDs, source IDs, and conflict/unresolved IDs. This remains inert Physical Constraints data: Scene Planning neither strips it nor reinterprets it as direct Research evidence.

## Pipeline

```text
Director JSON → DirectorIntentContract validation
Physical Constraints JSON → PhysicalConstraintsContract validation
→ Director ↔ Physical fidelity gate
→ canonical Director SHA-256 + canonical Physical SHA-256
→ deterministic ScenePlanningScope derivation
→ trust-separated packet
→ exactly one model invocation
→ non-thought response extraction
→ ScenePlanningContract.model_validate_json()
→ exact candidate.input_scope fidelity
→ accept / reject
```

There is no retry, repair, fallback model, second planning pass, or partial acceptance.

## Director ↔ Physical fidelity and order

The preflight compares the five Director-owned Physical scope collections: physical questions, research requirements, scene entities, material-unknown `(entity_id, parameter)` pairs, and validation targets. It rejects blank or duplicate identifiers/pairs before comparison. Comparison is exact membership and order-insensitive; sorting exists only as a comparison representation.

This deliberately differs from the two later order rules:

- `ScenePlanningScope` derivation preserves validated authoritative upstream order.
- Candidate `input_scope` fidelity is exact structural equality and therefore order-sensitive.

These rules are not contradictory: preflight confirms that Physical is paired with the supplied Director, while the runtime-derived scope fixes the authoritative ordered snapshot that the model must reproduce.

## Canonical fingerprints

The runtime fingerprints validated upstream snapshots with:

```python
json.dumps(
    contract.model_dump(mode="json"),
    indent=2,
    sort_keys=True,
    ensure_ascii=False,
) + "\n"
```

The text is encoded as UTF-8 and passed to SHA-256 `hexdigest()`. It does not hash raw file bytes, raw JSON formatting, `model_dump_json()`, runner stdout, packet rendering, or JSON Schema.

The fingerprint binds Scene Planning output to the exact validated Director or Physical snapshot supplied to this runtime. It does not prove historical authorship, that a Physical file was originally produced by Phase 3, or provenance authentication; v0.1 has no signatures.

## Deterministic expected scope

The runtime owns all of `ScenePlanningScope`. Director supplies its fingerprint, ordered entity IDs, validation-target IDs, physical-question IDs, and ordered material-unknown pairs. Physical Constraints supplies its fingerprint plus ordered PhysicalConstraint, PhysicalConflict, unresolved, and artistic-deviation references.

Material identities flatten deterministically in Physical constraint order, then material-identity order within each constraint. There is no sorting, merging, deduplication, semantic inference, or direct Research access.

## Trust-separated packet

```json
{
  "authoritative_runtime": {
    "expected_input_scope": {}
  },
  "untrusted_input_data": {
    "director_context": {},
    "physical_constraints_context": {}
  }
}
```

Only `authoritative_runtime.expected_input_scope` is runtime authority. Everything under `untrusted_input_data` is complete validated context whose natural-language strings are data, never instructions. Such strings may contain prompt injection, renderer instructions, fake SHA values, tool requests, or requests to modify IDs; expected scope remains independently derived.

The packet has no direct `ResearchEvidenceContract`, `research_context`, Parallel retrieval, new source access, or new Research synthesis. Nested Research-derived traceability inside the complete Physical contract remains allowed and inert.

## Model configuration and transport

The agent is `scene_planning_agent`, uses `CINEVERITY_GEMINI_MODEL` with default `gemini-3.5-flash`, has `ScenePlanningContract` output schema, `tools=[]`, and is wrapped in ADK `AdkApp`.

Each valid synthesis attempt has exactly one `async_stream_query` call. Thought chunks and metadata-only parts are ignored; non-thought text chunks are concatenated in stream order, then stripped once. No usable text raises `ValueError`. Malformed JSON is not repaired; `ScenePlanningContract.model_validate_json()` owns structural candidate parsing.

## Output fidelity and planning boundary

Candidate acceptance requires:

```text
candidate.input_scope == derive_scene_planning_scope(actual Director, actual Physical)
```

This catches wrong fingerprints, reordered authoritative lists, missing/extra IDs or references, changed constraint status, changed conflict resolution, altered unresolved references, artistic acceptance flags, and material-identity status/labels. There is no subset acceptance, membership approximation, normalization, or repair.

The frozen contract preserves:

```text
PHYSICAL CONSTRAINT != SCENE IMPLEMENTATION CHOICE != ARTISTIC DEVIATION != UNRESOLVED DEPENDENCY
IMPLEMENTABLE != PHYSICALLY REQUIRED
```

Every `implementation_choice` requires a non-empty `basis.implementation_rationale`. The rationale explains why the implementation decision was selected; it does not convert that discretionary choice into a physically required fact. `IMPLEMENTATION RATIONALE != PHYSICAL GROUNDING`.

Director material-unknown pairs cannot become ordinary implementation facts. Established identity exists only when the exact accepted Physical identity establishes it; `contextual_only` and `unresolved` cannot become established. Artistic realization remains distinct from physical grounding. Validation hooks are planned checks, not assertions that validation succeeded, physics is proven, renderer output is correct, or cinematic quality is achieved.

## Renderer boundary

Scene Planning v0.1 is renderer and engine agnostic. Renderer adapters, Blender, Unreal, Three.js, WebGPU, shader implementation, engine commands, and simulation execution belong to later layers. This is prompt discipline, not a broad lexical engine-name validator.

## Runner

The controlled runner accepts:

```text
--director-contract PATH
--physical-constraints-contract PATH
```

There is no `--research-contract`. `GOOGLE_CLOUD_PROJECT` is required and has no developer-specific default. Defaults are `GOOGLE_CLOUD_LOCATION=global`, `GOOGLE_GENAI_USE_ENTERPRISE=True`, and `CINEVERITY_GEMINI_MODEL=gemini-3.5-flash`.

Its order is environment resolution, `vertexai.init`, enterprise check, lazy imports, UTF-8 reads, `validate_runtime_inputs`, `synthesize_scene_planning`, then accepted JSON on stdout. Output uses `model_dump_json(indent=2)` and UTF-8 stdout. Runner stdout JSON is not canonical fingerprint bytes and is never hashed.

## Call-count security properties

- Invalid or mismatched upstream input: zero model calls.
- Valid upstream input: exactly one maximum model call.
- Invalid model output, wrong output scope, or empty response: one call then reject.
- No failure creates a second model call.

## v0.1 limitations and exclusions

This boundary provides bounded structural and runtime integrity, not scientific semantic correctness, prose entailment, artistic/cinematic quality, semantic necessity of camera/light/geometry, arbitrary parameter/category correctness, renderer feasibility, historical cryptographic origin, general prompt-injection immunity, or semantic interpretation of Research provenance.

Out of scope are direct Research reinterpretation, Parallel/retrieval, new evidence acquisition, scientific re-evaluation, renderer adapters, execution plans, shaders, simulation, iterative planning, multi-agent debate, retry/repair loops, and arbitrary semantic NLP policing.
