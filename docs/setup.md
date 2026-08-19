# CineVerity — Setup and Local Execution

## What this guide covers

This guide explains how to install, authenticate, test, and manually run CineVerity's current specialist stages. It does not describe a hosted deployment, renderer, simulation system, or automatic end-to-end orchestrator.

## Verified Python version

**Verified development/runtime environment: Python 3.11.9.**

No formal supported Python version range is declared yet. This guide does not claim compatibility with other Python versions.

## Prerequisites

- Git
- Python 3.11.9 (verified)
- A Google Cloud project with billing enabled as required by the current Google setup
- Google Cloud CLI (`gcloud`) for local Application Default Credentials (ADC)
- Vertex AI API: `aiplatform.googleapis.com`
- A Parallel API key for the live Research retrieval stage

The current local workflow does not require a service-account JSON file, FastAPI, Docker, Node.js, a renderer, or simulation software.

## Clone and create a virtual environment

```text
git clone https://github.com/victortutu-hub/cineverity.git
cd cineverity
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

POSIX shell:

```bash
python -m venv .venv
source .venv/bin/activate
```

The code uses portable Python paths where possible, but each operating system has not been independently tested.

For the documented Windows artifact-redirection workflow, use PowerShell 7 / PowerShell Core; it was verified with PowerShell 7.6.4. Windows PowerShell 5.1 is not verified for this workflow: its `>` behavior may write text with an encoding incompatible with the UTF-8 JSON artifacts expected by downstream CineVerity runners.

## Install dependencies

Runtime only:

```text
python -m pip install -r requirements.txt
```

Development and offline tests:

```text
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` includes the runtime requirements. JSON Schema exporters are developer-maintenance tools; they are not required to operate the current specialist stages.

## Google Cloud authentication

Use local Application Default Credentials:

```text
gcloud auth application-default login
```

Enable the Vertex AI API for your project:

```text
gcloud services enable aiplatform.googleapis.com --project YOUR_PROJECT_ID
```

No service-account JSON file is required for local development. Never commit credentials.

## Environment variables

CineVerity does **not** automatically load `.env`. [`.env.example`](../.env.example) is a reference template only; set the variables in your shell.

- `GOOGLE_CLOUD_PROJECT` — required for Google/Gemini stage runners. There is no developer-project fallback.
- `GOOGLE_CLOUD_LOCATION` — defaults to `global` where supported by the current runners.
- `GOOGLE_GENAI_USE_ENTERPRISE` — must be truthy, normally `True`.
- `CINEVERITY_GEMINI_MODEL` — defaults to `gemini-3.5-flash`.
- `PARALLEL_API_KEY` — secret, required for Research retrieval only. It is not required for offline tests or stages that do not call Parallel directly.

Windows PowerShell:

```powershell
$env:GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
$env:GOOGLE_CLOUD_LOCATION="global"
$env:GOOGLE_GENAI_USE_ENTERPRISE="True"
$env:CINEVERITY_GEMINI_MODEL="gemini-3.5-flash"
$env:PARALLEL_API_KEY="YOUR_PARALLEL_API_KEY"
```

POSIX shell:

```bash
export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
export GOOGLE_CLOUD_LOCATION="global"
export GOOGLE_GENAI_USE_ENTERPRISE="True"
export CINEVERITY_GEMINI_MODEL="gemini-3.5-flash"
export PARALLEL_API_KEY="YOUR_PARALLEL_API_KEY"
```

Do not commit real API keys or credentials.

## Offline tests

```text
python -m pytest -q
```

The verified offline suite does not require Google Cloud or Parallel credentials. It uses fake applications and adapters at runtime boundaries; it does not make live Google or Parallel API calls.

## Live Google smoke tests

These are live Google Cloud/Gemini calls, separate from offline tests:

```text
python scripts/hello_gemini.py
python scripts/run_hello_agent.py
```

They require valid ADC, `GOOGLE_CLOUD_PROJECT`, and the Google Cloud configuration above.

## Manual specialist workflow

```text
creative brief
    ↓
