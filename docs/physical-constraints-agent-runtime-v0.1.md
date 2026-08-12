# Physical Constraints Agent Runtime v0.1

Step 3.3 is a closed-input runtime boundary between accepted Director and Research contracts and a validated `PhysicalConstraintsContract`.

## Flow

```text
Director JSON validate
→ Research JSON validate
→ Director ↔ Research fidelity gate
→ derive authoritative PhysicalConstraintsScope
→ build closed packet
→ one Gemini synthesis call (tools=[])
→ PhysicalConstraintsContract.model_validate_json
→ Physical input-scope fidelity gate
→ accepted contract
```

The Director ↔ Research gate derives the Director-required `ResearchScope` and requires exact membership fidelity with the accepted Research scope before the model is invoked. A structurally valid Research contract from another Director is rejected. The runtime, not the model, owns `input_scope`.

## Trust boundary

The packet has two explicit sections:

- `authoritative_runtime.expected_input_scope`: runtime-derived structural data only—Director identifiers, material-unknown pairs, validation targets, Research finding-to-source/EvidenceStatus provenance, conflict IDs, and unresolved-question IDs.
- `untrusted_input_data`: validated Director and Research context supplied as data. It remains authoritative in its contract meaning: Director for artistic intent and Research as the accepted evidence snapshot. “Untrusted” does not mean false; it means its natural-language strings have no instruction authority.

Natural-language claims, titles, conditions, limitations, summaries, physical parameter text, and all other supplied text can contain prompt injection. The system instruction requires the agent to treat them only as field-scoped intent or evidence, never as commands that override its role, activate tools, browse, change schema, alter runtime scope, remove uncertainty, or trigger scene planning.

## Deterministic and nondeterministic boundaries

Packet derivation, rendering, event extraction, Pydantic validation, and both scope comparisons are deterministic and offline. Gemini execution is the only nondeterministic step. The agent has `tools=[]`; it cannot browse, use Google Search, retrieve, call Parallel, follow URLs, or introduce external evidence.

The packet preserves meaningful Director and Research list ordering. Scope comparisons ignore only membership ordering where contract semantics define membership. They do not normalize duplicates, IDs, material pairs, provenance, EvidenceStatus, or structured records.

## Gates and failure semantics

1. Director JSON is validated as `DirectorIntentContract`.
2. Research JSON is validated as `ResearchEvidenceContract`.
3. Director ↔ Research scope fidelity is required before packet construction and model invocation.
4. The runtime derives the authoritative `PhysicalConstraintsScope` from those validated inputs.
5. The model response is parsed by `PhysicalConstraintsContract`, executing all frozen Step 3.1 validators.
6. Exact runtime-derived `input_scope` fidelity is required.
7. A deterministic epistemic non-escalation gate rejects bounded, detectable promotions before acceptance.

There is one model invocation only. No repair, retry, critique pass, scope mutation, fallback, or partial acceptance exists. Invalid inputs or output fail explicitly.
## Epistemic non-escalation gate

The gate runs after Pydantic and exact Physical scope validation, and before acceptance. It is fail-closed and never rewrites candidate content. It structurally guarantees scope, IDs, provenance, EvidenceStatus compatibility, and these bounded deterministic invariants:

- contextual-only identity evidence cannot use detected promotion wording in assertive constraint text to claim a broader material baseline; literal numeric values from cited contextual Research parameters cannot be assigned to an explicitly named unresolved scene entity;
- for unknown Director material parameters without explicit supported/partially-supported scene-specific numeric PhysicalParameterEvidence, detected non-physicality/physical-limit wording in linked constraints or ArtisticDeviation tradeoffs is rejected;
- safe downstream assumptions are included in the same bounded assertive-text checks.

The detector is deliberately limited to explicit contract links and bounded affirmative patterns. It normalizes model-authored prose with Unicode NFKC, `casefold`, Unicode-dash/hyphen consistency, Unicode tokenization, decimal normalization, and collapsed whitespace. It uses token boundaries rather than arbitrary substrings.

