"""Deterministic hosted pipeline coordination over injected specialist runtimes."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from src.contracts.director_intent import DirectorIntentContract
from src.contracts.physical_constraints import PhysicalConstraintsContract
from src.contracts.research_evidence import ResearchEvidenceContract
from src.contracts.scene_planning import ScenePlanningContract
from src.contracts.validation_readiness import ValidationReadinessContract
from src.services.director_runtime import synthesize_director
from src.services.physical_constraints_runtime import synthesize_physical_constraints
from src.services.research_retrieval import build_search_plans, execute_search_plans
from src.services.research_runtime import synthesize_with_app
from src.services.scene_planning_runtime import synthesize_scene_planning
from src.services.validation_readiness_runtime import synthesize_validation_readiness


@dataclass(frozen=True)
class HostedRuntimeDependencies:
    """Injected applications and retrieval adapter; no provider setup occurs here."""

    director_app: Any
    research_app: Any
    physical_constraints_app: Any
    scene_planning_app: Any
    validation_readiness_app: Any
    parallel_adapter: Any


@dataclass(frozen=True)
class HostedRunResult:
    """The five individually accepted specialist artifacts for one completed run."""

    director: DirectorIntentContract
    research: ResearchEvidenceContract
    physical_constraints: PhysicalConstraintsContract
    scene_planning: ScenePlanningContract
    validation_readiness: ValidationReadinessContract


class HostedStageError(RuntimeError):
    """Preserve the failing application stage while retaining its original cause."""

    def __init__(self, stage: str) -> None:
        super().__init__(f"Hosted pipeline failed during {stage}.")
        self.stage = stage


async def _run_stage(stage: str, operation: Any) -> Any:
    try:
        return await operation()
    except HostedStageError:
        raise
    except Exception as err:
        raise HostedStageError(stage) from err


def _run_sync_stage(stage: str, operation: Any) -> Any:
    """Run deterministic local work while preserving ordinary exception identity."""
    try:
        return operation()
    except Exception as err:
        raise HostedStageError(stage) from err


async def run_hosted_pipeline(
    brief: str,
    dependencies: HostedRuntimeDependencies,
) -> HostedRunResult:
    """Run accepted contracts in fixed order; any failure stops the pipeline."""
    director = await _run_stage(
        "director",
        lambda: synthesize_director(dependencies.director_app, brief),
    )

    plans = _run_sync_stage(
        "research_planning",
        lambda: build_search_plans(director),
    )

    async def retrieve_research() -> Any:
        return await asyncio.to_thread(
            execute_search_plans,
            plans,
            dependencies.parallel_adapter,
        )

    registry = await _run_stage("parallel_retrieval", retrieve_research)
    research = await _run_stage(
        "research",
        lambda: synthesize_with_app(dependencies.research_app, director, registry),
    )
    physical = await _run_stage(
        "physical_constraints",
        lambda: synthesize_physical_constraints(
            dependencies.physical_constraints_app,
            director,
            research,
        ),
    )
    scene = await _run_stage(
        "scene_planning",
        lambda: synthesize_scene_planning(
            dependencies.scene_planning_app,
            director,
            physical,
        ),
    )
    validation = await _run_stage(
        "validation_readiness",
        lambda: synthesize_validation_readiness(
            dependencies.validation_readiness_app,
            director,
            physical,
            scene,
        ),
    )
    return HostedRunResult(
        director=director,
        research=research,
        physical_constraints=physical,
        scene_planning=scene,
        validation_readiness=validation,
    )
