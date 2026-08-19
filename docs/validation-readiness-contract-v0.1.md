# Validation Readiness Contract v0.1

## Boundary

`ValidationReadinessContract` is a deterministic contract/preflight boundary. It describes readiness to validate a supplied `DirectorIntentContract`, `PhysicalConstraintsContract`, and `ScenePlanningContract`; it never represents renderer, simulation, measurement, scientific testing, or external verification as executed.

Research is not a direct input. Research-derived provenance may remain transitively inside the accepted Physical Constraints snapshot, but this contract neither reopens nor reinterprets Research.

## Readiness is not execution

Readiness states are `structurally_checkable`, `ready_for_execution`, `blocked`, and `cannot_validate_yet`. Execution states are only `not_required`, `not_executed`, and `unavailable`. There is deliberately no executed pass/fail state in v0.1.

The contract preserves authoritative Director validation targets, Scene Planning hooks and dependencies, Physical constraints/conflicts/unresolved records, and artistic deviations. Each scoped target, hook, and Physical subject requires exactly one readiness record. Hooks remain checks to perform, not evidence that they happened.
Every authoritative Scene Planning dependency receives exactly one `dependency_coverage` record. A Scene Planning dependency has a typed subject and reason, but no authoritative satisfied, blocking, or execution status; Validation Readiness therefore does not invent one. Its coverage preserves only the exact dependency ID and the validation-hook bindings that Scene Planning already encodes. Dependency presence alone does not force a record to be blocked.

`scene_validation_hook_references` preserve the actual target/constraint/conflict/unresolved/deviation/dependency links encoded by Scene Planning hooks. A target or Physical subject readiness record may use a hook only when that exact binding exists in scope. Step 5.1 cannot infer relationships that Scene Planning does not encode, including arbitrary prose, scene semantics, or execution completion.

## Scope and future runtime

`input_scope` contains only IDs, structured references, and shape-validated SHA-256 fields for the Director, Physical Constraints, and Scene Planning snapshots. Step 5.1 does not derive hashes or compare snapshots. A future Step 5.3 runtime must derive all fingerprints and scope records independently from validated upstream contracts, reject mismatches before a model call, and require exact candidate scope fidelity.

## Non-escalation

Internal validators prevent unsupported/indeterminate constraints, unresolved constraints, unresolved conflicts, conditional constraints, and artistic deviations requiring acceptance from becoming validation-ready. Artist acceptance is not represented as accepted because v0.1 has no authoritative acceptance source.

Pydantic cannot prove arbitrary prose entailment. It guarantees only typed states, local references, exhaustive coverage, and the listed structural non-escalation rules. It does not prove science, renderer output, simulation, measurement, cinematic quality, or that any external validation was executed.

## Out of scope

No Gemini, ADK, Vertex, Parallel, retrieval, network, renderer, Blender, Unreal, WebGPU, shader, simulation, image analysis, measurement, or runtime/agent/runner/schema work belongs to Step 5.1.
