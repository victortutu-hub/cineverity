"""Lazy hosted runtime bootstrap with explicit provider initialization order."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import vertexai

from src.backend.orchestrator import HostedRuntimeDependencies


class HostedRuntimeBootstrapError(RuntimeError):
    """Raised for sanitized hosted runtime configuration/bootstrap failures."""


@dataclass(frozen=True)
class HostedRuntimeConfiguration:
    project_id: str
    location: str
    enterprise: str
    model: str


def _default_agent_loader() -> tuple[Any, Any, Any, Any, Any]:
    """Import concrete applications only after Vertex initialization."""
    from src.agents.director_agent import director_app
    from src.agents.physical_constraints_agent import physical_constraints_app
    from src.agents.research_agent import research_app
    from src.agents.scene_planning_agent import scene_planning_app
    from src.agents.validation_readiness_agent import validation_readiness_app

    return (
        director_app,
        research_app,
        physical_constraints_app,
        scene_planning_app,
        validation_readiness_app,
    )


def _default_parallel_adapter_factory() -> Any:
    """Construct the retrieval adapter only after agent applications are imported."""
    from src.services.parallel_search import ParallelSearchAdapter

    return ParallelSearchAdapter()


class HostedRuntimeProvider:
    """Build and cache one hosted runtime bundle on first successful use."""

    def __init__(
        self,
        *,
        environ: Mapping[str, str] | None = None,
        vertex_initializer: Callable[..., None] = vertexai.init,
        agent_loader: Callable[[], tuple[Any, Any, Any, Any, Any]] = _default_agent_loader,
        parallel_adapter_factory: Callable[[], Any] = _default_parallel_adapter_factory,
    ) -> None:
        self._environ = environ if environ is not None else os.environ
        self._vertex_initializer = vertex_initializer
        self._agent_loader = agent_loader
        self._parallel_adapter_factory = parallel_adapter_factory
        self._lock = asyncio.Lock()
        self._cached: HostedRuntimeDependencies | None = None

    def _preflight(self) -> HostedRuntimeConfiguration:
        project_id = self._environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise HostedRuntimeBootstrapError("Hosted runtime configuration is unavailable.")
        if not self._environ.get("PARALLEL_API_KEY"):
            raise HostedRuntimeBootstrapError("Hosted runtime configuration is unavailable.")

        location = self._environ.get("GOOGLE_CLOUD_LOCATION") or "global"
        enterprise = self._environ.get("GOOGLE_GENAI_USE_ENTERPRISE") or "True"
        model = self._environ.get("CINEVERITY_GEMINI_MODEL") or "gemini-3.5-flash"
        if enterprise.lower() not in {"true", "1", "yes"}:
            raise HostedRuntimeBootstrapError("Hosted runtime configuration is unavailable.")

        if isinstance(self._environ, dict):
            self._environ.setdefault("GOOGLE_CLOUD_LOCATION", location)
            self._environ.setdefault("GOOGLE_GENAI_USE_ENTERPRISE", enterprise)
            self._environ.setdefault("CINEVERITY_GEMINI_MODEL", model)
        else:
            os.environ.setdefault("GOOGLE_CLOUD_LOCATION", location)
            os.environ.setdefault("GOOGLE_GENAI_USE_ENTERPRISE", enterprise)
            os.environ.setdefault("CINEVERITY_GEMINI_MODEL", model)
        return HostedRuntimeConfiguration(project_id, location, enterprise, model)

    async def get(self) -> HostedRuntimeDependencies:
        if self._cached is not None:
            return self._cached
        async with self._lock:
            if self._cached is not None:
                return self._cached
            configuration = self._preflight()
            try:
                self._vertex_initializer(
                    project=configuration.project_id,
                    location=configuration.location,
                )
                apps = self._agent_loader()
                adapter = self._parallel_adapter_factory()
            except HostedRuntimeBootstrapError:
                raise
            except Exception as err:
                raise HostedRuntimeBootstrapError(
                    "Hosted runtime configuration is unavailable."
                ) from err
            self._cached = HostedRuntimeDependencies(
                director_app=apps[0],
                research_app=apps[1],
                physical_constraints_app=apps[2],
                scene_planning_app=apps[3],
                validation_readiness_app=apps[4],
                parallel_adapter=adapter,
            )
            return self._cached
