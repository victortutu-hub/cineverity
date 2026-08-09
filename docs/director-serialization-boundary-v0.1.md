# Director Agent Serialization Boundary v0.1 Specification

## 1. Purpose of Step 1.2

The purpose of Phase 1 Step 1.2 is to establish a deterministic, portable, and machine-readable JSON Schema and serialization boundary for `DirectorIntentContract` v0.1.

This step decouples data contract definition from downstream consumers, language-specific frameworks, and external LLM APIs by providing canonical schema export, JSON serialization/deserialization semantics, and round-trip validation guarantees.

---

## 2. Pydantic Model as Single Source of Truth

The Python Pydantic v2 class `DirectorIntentContract` defined in `src/contracts/director_intent.py` is the single source of truth for the Director Agent v0.1 data model.

The JSON Schema artifact (`schemas/director-intent-contract-v0.1.schema.json`) is **not** manually authored or maintained independently. It is programmatically derived directly from `DirectorIntentContract.model_json_schema()`.

---

## 3. JSON Schema Artifact

### Location
`schemas/director-intent-contract-v0.1.schema.json`

### Canonical Serialization Strategy
To guarantee byte-for-byte determinism across different runs, environments, and machines, the schema artifact is generated using the following explicit canonical formatting rule:

```python
canonical_json = (
    json.dumps(
        DirectorIntentContract.model_json_schema(),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    + "\n"
)
```

### Export Script
The export process is automated via:
`scripts/export_director_schema.py`

Running this script repeatedly produces byte-identical output.

---

## 4. Serialization and Deserialization Workflows

### Serialization Flow
1. **Python Model -> JSON Primitives**:
   `data_dict = contract.model_dump(mode="json")`
   Produces JSON-safe Python primitives (`dict`, `list`, `str`, `int`, `float`, `bool`, `None`).

2. **Python Model -> JSON String**:
   `json_str = contract.model_dump_json()`
   Produces a valid UTF-8 JSON string representation.

### Deserialization Flow
1. **JSON String -> Validated Model**:
   `contract = DirectorIntentContract.model_validate_json(json_str)`

2. **JSON Dictionary -> Validated Model**:
   `contract = DirectorIntentContract.model_validate(data_dict)`

Both deserialization pathways run full validation, including:
- Type checking and strict field constraints (`extra="forbid"`).
- Enumeration value validation (`RealityMode`, `Priority`, `AmbiguityResolution`).
- Cross-entity reference integrity checks via `@model_validator(mode="after")`.

---

## 5. Round-Trip Guarantee

The serialization boundary guarantees semantic equality across round-trip transformations:

```text
DirectorIntentContract
        |
        v  (model_dump_json)
    JSON String
        |
        v  (model_validate_json)
DirectorIntentContract
```

For any valid contract `C`:
`DirectorIntentContract.model_validate_json(C.model_dump_json()) == C`

Deserialization retains all validated data, constraint types, and entity relationship structures without silent loss or corruption.

---

## 6. Intended Future Agent Structured Output Boundary

In future steps, the LLM-driven Director Agent (e.g., powered by Gemini) will operate within this exact boundary:

```text
Creative Prompt (Artist Input)
        |
        v
  Director Agent (LLM Execution)
        |
        v
Structured JSON Output
        |
        v  (DirectorIntentContract.model_validate_json)
Validated CineVerity Contract
        |
        v
Downstream Agents (Research, Physical Constraints, Scene Planning, Validation)
```

By establishing this boundary in Step 1.2, downstream agents can rely on a strict, portable contract regardless of how the structured JSON is generated.

---

## 7. Scope Boundaries & Disclaimers

### What Step 1.2 Proves
- Schema generation determinism and export pipeline.
- JSON serialization (`model_dump`, `model_dump_json`) correctness.
- JSON deserialization and strict validation (`model_validate_json`).
- Round-trip semantic equality.
- Checked-in schema artifact alignment.

### What Step 1.2 Does NOT Prove or Perform
Step 1.2 explicitly does **NOT**:
- Call Gemini or Google Cloud APIs.
- Validate Gemini structured output.
- Implement Director Agent execution logic.
- Validate physical truth or optics laws.
- Perform research or search calls.
- Call the Parallel Search API.
- Call Google ADK tools.
- Make any network requests.
- Render 3D scenes, geometry, or shaders.
