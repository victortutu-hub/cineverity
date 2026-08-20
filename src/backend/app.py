"""FastAPI/NDJSON adapter for the deterministic hosted CineVerity pipeline."""

from __future__ import annotations

import asyncio
import json
import math
import threading
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

from src.backend.bootstrap import HostedRuntimeBootstrapError, HostedRuntimeProvider
from src.backend.orchestrator import HostedStageError, HostedRuntimeDependencies, run_hosted_pipeline


DEFAULT_RUN_TIMEOUT_SECONDS = 900.0


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


PipelineCallable = Callable[[str, HostedRuntimeDependencies, Any], Awaitable[Any]]


def _ndjson(event: dict[str, Any]) -> bytes:
    return (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


async def _drain_pipeline_task(pipeline_task: asyncio.Task[Any]) -> bool:
    """Drain to completion and report cancellation of this owner, not its child."""
    owner_task = asyncio.current_task()
    owner_cancellation_seen = False
    while not pipeline_task.done():
        try:
            await asyncio.shield(pipeline_task)
        except asyncio.CancelledError:
            if owner_task is not None and owner_task.cancelling() > 0:
                owner_cancellation_seen = True
        except Exception:
            break
    if pipeline_task.done():
        try:
            pipeline_task.result()
        except (asyncio.CancelledError, Exception):
            pass
    return owner_cancellation_seen


async def _run_with_owned_gate(
    gate: ProcessRunGate,
    operation: Callable[[], Awaitable[None]],
) -> None:
    """The independent execution task owns permit release after safe cleanup."""
    try:
        await operation()
    finally:
        gate.release()


def _validate_timeout(run_timeout_seconds: float) -> float:
    if isinstance(run_timeout_seconds, bool):
        raise ValueError("run_timeout_seconds must be finite and greater than zero")
    try:
        timeout = float(run_timeout_seconds)
    except (TypeError, ValueError) as err:
        raise ValueError("run_timeout_seconds must be finite and greater than zero") from err
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("run_timeout_seconds must be finite and greater than zero")
    return timeout


def create_app(
    *,
    runtime_provider: Any | None = None,
    pipeline_callable: PipelineCallable = run_hosted_pipeline,
    run_gate: ProcessRunGate | None = None,
    run_timeout_seconds: float = DEFAULT_RUN_TIMEOUT_SECONDS,
) -> FastAPI:
    """Create a credential-safe HTTP adapter with a soft execution deadline."""
    timeout_seconds = _validate_timeout(run_timeout_seconds)
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

        last_started_stage: str | None = None

        async def observer(stage: str, state: str, artifact: Any | None) -> None:
            nonlocal last_started_stage
            if state == "running":
                last_started_stage = stage
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
            pipeline_task: asyncio.Task[Any] | None = None
            pipeline_cancel_requested = False
            stream_closed = False

            async def cancel_pipeline_once() -> None:
                nonlocal pipeline_cancel_requested
                if pipeline_task is not None and not pipeline_task.done() and not pipeline_cancel_requested:
                    pipeline_task.cancel()
                    pipeline_cancel_requested = True

            try:
                await publish({"type": "run_started", "run_id": run_id})
                pipeline_task = asyncio.create_task(
                    pipeline_callable(payload.brief, dependencies, observer)
                )
                done, _ = await asyncio.wait({pipeline_task}, timeout=timeout_seconds)
                if pipeline_task in done or pipeline_task.done():
                    await pipeline_task
                else:
                    await cancel_pipeline_once()
                    error = {
                        "code": "run_timeout",
                        "message": "The run exceeded its execution deadline.",
                    }
                    if last_started_stage is not None:
                        await publish(
                            {
                                "type": "stage_failed",
                                "run_id": run_id,
                                "stage": last_started_stage,
                                "error": error,
                            }
                        )
                        await publish(
                            {
                                "type": "run_failed",
                                "run_id": run_id,
                                "stage": last_started_stage,
                                "error": error,
                            }
                        )
                    else:
                        await publish({"type": "run_failed", "run_id": run_id, "error": error})
                    await queue.put(None)
                    stream_closed = True
                    owner_cancelled_during_drain = await _drain_pipeline_task(pipeline_task)
                    if owner_cancelled_during_drain:
                        raise asyncio.CancelledError
                    return
            except asyncio.CancelledError:
                await cancel_pipeline_once()
                if pipeline_task is not None:
                    await _drain_pipeline_task(pipeline_task)
                raise
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
                if not stream_closed:
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
