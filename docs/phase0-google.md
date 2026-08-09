# CineVerity — Phase 0: Google Infrastructure

## Goal

Prove the minimum Google-native execution path before any CineVerity product logic is added.

Success means:

1. a dedicated Google Cloud project exists with billing enabled;
2. the Agent Platform API is enabled;
3. local development uses Application Default Credentials (ADC);
4. Python can call Gemini through Google Cloud;
5. Google ADK can run the first CineVerity agent locally;
6. no OpenAI, Anthropic, or other non-Google AI runtime dependency exists.

## Phase 0 execution chain

```text
Local CineVerity repository
        |
        v
Application Default Credentials
        |
        v
Google Cloud project
        |
        v
Agent Platform API
        |
        +--> Google Gen AI SDK --> Gemini
        |
        +--> Google ADK --------> First CineVerity Agent
```

## Required Google Cloud API

For the first local tests:

- `aiplatform.googleapis.com`

Cloud Storage and deployment APIs are intentionally deferred until deployment work begins.

## Authentication policy

Local development uses:

```text
gcloud auth application-default login
```

No service-account JSON key is required for Phase 0.

For production, CineVerity should use an attached Google Cloud identity rather than committing credential files.

## Environment

```text
GOOGLE_CLOUD_PROJECT=<project-id>
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_ENTERPRISE=True
CINEVERITY_GEMINI_MODEL=gemini-3.5-flash
```

## Test 1 — Hello Gemini

Run:

```text
python scripts/hello_gemini.py
```

Success criterion:

- the script prints a Gemini response;
- the script ends with `[OK] Gemini request completed successfully through Google Cloud.`

## Test 2 — First ADK agent

Run:

```text
python scripts/run_hello_agent.py
```

Success criterion:

- ADK produces agent events/responses;
- the process ends with `[OK] ADK agent execution completed.`

## What Phase 0 does NOT include

- Parallel Search API;
- FastAPI application endpoints;
- multi-agent orchestration;
- CineVerity scene schemas;
- Cloud Run deployment;
- Agent Runtime deployment;
- UI integration.

Those are later phases. Phase 0 exists only to prove the Google-native foundation first.