director.json
    ↓
research.json
    ↓
physical.json
    ↓
scene.json
    ↓
validation-readiness.json
```

This is a manual, stage-by-stage workflow. A single automatic end-to-end orchestrator is not implemented yet.

### 1. Director

One-line portable example:

```text
python scripts/run_director_agent.py --prompt "A transparent crystal monolith levitates above a dark basalt surface while narrow colored lights pass through it." --output director.json
```

The runner keeps human-readable status on stdout. Use `--output`: it writes only accepted `DirectorIntentContract` JSON to `director.json`, after contract validation succeeds. Director does not automatically trigger Research.

### 2. Research

```text
python scripts/run_research_agent.py --director-contract director.json > research.json
```

Research performs deterministic, bounded search planning, live Parallel Search API retrieval, and Gemini research synthesis. It requires both Google Cloud/Gemini configuration and `PARALLEL_API_KEY`. `research.json` is the accepted `ResearchEvidenceContract`. External search results are not deterministic.

### 3. Physical Constraints

```text
python scripts/run_physical_constraints_agent.py --director-contract director.json --research-contract research.json > physical.json
```

`physical.json` is the accepted `PhysicalConstraintsContract`. This is a live Gemini synthesis stage; it does not execute simulation or scientific measurement.

### 4. Scene Planning

```text
python scripts/run_scene_planning_agent.py --director-contract director.json --physical-constraints-contract physical.json > scene.json
```

`scene.json` is the accepted `ScenePlanningContract`. It is renderer-agnostic planning and does not execute a renderer.

### 5. Validation Readiness

```text
python scripts/run_validation_readiness_agent.py --director-contract director.json --physical-constraints-contract physical.json --scene-planning-contract scene.json > validation-readiness.json
```

`validation-readiness.json` is the accepted `ValidationReadinessContract`.

**Validation Readiness is structural preflight/readiness. It is not executed renderer validation, simulation, measurement, or scientific PASS/FAIL.**

## Output and redirection

Do not use `python scripts/run_director_agent.py > director.json`: Director stdout includes human-readable status. Use `--output director.json` instead.

On their successful paths, Research, Physical Constraints, Scene Planning, and Validation Readiness emit accepted contract JSON to stdout, so their output can be redirected to the next artifact file. Errors and failures are not valid contract artifacts.

Shell redirection may create or truncate the destination before a runner completes. A file named `research.json`, `physical.json`, `scene.json`, or `validation-readiness.json` is not proof that its stage succeeded: use it downstream only after the runner exits successfully. A failed command may leave an empty, partial, or otherwise invalid file; downstream validation will reject it, but do not intentionally continue after a failed stage. In PowerShell, check `$LASTEXITCODE`; in POSIX shells, check the command exit status.

## Network boundary

Offline `python -m pytest -q` does not use live Google or Parallel APIs.

The hello scripts and specialist stage runners use live Google Cloud/Gemini. Research additionally uses the Parallel Search API.

## Troubleshooting

- **`GOOGLE_CLOUD_PROJECT must be set.`** Set the project variable before running a Google stage.
- **`PARALLEL_API_KEY must be set for Parallel Search.`** Set the key before running Research retrieval.
- **ADC/authentication error.** Run `gcloud auth application-default login` and check your project/API configuration.
- **`GOOGLE_GENAI_USE_ENTERPRISE must be True.`** Set it to a truthy value such as `True`.
- **Invalid downstream contract.** Do not manually alter IDs, fingerprints, or scope between stages; fidelity gates intentionally reject mismatched snapshots.

## Security

Never commit:

- Parallel API keys
- Google credentials
- service-account JSON files
- `.env` files with real secrets

The repository provides [`.env.example`](../.env.example) only as a placeholder reference.
