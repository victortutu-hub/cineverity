# Director Agent Contract v0.1 Specification

## 1. Purpose

The Director Agent Contract v0.1 defines the deterministic schema boundary for interpreting high-level creative prompts into structured cinematic intent within CineVerity.

The core goal of Director Agent v0.1 is to parse artistic directives into an explicit, machine-readable format (`DirectorIntentContract`) without guessing physical values, resolving technical ambiguities, or modifying the artist's original creative intent.

---

## 2. Artist Intent vs Physical Truth vs Current Knowledge

CineVerity enforces a fundamental architectural boundary between three categories of information:

1. **WHAT THE ARTIST WANTS (Creative Intent)**
   - The artistic vision, aesthetic goals, mood, style, and artistic overrides requested by the user.
   - A requested artistic effect must **never** automatically become a verified physical claim.

2. **WHAT PHYSICS ALLOWS (Physical Truth)**
   - Scientific laws, empirical properties, and physical constraints validated by reference data or simulation.
   - A potential physical contradiction must **never** silently erase or rewrite the artist's intention.

3. **WHAT THE SYSTEM CURRENTLY KNOWS (Current Knowledge)**
   - Verified facts, pending research requirements, physical questions, and unresolved ambiguities tracked by the pipeline.

Director Agent v0.1 operates strictly at the boundary of **Artist Intent** and **Current Knowledge identification**. It captures artistic desires and surfaces technical questions without asserting physical truth.

---

## 3. Input Contract

The input to the future Director Agent v0.1 is a simple JSON object containing a raw creative prompt:

```json
{
  "creative_prompt": "string"
}
```

---

## 4. Output Contract

The output produced by Director Agent v0.1 is a validated Pydantic model (`DirectorIntentContract`) adhering to the following structure:

### Required Top-Level Fields

- `contract_version`: Must be `"0.1"`.
- `agent`: Must be `"director_agent"`.
- `creative_intent`: Core idea, desired emotions, visual priorities, and reality mode.
- `scene_entities`: Identified objects, surfaces, and participants in the scene.
- `material_intent`: Material families, desired visual properties, and unknown parameters.
- `lighting_intent`: Light sources, visual roles, color intent, and interaction targets.
- `environment_intent`: Setting, surface details, atmosphere, background priority, and environmental effects.
- `cinematic_intent`: Visual style, camera, motion, timing, and framing requirements.
- `physical_questions`: Domain-specific physical questions raised by the creative brief.
- `research_required`: Topics requiring external evidence or scientific lookup.
- `artistic_freedoms`: Aesthetic decisions explicitly unconstrained by physical realism.
- `hard_constraints`: Absolute non-negotiable visual requirements specified by the artist.
- `ambiguities`: Unclear prompt details categorized by resolution strategy.
- `validation_targets`: Downstream validation goals for checking scene consistency.
- `director_summary`: Concise technical summary of the intent interpretation.

---

## 5. Reality Modes

The contract categorizes the scene's relationship to physical reality using four explicit modes (`RealityMode`):

1. `strict_physical`: Every visual element must strictly adhere to real-world physics.
2. `physically_grounded_artistic`: Physical grounding is preferred, but artistic direction takes priority where specified.
3. `speculative_but_coherent`: Elements may be physically speculative or sci-fi, but must remain internally self-consistent.
4. `explicitly_nonphysical`: The scene intentionally violates physical laws for artistic expression (e.g., surrealism or stylized animation).

---

## 6. Required Behavior

Director Agent v0.1 must:

- Structurally parse the creative prompt into all required fields of `DirectorIntentContract`.
- Assign unique identifiers (`id`) to all entities, lighting elements, questions, research requirements, ambiguities, and validation targets.
- Explicitly catalog missing or unknown physical parameters in `MaterialIntent.unknown_parameters`.
- Formulate explicit physical questions in `physical_questions` whenever a requested visual behavior requires physical verification.
- Maintain reference integrity across entities, materials, lights, and physical questions.
- Preserve artistic overrides explicitly within `artistic_freedoms`.

---

## 7. Forbidden Behavior

