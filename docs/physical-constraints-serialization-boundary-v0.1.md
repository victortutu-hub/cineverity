# Physical Constraints Serialization Boundary v0.1

## Purpose

Phase 3 Step 3.2 provides the deterministic serialization boundary for `PhysicalConstraintsContract`. The frozen Pydantic model is the single source of truth. The JSON Schema artifact is generated from `PhysicalConstraintsContract.model_json_schema()` and is never manually maintained.

## Canonical schema

`scripts/export_physical_constraints_schema.py` writes `schemas/physical-constraints-contract-v0.1.schema.json` with:

```python
json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
```

The exporter writes `canonical_schema_text().encode("utf-8")` with `write_bytes()`. The artifact therefore has UTF-8 bytes, no BOM, LF-only line endings, sorted object keys, stable indentation, and exactly one trailing LF. Repeated export is byte-identical. Git newline normalization is repository configuration outside this boundary; exported artifact bytes and the independent byte comparison are authoritative.

## Canonical contract JSON

For a validated contract, canonical JSON is defined as:

```python
json.dumps(
    contract.model_dump(mode="json"),
    indent=2,
    sort_keys=True,
    ensure_ascii=False,
) + "\n"
```

Object keys are sorted; list order is preserved. Unicode is emitted directly, with no ASCII escaping, semantic normalization, repair, reinterpretation, or mutation.

## Validation and round-trip

`model_dump(mode="json")` produces JSON-safe primitives. Both canonical JSON and `model_dump_json()` can be passed to `PhysicalConstraintsContract.model_validate_json()`, which reconstructs the model and reruns all Step 3.1 structural validators: coverage alignment, closed scope references, material-identity provenance, and conservative evidence-status guards.

```text
PhysicalConstraintsContract
→ JSON
→ model_validate_json
→ semantically equal PhysicalConstraintsContract
```

## Scope exclusions

Step 3.2 contains no Physical Constraints Agent runtime, input-scope derivation, semantic-fidelity gate, Gemini, ADK, Vertex, Parallel, network access, retrieval, scene planning, rendering, simulation, or scientific interpretation logic.