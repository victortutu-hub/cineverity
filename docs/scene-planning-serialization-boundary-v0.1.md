# Scene Planning Serialization Boundary v0.1

## Purpose

Phase 4 Step 4.2 provides the deterministic serialization boundary for `ScenePlanningContract`. It mirrors the frozen Research and Physical Constraints serialization boundaries. The frozen Pydantic contract remains the single source of truth; its checked-in JSON Schema is generated from `ScenePlanningContract.model_json_schema()` and is never manually maintained.

## Canonical schema

`scripts/export_scene_planning_schema.py` renders the schema with:

```python
json.dumps(
    ScenePlanningContract.model_json_schema(),
    indent=2,
    sort_keys=True,
    ensure_ascii=False,
) + "\n"
```

The exporter writes `canonical_schema_text().encode("utf-8")` through `write_bytes()`. The artifact consequently has UTF-8 bytes without a BOM, LF-only line endings, sorted object keys, two-space indentation, and exactly one trailing LF. Repeated export is byte-identical.

## Canonical contract JSON

For an already validated contract, canonical data JSON is:

```python
json.dumps(
    contract.model_dump(mode="json"),
    indent=2,
    sort_keys=True,
    ensure_ascii=False,
) + "\n"
```

Object keys are sorted, but every list remains in the exact contract order. This includes `input_scope` membership lists, decisions, assignments, material plans, dependencies, artistic-deviation realizations, shots, temporal beats, validation hooks, coverage, and nested membership lists. Serialization never sorts or deduplicates list content.

Unicode is emitted literally in UTF-8 without ASCII escaping, mojibake repair, Unicode normalization, or string mutation. `SceneParameterValue.numeric_value` is a validated string and retains its lexical form exactly: for example, `"1.5"`, `"1.50"`, `"01.5"`, and `"1.5e0"` remain distinct. The two upstream SHA-256 fields are likewise preserved exactly; Step 4.2 neither derives fingerprints nor verifies their ownership.

## Validation and round-trip

`model_dump(mode="json")` supplies JSON-safe Pydantic data. `model_dump_json()` is used only for semantic round-trip validation, not as canonical bytes. `ScenePlanningContract.model_validate()` and `model_validate_json()` reconstruct a strict validated contract and rerun all frozen Scene Planning validators, including cross-references, coverage, dependency, scope, material-identity, and decision constraints.

There is no repair, retry, field dropping, normalization, or fallback:

```text
ScenePlanningContract
→ canonical JSON / UTF-8 bytes
→ ScenePlanningContract.model_validate_json()
→ semantically equal contract
```

Step 4.3 owns upstream fingerprint derivation and ownership verification. This boundary serializes only the already validated Scene Planning contract and does not change Scene Planning semantics, invoke runtime agents, or perform Gemini, ADK, Vertex, Parallel, retrieval, network, rendering, or simulation work.
