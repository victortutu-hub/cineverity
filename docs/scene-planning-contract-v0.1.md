# Scene Planning Contract v0.1

## Boundary

`ScenePlanningContract` converts accepted `DirectorIntentContract` plus `PhysicalConstraintsContract` into renderer-agnostic production planning. Research is deliberately excluded: Scene Planning consumes the accepted physical interpretation and never reinterprets raw evidence.

## Structural guarantees

The contract is strict (`extra="forbid"`), preserves exact scoped IDs and typed links, rejects duplicate/blank membership, and distinguishes physically grounded decisions, implementation choices, artistic realizations, and unresolved handling. `grounding_constraint_ids` and `constraining_constraint_ids` are intentionally distinct: implementable does not mean physically required.

`director_contract_sha256` and `physical_constraints_contract_sha256` must be lowercase 64-character SHA-256 hex strings. Step 4.1 verifies shape only. A future runtime must derive canonical upstream hashes, validate Director-to-Physical fidelity, derive the exact scope, and reject mismatches before model invocation.

## Values and material safety

Concrete parameter values are typed as numeric, categorical, descriptive, boolean, or unresolved. Numeric values use finite `Decimal` syntax; no unit conversion, algebra, or scientific validation occurs. No parameter assignment can claim `physically_grounded`. A Director-declared material unknown cannot become an ordinary implementation value: it remains unresolved, provisional with an explicit typed dependency, or an explicitly linked artistic realization.

Material plans use `established`, `unresolved_abstract`, or `provisional_placeholder`. Established identity requires the exact scoped established label and a grounding constraint. Contextual or unresolved identities cannot become established through planning prose.

## Dependencies, deviations, validation and coverage

Dependencies are one-way typed links for unresolved constraints, physical conflicts, material identity uncertainty, artist acceptance, or artist decisions. Committed decisions cannot have dependencies. Artistic deviations have exactly one realization and preserve ID, type, entity binding, and explicit-acceptance requirement.

Validation hooks are checks, not validation results. Coverage is exact for scoped constraints, conflicts, unresolved constraints, and artistic deviations; it must cite related decisions, dependencies, and hooks rather than unrelated valid IDs.

## Limits and execution

The contract does not prove scientific correctness, prose entailment, artistic quality, or that a constraint semantically requires a camera, light, geometry, or implementation decision. It is renderer/engine agnostic: no Blender, Unreal, Three.js, WebGPU, shaders, or engine settings belong here. Those choices belong to a later execution/adapter layer.
## Structural hardening

All scope membership collections reject blank and duplicate entries before any set/map membership check. TemporalBeat IDs are globally unique across the contract. Conflicting established material labels for the same scene entity fail closed.

Future runtime flow is: validate Director; validate Physical Constraints; verify exact Director-owned fields in Physical input scope (questions, requirements, entities, material-unknown pairs, validation targets); derive scope and canonical fingerprints; then invoke the model. Step 4.1 validates fingerprint shape only, not upstream ownership.
