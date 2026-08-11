# Research Serialization Boundary v0.1

## Purpose

Phase 2 Step 2.2 establishes the deterministic, portable serialization boundary for `ResearchEvidenceContract`. The frozen Pydantic model remains the single source of truth; the checked-in JSON Schema is generated from `ResearchEvidenceContract.model_json_schema()` and is never manually maintained.

## Canonical schema

`scripts/export_research_schema.py` writes `schemas/research-evidence-contract-v0.1.schema.json` using:

```python
json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
```

This produces stable key ordering, UTF-8 text, and exactly one trailing newline. Repeated generation is byte-identical.

## Serialization and validation

`contract.model_dump(mode="json")` produces JSON-safe primitives. `contract.model_dump_json()` produces a JSON string. `ResearchEvidenceContract.model_validate()` and `model_validate_json()` reconstruct a validated contract and execute every custom validator again: source provenance, Director scope references, material unknown pairs, physical-parameter source subsets, conflicts, and complete coverage.

The round-trip guarantee is:

```text
ResearchEvidenceContract.model_validate_json(C.model_dump_json()) == C
```

Source provenance, date and timezone-aware datetime metadata, conditions, limitations, and non-scalar `PhysicalParameterEvidence.value_text` are preserved through this boundary.

## Future relationship and exclusions

A future Research Agent runtime and Parallel integration may emit this portable JSON, while the future Physical Constraints Agent may consume it. Step 2.2 does not perform research, call Parallel or Gemini, validate scientific truth, resolve conflicts, produce physical verdicts, orchestrate agents, or make network requests.