Director Agent v0.1 must **NOT**:

- Browse the web or make external network requests.
- Call the Parallel Search API or external search services.
- Invent physical constants (e.g., arbitrary density, mass, or speed of light).
- Invent refractive indices or material dispersion coefficients.
- Generate shaders, GLSL code, HLSL code, or material nodes.
- Generate 3D geometry, meshes, or scene graphs.
- Render images, frames, or video clips.
- Perform physical simulations (e.g., ray tracing, fluid dynamics, stress analysis).
- Validate physical correctness or perform scientific proof checking.
- Silently correct or alter artistic requests to match real-world physics.
- Prematurely select execution targets, render engines, or frameworks (e.g., Three.js, WebGPU, Blender, Unreal Engine, GLSL).

---

## 8. Artistic Override Principle

If an artist requests a visual effect that conflicts with known physical laws, the system must:

1. **Capture the artistic request as visual intent** in `creative_intent`, `material_intent`, or `artistic_freedoms`.
2. **Flag the physical query** in `physical_questions` with a high or critical priority.
3. **Never silently alter or "fix" the prompt** to fit real-world physics.

Artistic direction is sovereign. Physical validation agents downstream will analyze feasibility and highlight trade-offs, but Director Agent v0.1 never erases artistic choice.

---

## 9. Reference Test Case

### Prompt
> "A transparent crystal monolith levitates above a dark basalt surface while three narrow colored lights pass through it, producing physically plausible internal refraction and caustics. The mood should feel alien but scientifically believable."

### Required Schema Representation
- **Entities**: Monolith (`transparent crystal`), Surface (`dark basalt`).
- **Preserved Elements**:
  - Transparent crystal monolith
  - Levitation
  - Basalt surface
  - Three colored lights
  - Internal refraction
  - Caustics
  - Alien mood
  - Scientific believability
- **Forbidden Inventions**:
  - Must **NOT** invent specific refractive indices (e.g., specifying `IOR = 1.54` without evidence).
  - Must **NOT** invent exact crystal chemical compositions.
  - Must **NOT** invent unsupported physical constants.
- **Questions & Research**: Must record unknown refractive index and dispersion properties as items in `MaterialIntent.unknown_parameters` and `physical_questions`.

---

## 10. Adversarial Test Case

### Prompt
> "Create a diamond where red light refracts twice as strongly as blue light. It must remain completely physically accurate."

### Required Schema Representation & Handling
- **Preserved Elements**:
  - Diamond entity.
  - Requested red/blue dispersion behavior (red refracting twice as strongly as blue light).
  - Request for complete physical accuracy.
- **System Handling**:
  - The potential conflict between requested dispersion and physical accuracy must **NOT** result in silently changing the prompt (e.g., "correcting" it to real diamond dispersion where blue light refracts more than red).
  - The contract must record the requested behavior under `creative_intent` / `material_intent` / `artistic_freedoms`.
  - The potential physical conflict must be recorded as a critical `PhysicalQuestion` and/or `Ambiguity` (e.g., resolution: `requires_validation` or `defer_to_research_or_user`).

---

## 11. Downstream Relationship

The `DirectorIntentContract` serves as the single source of intent truth for all subsequent agents in the CineVerity pipeline:

```text
DirectorIntentContract
        |
        +--> Research Agent (queries external evidence for research_required)
        |
        +--> Physical Constraints Agent (evaluates physical_questions and unknown parameters)
        |
        +--> Scene Planning Agent (translates scene_entities and cinematic_intent into spatial layout)
        |
        +--> Validation Agent (validates constraints against validation_targets without violating artistic_freedoms)
```

---

## 12. Success Criterion

Phase 1 Step 1.1 is successful when:

1. `DirectorIntentContract` strictly validates all input data using Pydantic v2.
2. Invalid cross-entity references (e.g., material pointing to non-existent entity ID) are deterministically rejected with validation errors.
3. Unknown fields, invalid version strings, or invalid agent identifiers are rejected.
4. Unit tests pass cleanly without invoking external APIs, web searches, or render tools.
