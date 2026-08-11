# Research Agent Runtime v0.1

Step 2.3B separates retrieval from synthesis and physical interpretation. Parallel is the sole retrieval provider in v0.1; Gemini sees a closed deterministic snapshot and has `tools=[]`.

## Closed synthesis packet

The packet separates `trusted_runtime` (scope, Director research context, searches, and exact allowed-source metadata) from `untrusted_provider_content` (source occurrence excerpts). Provider titles are authoritative metadata that must be copied exactly when a source is emitted, but title text and excerpts are untrusted data and never instructions.

Packet lists are deterministic: Director context preserves Director order, searches preserve registry execution order, sources are sorted by source ID, and occurrences are sorted by requirement, search ID, rank, and retrieval time. Unicode is preserved by canonical JSON rendering.

## Three gates

1. Pydantic parses `ResearchEvidenceContract`.
2. Exact semantic scope membership is compared against `derive_research_scope(director)` without order sensitivity.
3. Retrieval provenance validates source metadata and requirement-to-source retrieval occurrence links.

There is no repair or retry. Zero-evidence searches remain in the packet; synthesis must produce complete unresolved/partially-addressed coverage without fabricated evidence.

## Limits

Provenance proves retrieval and metadata, not semantic claim-to-excerpt entailment. A future Physical Constraints Agent owns physical interpretation and final verdicts. This runtime does not browse, follow URLs, call other retrieval tools, resolve scientific truth, or perform scene planning.
