# Research Agent Contract v0.1

## Purpose

`ResearchEvidenceContract` is the deterministic output boundary for the future CineVerity Research Agent. It records normalized sources, source-linked findings, conflicts, unresolved questions, and complete coverage of Director research requirements.

The boundary is deliberate:

```text
source != claim != physical verdict
```

A source record is provenance metadata. A finding is a claim that explicitly names its supporting source IDs. Neither is a final statement about physical feasibility; that work belongs to the future Physical Constraints Agent.

## Provenance and findings

Every supported, partially supported, or conflicting finding must reference one or more known sources. Unsupported and insufficient-evidence findings may remain source-free to make an evidence gap explicit. URLs are optional source metadata and are never treated as proof by themselves.

Findings may refer to Director research requirements, physical questions, scene entities, and material unknowns. Material unknowns use the stable `(entity_id, parameter)` identity pair rather than invented IDs.

## Physical parameters

`PhysicalParameterEvidence` preserves `value_text`, unit, conditions, uncertainty, related entity, and source IDs. `value_text` deliberately accommodates ranges, inequalities, functions, and non-scalar reported values without converting them into unsupported floats.

## Conflicts and unresolved research

Conflicts retain all referenced findings and sources. A conflict requires at least two distinct evidence references and is never silently reconciled. Unresolved questions record the missing evidence and priority without declaring a physical verdict.

Every Director research requirement declared in `ResearchScope` has exactly one `ResearchCoverage` entry: `addressed`, `partially_addressed`, or `unresolved`. This distinguishes a deliberate unresolved result from omitted reporting.

## Pipeline relationship

The future orchestration layer will derive `ResearchScope` from `DirectorIntentContract`. A future Parallel integration may populate this contract, but is outside v0.1. A future Physical Constraints Agent will consume these structured records to determine whether evidence is supported, unsupported, conditional, contradictory, or unknown.

## Scope exclusions

This contract contains no Research Agent runtime, Gemini call, Parallel client, network operation, scientific semantic validation, scene plan, or physical feasibility verdict. Pydantic validates identifiers and provenance structure only.
