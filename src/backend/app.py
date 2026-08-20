"""FastAPI/NDJSON adapter for the deterministic hosted CineVerity pipeline."""

from __future__ import annotations

import asyncio
import json
import threading
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

from src.backend.bootstrap import HostedRuntimeBootstrapError, HostedRuntimeProvider
from src.backend.orchestrator import HostedStageError, HostedRuntimeDependencies, run_hosted_pipeline


class RunRequest(BaseModel):
    """Backend-owned browser request shape; not a CineVerity contract."""

    model_config = ConfigDict(extra="forbid")

    brief: StrictStr = Field(max_length=6000)

    @field_validator("brief")
    @classmethod
    def require_nonblank_brief(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("brief must not be blank")
        return value


class ProcessRunGate:
    """Single-process demo permit; intentionally not distributed coordination."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active = False

    def try_acquire(self) -> bool:
        with self._lock:
            if self._active:
                return False
            self._active = True
            return True

    def release(self) -> None:
        with self._lock:
            self._active = False


PipelineCallable = Callable[
    [str, HostedRuntimeDependencies, Any], Awaitable[Any]
]


def _ndjson(event: dict[str, Any]) -> bytes:
    return (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


async def _run_with_owned_gate(
    gate: ProcessRunGate,
    operation: Callable[[], Awaitable[None]],
) -> None:
    """The independent pipeline task, not the client stream, owns permit release."""
    try:
        await operation()
    finally:
        gate.release()


def create_app(
    *,
    runtime_provider: Any | None = None,
    pipeline_callable: PipelineCallable = run_hosted_pipeline,
    run_gate: ProcessRunGate | None = None,
) -> FastAPI:
    """Create a credential-safe HTTP adapter with lazy production defaults."""
    app = FastAPI()
    app.state.runtime_provider = runtime_provider or HostedRuntimeProvider()
    app.state.run_gate = run_gate or ProcessRunGate()
    app.state.active_tasks: set[asyncio.Task[Any]] = set()

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/runs")
    async def start_run(request: Request, payload: RunRequest) -> StreamingResponse:
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type.lower():
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={"code": "invalid_request", "message": "JSON request body required."},
            )
        try:
            dependencies = await app.state.runtime_provider.get()
        except HostedRuntimeBootstrapError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "configuration_unavailable", "message": "Runtime configuration is unavailable."},
            ) from None
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "internal_error", "message": "The run could not start."},
            ) from None
        gate: ProcessRunGate = app.state.run_gate
        if not gate.try_acquire():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "run_in_progress", "message": "A run is already in progress."},
            )

        run_id = str(uuid.uuid4())
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

        async def publish(event: dict[str, Any]) -> None:
            await queue.put(event)

        async def observer(stage: str, state: str, artifact: Any | None) -> None:
            if state == "running":
                await publish({"type": "stage_started", "run_id": run_id, "stage": stage})
                return
            event: dict[str, Any] = {
                "type": "stage_accepted",
                "run_id": run_id,
                "stage": stage,
            }
            if artifact is not None:
                event["artifact"] = artifact.model_dump(mode="json")
            await publish(event)

        async def execute() -> None:
            try:
                await publish({"type": "run_started", "run_id": run_id})
                await pipeline_callable(payload.brief, dependencies, observer)
            except HostedStageError as err:
                error = {"code": "stage_failed", "message": "A pipeline stage failed."}
                await publish({"type": "stage_failed", "run_id": run_id, "stage": err.stage, "error": error})
                await publish({"type": "run_failed", "run_id": run_id, "stage": err.stage, "error": error})
            except Exception:
                error = {"code": "internal_error", "message": "The run could not complete."}
                await publish({"type": "stage_failed", "run_id": run_id, "stage": "internal", "error": error})
                await publish({"type": "run_failed", "run_id": run_id, "stage": "internal", "error": error})
            else:
                await publish({"type": "run_completed", "run_id": run_id})
            finally:
                await queue.put(None)

        task = asyncio.create_task(_run_with_owned_gate(gate, execute))
        app.state.active_tasks.add(task)
        task.add_done_callback(app.state.active_tasks.discard)

        async def event_stream() -> AsyncIterator[bytes]:
            while True:
                event = await queue.get()
                if event is None:
                    return
                yield _ndjson(event)

        return StreamingResponse(event_stream(), media_type="application/x-ndjson")

    return app


app = create_app()
