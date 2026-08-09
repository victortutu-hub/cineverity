# Director Agent Runtime v0.1 Specification

## 1. Purpose of Step 1.3

Phase 1 Step 1.3 implements the first operational CineVerity agent—the **Director Agent**—connecting Google Gemini via the Google Agent Development Kit (ADK) to the frozen `DirectorIntentContract` structured output boundary established in Steps 1.1 and 1.2.

This step proves that a live Gemini LLM response can cross the deterministic contract boundary and yield a fully validated `DirectorIntentContract` without violating physical truth boundaries or inventing ungrounded scientific facts.

---

## 2. Architecture & Execution Flow

```text
Creative Prompt (Artist Brief)
        |
        v
Google ADK Agent (`director_agent` via Gemini)
        |  (configured with output_schema=DirectorIntentContract)
        v
Model Event Stream (Raw Text Output)
        |  (extract_text_from_adk_events)
        v
Raw JSON String
        |  (DirectorIntentContract.model_validate_json)
Validated Cinematic Intent Contract
```

---

## 3. Google ADK Structured-Output Boundary

The Director Agent is defined using Google ADK's `Agent` class in `src/agents/director_agent.py`:

```python
director_agent = Agent(
    name="director_agent",
    model=os.getenv("CINEVERITY_GEMINI_MODEL", "gemini-3.5-flash"),
    description="CineVerity Director Agent interpreting creative briefs into structured intent contracts.",
    instruction=DIRECTOR_SYSTEM_INSTRUCTION,
    output_schema=DirectorIntentContract,
    tools=[],
)

director_app = agent_engines.AdkApp(agent=director_agent)
```

- **Output Schema**: Passing `output_schema=DirectorIntentContract` instructs Gemini at the API level to structure its response according to the JSON schema.
- **No Tools**: The Director Agent is strictly unequipped (`tools=[]`). It cannot execute code, make web searches, call external APIs, or render 3D scenes.

---

## 4. Why Dual Validation (ADK Schema + Pydantic Model Validation)?

Relying on LLM structured generation alone is insufficient for production agent systems:
1. LLM API schema enforcement guarantees top-level JSON formatting, but custom python-side constraints (such as cross-entity reference validation between `MaterialIntent.entity_id` and `SceneEntity.id`) require runtime execution.
2. Explicit deserialization via `DirectorIntentContract.model_validate_json()` enforces `extra="forbid"`, custom validators, and cross-reference integrity.

---

## 5. System Instruction Principles & Non-Invention Rules

The Director Agent's system instruction enforces 13 strict operational rules:

1. Preserve artistic intent above all else.
2. Strictly distinguish between Artist Intent, Physical Truth, and Current Knowledge.
3. Never turn a requested visual effect into a verified physical fact.
4. Never silently correct or alter an artistic request to fit real-world physics.
5. **Never invent** numeric refractive indices, dispersion coefficients, densities, wavelengths, physical constants, scientific evidence, or material properties not supplied by the user.
6. Unknown physical parameters belong in `MaterialIntent.unknown_parameters`.
7. Questions requiring external evidence belong in `research_required`.
8. Physical uncertainty or potential physical conflicts belong in `physical_questions` and/or `ambiguities`.
9. Aesthetic premises or non-physical requests belong in `artistic_freedoms`.
10. Explicit user requirements belong in `hard_constraints`.
11. Do not select Three.js, WebGPU, Blender, Unreal, GLSL, or any rendering engine unless explicitly requested by the user.
12. Do not perform research, browse the web, or claim physical correctness.
13. Produce only the structured output conforming to the required schema.

---

## 6. Failure Behavior

If raw model output fails Pydantic validation:
- The system raises a clear `ValueError` with detailed validation failure messages.
- **No automatic repair or silent muting** is performed in v0.1.
- **No automatic retries** are issued in v0.1.

---

## 7. How to Run Locally

### Required Environment Variables
Set the standard Google Cloud credentials established in Phase 0:

```bash
export GOOGLE_CLOUD_PROJECT="your-google-cloud-project-id"
export GOOGLE_GENAI_USE_ENTERPRISE="true"
export GOOGLE_CLOUD_LOCATION="us-central1" # Optional, defaults to global
export CINEVERITY_GEMINI_MODEL="gemini-3.5-flash" # Optional default
```

### Reference Live Test Run
Run the default reference prompt:

```bash
.venv\Scripts\python scripts/run_director_agent.py
```

Reference prompt:
> *"A transparent crystal monolith levitates above a dark basalt surface while three narrow colored lights pass through it, producing physically plausible internal refraction and caustics. The mood should feel alien but scientifically believable."*

### Adversarial Live Test Run
Run the preset adversarial prompt:

```bash
.venv\Scripts\python scripts/run_director_agent.py --adversarial
```

Adversarial prompt:
> *"Create a diamond where red light refracts twice as strongly as blue light. It must remain completely physically accurate."*

Expected adversarial behavior:
- Preserves requested custom dispersion behavior and physical accuracy requirement in intent fields.
- Flags the physical conflict in `physical_questions` / `ambiguities` with high/critical priority (`resolution="requires_validation"`).
- Does **not** claim the request is physically accurate.

---

## 8. Relationship to Future Agents

The validated `DirectorIntentContract` produced by the Director Agent will serve as the structured input for downstream agents in Phase 2:
- **Research Agent**: Will read `research_required` to perform targeted evidence lookups via the Parallel Search API.
- **Physical Constraints Agent**: Will evaluate `physical_questions` and `unknown_parameters` against evidence.
- **Scene Planning Agent**: Will convert `scene_entities` and `cinematic_intent` into spatial layout specifications.

---

## 9. Explicit Scope Exclusions

Step 1.3 explicitly does **NOT**:
- Perform external research or web searches.
- Call the Parallel Search API.
- Prove physical correctness or perform scientific simulation.
- Perform automatic LLM output repair or retries.
- Orchestrate multi-agent workflows.
- Render 3D images, videos, or geometry.
- Generate shaders or GLSL code.
- Select a rendering engine framework.
- Deploy agents to remote Google Cloud Agent Engine endpoints.