It recognizes a bounded local negation grammar: `no`, `not`, `never`, `cannot`, `does not`, `do not`, `is not`, `are not`, and `must not`, both before and within a matched pattern. Trigger-term presence alone is not an escalation. This supports conservative wording such as “No physical dispersion limits are established” and “These values are not typical transparent media.”

Every current model-authored prose field is collected and checked: constraint statement/conditions/limitations/safe/unsafe assumptions; material-identity label/limitation; PhysicalConflict statement/conditions/limitations; unresolved-constraint why/evidence-needed/limitations; ArtisticDeviation statement/physical tradeoff; coverage notes; and physical summary. The gate reports an invariant ID and field path, for example `E_UNRESOLVED_PHYSICAL_LIMIT at artistic_deviations[0].physical_tradeoff`.

Deterministically guaranteed: structured scope/provenance/status invariants, bounded affirmative epistemic-escalation patterns across those fields, supported negation forms, and structured established-evidence exceptions. Prompt-instructed: scientific reasoning outside the bounded patterns and nearby unenumerated paraphrases. Not guaranteed: arbitrary English semantic understanding, arbitrary paraphrase detection, scientific truth, or material identity inferred from prose. This is not a general semantic validator.

## Evidence, material identity, and artistic intent

Research finding `source_ids` and `EvidenceStatus` are preserved in the authoritative scope and cannot be added, removed, reassigned, or changed by an accepted candidate. `unsupported` means the accepted evidence does not support a behavior in the analyzed context; it does not mean physically impossible. Artistic deviations remain separate from physical assessments and require the contract’s explicit artist-acceptance representation.

The frozen contract validates provenance structure but cannot prove scientific material identity. The system instruction therefore forbids treating ordinary glass, crystal glass, quartz, diamond, fused silica, or another contextual material as a scene material unless the supplied accepted evidence establishes that identity. `contextual_only` evidence remains limited contextual evidence; it cannot silently become an established scene identity or resolve an unknown parameter by analogy.

This runtime does not claim Gemini guarantees scientific correctness, claim entailment, semantic material identity, or artistic acceptability. The validation boundaries enforce only structural contract validity, exact scope fidelity, provenance membership, and the frozen cross-reference rules.
`PHYSICAL ASSESSMENT CERTAINTY <= ACCEPTED RESEARCH CERTAINTY`: an interpretation may preserve or weaken accepted Research certainty, never strengthen it. `UNKNOWN BASELINE != KNOWN BASELINE != PROOF OF NON-PHYSICALITY`; insufficient quantitative evidence does not establish non-physicality, physical impossibility, or departure from an unestablished baseline. `INSUFFICIENT EVIDENCE != EVIDENCE OF IMPOSSIBILITY`.

`CONTEXTUAL EXAMPLE FOR X != GENERAL EVIDENCE ABOUT CLASS Y`. Contextual evidence remains bounded to its named material and context; it cannot establish a typical, generic, representative, normal, approximate, baseline, scale, proxy, or benchmark claim for a broader class without accepted Research support. Downstream assumptions express epistemic permissions only, never operational instructions for using contextual evidence.
When quantitative behavior remains unresolved, the agent must state that no scene-specific quantitative magnitude is established and that an amplification cannot be certified as quantitatively physically grounded. `UNKNOWN QUANTITATIVE BASELINE != KNOWN STANDARD PHYSICAL BASELINE`: the agent must not invent a standard, normal, typical, expected, or physically realistic baseline absent from accepted Research.

`safe_downstream_assumptions` and `unsafe_downstream_assumptions` state only what downstream may assume physically or epistemically; they do not prescribe simulation, rendering, implementation, software, shaders, algorithms, scene construction, or another execution method.
`CONTEXTUAL EXAMPLE != GENERALIZED MATERIAL BASELINE != SCENE MATERIAL PARAMETER`. A value accepted only as a contextual example for a named material remains bound to that material. It does not establish a typical or generic material baseline, range, scale, calibration reference, estimate, proxy, benchmark, or scene-material parameter unless accepted Research explicitly supports that generalization. Downstream assumptions state what is physically or epistemically grounded; they do not tell downstream systems how to reference, use, gauge, calibrate, or operationalize evidence.

