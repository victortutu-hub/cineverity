# CineVerity — Hackathon Development & Submission Notes

## Event and target

**Agentic Cinema: The Blockbuster Hackathon — 2026**

Submission deadline: **September 7, 2026 at 2:00 PM PDT**.

CineVerity is a new project created during the contest period and targets the **Parallel** partner track.

## Current product boundary

Implemented specialist workflow stages:

```text
Creative Intent
→ Director
→ Parallel Research Retrieval
→ Gemini Research Synthesis
→ Physical Constraints
→ Scene Planning
→ Validation Readiness
```

The repository contains controlled runners for these stages, not one complete automatic orchestration layer across the full flow.

Not implemented as a complete product flow:

- single automatic end-to-end orchestration;
- hosted functional MVP;
- executed renderer, simulation, measurement, or scientific validation.

**Validation Readiness Agent** is structural preflight/readiness only. It does not mean renderer, simulation, measurement, or scientific validation has been executed.

## Partner-track implementation

Parallel Search API is actively used for Research retrieval through the official Python SDK. Search planning is deterministic and bounded; external search results are not claimed to be deterministic. The Research retrieval boundary preserves retrieved source identity and provenance for downstream synthesis.

Parallel is not used by every agent. It is the runtime retrieval component for the Research stage.

## Agentic functionality

- [x] Gemini integration
- [x] Google Cloud / ADK agent runtime
- [x] Director Agent
- [x] Research Agent
- [x] Parallel Search API runtime integration
- [x] Gemini research synthesis
- [x] Physical Constraints Agent
- [x] Scene Planning Agent
- [x] Validation Readiness Agent
- [ ] Full automatic end-to-end orchestration

## Submission requirements to track

The submitted project must be a functional AI agent or multi-agent system powered by Gemini and approved Google Cloud agent tooling, with active runtime use of the selected Partner service. It must run on at least one supported platform (web, Android, or iOS), be newly created during the contest period, and be public/open source with the source code, assets, and instructions needed to run the project.

The submission also requires a hosted Project URL and a public YouTube or Vimeo demo video. The video should be no longer than 3 minutes; if longer, only the first 3 minutes are evaluated. Submission material must be in English or include English subtitles where applicable. Runtime AI use is limited to Google Cloud AI tooling and the selected Partner product's permitted built-in AI capabilities.

### Repository

- [x] Public repository
- [x] MIT/open-source license
- [x] Initial README
- [x] Architecture notes
- [x] Development landing page
- [x] Functional source code
- [x] Environment-variable template with names/placeholders only
- [x] Automated tests
- [x] Complete setup/run instructions
- [ ] Final architecture diagram or visual

### Hosted project

- [x] Static development landing page prepared
- [x] GitHub Pages activated/verified
- [ ] Functional MVP deployed
- [ ] Final hosted Project URL verified

### Final submission evidence

Implementation exists in code for Google Cloud runtime and Parallel Search API retrieval. Final live demo/submission evidence is still to be prepared.

- [ ] Hosted functional Project URL
- [x] Complete setup/run instructions
- [ ] Final architecture diagram or visual
- [ ] Screenshots
- [ ] Final demo scenario
- [ ] Public YouTube/Vimeo demo video (≤3 minutes)
- [ ] English narration/subtitles as needed
- [ ] Final project description, findings, and learnings
- [ ] Final Devpost submission
- [ ] Runtime demonstration of Google Cloud
- [ ] Runtime demonstration of Parallel Search API

## Runtime compliance

Current runtime AI architecture uses Gemini on Google Cloud, Google ADK and Google Cloud runtime tooling, and Parallel Search API for the selected partner track. The runtime does not claim use of other AI providers.

## Candidate demo scenario

> Create a macro cinematic shot of a rotating crystal illuminated by three colored lights, with strong internal refraction and visible spectral dispersion.

This remains a candidate demo scenario, not a limitation of CineVerity and not a claim that the final demo has been recorded.

## Development transparency and guardrails

Keep the distinction between **implemented** and **in progress / required for submission** explicit.

1. Never commit API keys or credentials.
2. Claim only technology present in the working implementation.
3. Keep Parallel runtime integration observable in the live demo path.
4. Preserve research provenance when it affects downstream recommendations.
5. Keep artistic deviations explicit.
6. Distinguish readiness from executed validation.
7. Preserve the project's independent, new-project history.
