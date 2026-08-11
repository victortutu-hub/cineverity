# Research Retrieval Runtime v0.1

Phase 2 Step 2.3A integrates only the official Parallel Search SDK. It performs no Gemini synthesis and does not construct `ResearchEvidenceContract` or coverage.

## Bounded search

The runtime creates exactly one `SearchPlan` per Director research requirement, with exactly two deterministic queries. It accepts at most five requirements, uses `mode="advanced"` and `max_chars_total=10000`, and performs no retry, broadening, or iterative loop.

## Registry and source identity

Parallel responses are preserved as execution records. Eligible results require provider URL and title. Canonical sources are deduplicated by a conservative normalized URL and use `source_<20 lowercase SHA-256 hex characters>`. Every duplicate result appends an occurrence retaining requirement ID, search ID, session ID, excerpts, rank, and UTC retrieval time.

Normalization trims surrounding whitespace, lowercases scheme/hostname, removes fragments and default ports, removes `utm_*`, `gclid`, and `fbclid`, and sorts remaining query parameters. It preserves path case, trailing slashes, and semantic query values.

## Provenance gate

The gate prepares the future Step 2.3B boundary. It rejects any source not retrieved by Parallel or any mutation of ID, URL, title, publication date, accessed time, publisher, or source type. Provider URL/title/date are authoritative; publisher is `None`, source type is `other`, and accessed time is runtime UTC.

This step makes no network calls in tests, performs no scientific validation, and does not invoke Gemini or produce physical verdicts.
## Pre-live integrity invariants

Every provider result remains in `RetrievedSearch.raw_results`, including malformed or incomplete results. Only HTTP(S) results with a hostname and nonblank title are promoted into canonical evidence records.

A canonical source records `first_retrieved_at_utc`; later duplicate retrievals add occurrences without changing that timestamp. The provenance gate uses this explicit first timestamp and also verifies that each sourced finding has retrieval occurrence coverage for every Director research requirement it claims to address.