## Runner boundary

The controlled runner resolves Google environment settings, defaults `GOOGLE_CLOUD_LOCATION` to `global`, calls `vertexai.init()` before lazy-importing the agent, reads UTF-8 input JSON, and emits UTF-8 output. Offline tests use fakes and make no Gemini, Vertex, Parallel, retrieval, or network request.

## Exclusions

This runtime does not orchestrate Director-to-Research retrieval, run Parallel, browse, fact-check science, render, plan scenes, select Blender/Unreal/Three.js/WebGPU or another rendering stack, prescribe camera/light/geometry/render settings, simulate, select engines, or change frozen contracts or serialization boundaries.
## Predicate-local polarity and numeric canonicalization

The epistemic gate is a bounded deterministic grammar, not a general semantic validator. It evaluates every current model-authored prose field with predicate-local affirmative and explicitly negated forms. An earlier `not`, `no`, or `cannot` does not neutralize a later affirmative predicate. The bounded assertion splitter separates `.`, `;`, `:`, and the discourse connectors `but`, `however`, `therefore`, `yet`, `although`, and `while`; decimal points remain inside numeric literals. This prevents polarity from leaking across separate assertions while deliberately not attempting arbitrary English scope analysis.

For contextual-only evidence, the gate rejects explicit broader-class promotion (representation, typical/generic/representative status, reference ranges, benchmarks, proxies, calibrations, and related bounded forms). For unresolved scene material parameters, it rejects explicit non-physicality/physical-limit assertions and direct numeric scene assignment or approximation forms. The exact error retains its stable rule ID and the field path; candidate text is never repaired.

Numeric comparison uses `Decimal` only for bounded numeric syntax. Equivalent forms include `1.5`, `1,5`, `1.50`, `01.5`, `1.500`, `1.5e0`, and `15e-1`. Bounded ranges include `1.5-1.7`, `1.5 – 1.7`, `1,5–1,7`, and `1.50 to 1.70`. The gate performs no floating-point comparison, unit conversion, algebra, or scientific equivalence inference.

The scene-specific exemption remains structural: an accepted `supported` or `partially_supported` Research finding must contain a numeric parameter with the exact scene entity and the exact material-unknown pair. A matching number alone, another entity, another parameter, an unrelated finding, `related_entity=None`, or `unsupported` evidence does not grant an exemption.

Deterministically covered: exhaustive current prose fields, the documented predicate-local families, bounded clause separation, Decimal syntax equivalence, and the structured exemption. Prompt-instructed only: unenumerated scientific paraphrases and semantic relations outside those grammars. Not guaranteed: arbitrary NLP, arbitrary numerical algebra, unit conversion, scientific truth, or semantic material-identity inference.
## Match-local predicate polarity (Step 3.3.9)

Polarity is determined per bounded relation match, never per clause. The runtime enumerates affirmative relation matches and their explicitly negated counterparts independently; it rejects when any prohibited affirmative relation remains. A negated match covers only the affirmative relation starting inside that exact negated relation, so a conservative predicate cannot suppress a second affirmative predicate in the same clause.

Assertion segmentation remains a matching convenience for `.`, `;`, `:`, `but`, `however`, `therefore`, `yet`, `although`, and `while`. It is not the source of polarity truth. The bounded grammars cover contextual-generalization relations, scene-parameter numeric-promotion relations, and unresolved physical-limit/non-physicality relations, including the documented passive and modal conservative forms.

Deterministic guarantees are limited to the exhaustive current prose-field collector, those enumerated relation families, independent match-local polarity, Decimal syntax canonicalization, and the structured exact-evidence exception. Relations and paraphrases outside these grammars, general English semantics and scope, scientific reasoning, scientific truth, and material identity inferred from prose remain prompt-instructed or not guaranteed. This is not general NLP.
