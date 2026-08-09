# CineVerity — Initial Architecture

## 1. Purpose

CineVerity is being designed as an **agentic technical-director system for cinema**.

The central architectural requirement is that creative intent, external evidence, physical constraints, production planning, and validation remain **separate but connected stages**.

This separation is deliberate:

- it reduces the chance that generated technical claims are mistaken for verified facts;
- it makes uncertainty visible;
- it allows artistic departures from physical realism to remain explicit;
- it gives the project an auditable reasoning structure.

## 2. High-level flow

```text
Creative Scene Brief
        |
        v
  Director Agent
        |
        +--> Research Agent --> Parallel Search API
        |
        +--> Physical Constraints Agent
        |
        +--> Scene Planning Agent
        |
        +--> Validation Agent
        |
        v
Evidence-grounded Production Output
```

## 3. Intended agent responsibilities

### Director Agent
- interpret the filmmaker's brief;
- identify technical subproblems;
- coordinate specialist stages;
- preserve artistic intention;
- aggregate results without erasing uncertainty.

### Research Agent
- formulate research queries from the scene brief;
- use the selected partner integration at runtime;
- collect source material;
- preserve provenance.

Current hackathon direction: **Parallel Search API**.

### Physical Constraints Agent
Potential domains include optics, materials, lighting, atmosphere, scale, timing, and simulation assumptions.

Each constraint should distinguish between evidence-supported values, approximations, artistic overrides, and unknowns.

### Scene Planning Agent
- convert constraints into a structured production plan;
- preserve units and assumptions;
- avoid unnecessary renderer lock-in.

### Validation Agent
- detect contradictions;
- identify unsupported claims;
- expose uncertainty;
- identify conflicts between artistic goals and physical behavior.

## 4. Initial data contracts

### Scene brief

```json
{
  "title": "Macro crystal shot",
  "intent": "A rotating crystal illuminated by three colored lights",
  "visual_goals": ["strong internal refraction", "visible spectral dispersion"],
  "constraints": {},
  "target": {"format": "cinematic"}
}
```

### Evidence item

```json
{
  "claim": "Example technical claim",
  "source_url": "https://example.com",
  "source_title": "Example source",
  "retrieved_at": "ISO-8601",
  "confidence": 0.0
}
```

### Constraint item

```json
{
  "domain": "optics",
  "parameter": "refractive_index",
  "value": null,
  "unit": null,
  "status": "unknown",
  "evidence_refs": [],
  "artistic_override": false
}
```

## 5. Backend direction

Planned responsibilities:

- API endpoints for scene briefs and workflow execution;
- orchestration invocation;
- Gemini access through approved Google Cloud infrastructure;
- Parallel Search API runtime calls;
- provenance handling;
- schema validation;
- errors and partial-result reporting.

Candidate framework: **FastAPI**.

## 6. Frontend direction

Potential panels:

1. Scene Brief
2. Agent Timeline
3. Evidence
4. Physical Constraints
5. Scene Plan
6. Validation
7. Artistic Overrides

The UI should visually distinguish verified/evidence-grounded output, inference, uncertainty, and artistic override.

## 7. Deployment direction

Planned:

- public web interface;
- backend on Google Cloud;
- secrets stored outside the repository;
- public GitHub repository for judging;
- temporary GitHub Pages landing page during early development.

## 8. Non-goals for the first MVP

The first MVP does not need to generate a complete movie, replace DCC tools, implement a full renderer, or automate an entire studio pipeline.

It should prove this reasoning loop:

```text
intent → research → evidence → constraints → scene plan → validation
```

## 9. Architecture principle

**Scientific grounding should constrain the technical explanation, not suffocate the artistic decision.**
