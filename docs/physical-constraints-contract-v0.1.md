# Physical Constraints Contract v0.1

## Purpose

`PhysicalConstraintsContract` is the deterministic boundary that interprets an accepted `DirectorIntentContract` and `ResearchEvidenceContract` into physically relevant constraints for downstream use. It preserves the distinction:

```text
SOURCE != CLAIM != MATERIAL IDENTITY != PHYSICAL ASSESSMENT != ARTISTIC DEVIATION
```

It does not retrieve evidence, decide scientific truth beyond the accepted evidence, choose material identity silently, plan a scene, select rendering technology, or rewrite the artistic request.

## Authoritative input scope

`input_scope` is an authoritative snapshot of the identifiers available to this result: Director physical questions, research requirements, scene entities, material-unknown pairs, validation targets, and minimal Research finding provenance. The provenance projection contains only each `finding_id`, its `source_ids`, and frozen Research `evidence_status`; it does not duplicate Research claims.

Step 3.1 validates internal consistency against this declared snapshot. A later Step 3.3 runtime gate must derive the expected scope from the actual Director and Research contracts and require exact semantic fidelity. Step 3.1 does not perform that input-fidelity comparison.

## Assessments and coverage

`PhysicalAssessmentStatus` describes the physical interpretation of an individual constraint:

- `supported`
- `conditionally_supported`
- `conflicting`
- `unsupported`
- `indeterminate`

`PhysicalQuestionCoverageState` is deliberately separate. It reports whether a Director physical question is `addressed`, `partially_addressed`, or `unresolved`.

`unsupported` does not mean physically impossible. It means the currently accepted evidence does not support the behavior for the analyzed context. `indeterminate` means the accepted evidence is insufficient to decide.

Every scoped Director physical question has exactly one coverage record. Every linked constraint, unresolved record, and artistic deviation must address that same physical question. Research coverage remains owned by `ResearchEvidenceContract` and its research requirements.

## Provenance

A constraint may only cite Research findings present in `input_scope`. Its source IDs are constrained by:

```text
constraint.source_ids
⊆ union(source_ids of cited Research findings)
```

Nested material-identity source IDs must also remain within their parent constraint source IDs. `supported` requires at least one supported Research finding; `conditionally_supported` requires at least one supported or partially supported finding; `unsupported` requires a cited finding but may be source-free; `indeterminate` may remain finding-free and source-free. These are epistemic/reference guards, not scientific entailment or truth validation.

## Material identity

`MaterialIdentityReference` records whether evidence identity is established for a scene entity, unresolved, or contextual only.

- `established_for_scene_entity` requires an `identity_label` and Research provenance.
- `contextual_only` requires an `identity_label`, Research provenance, and a limitation. It may reference an unresolved scene material parameter, but must not semantically resolve or assign it merely by analogy; that discipline belongs to the future Physical Constraints Agent/runtime.
- `unresolved` has no `identity_label`.

`identity_label` is descriptive, provenance-bound text rather than a new stable identifier. Material-specific evidence is never transferred to another scene material without evidence establishing identity.

## Artistic deviations

`ArtisticDeviation` records an intentional departure separately from a physical assessment. It cites the relevant Director physical questions and existing constraints, states the physical trade-off, and exposes `requires_explicit_artist_acceptance`. It does not silently reject or repair the artistic request.

## Scope exclusions

This contract contains no Gemini runtime, Parallel retrieval, network call, JSON Schema export, physical simulation, scientific constants, new measurements, rendering choice, shader, geometry, camera placement, or scene plan. Pydantic validates closed-scope structural and provenance integrity only.