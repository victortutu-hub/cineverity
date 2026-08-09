"""
Director Agent Contract v0.1

Defines the Pydantic v2 data models, enums, and strict validation boundaries
for interpreting creative briefs into structured cinematic intent contracts.
"""

from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    """Base model enforcing strict Pydantic validation behavior across all contract schemas."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class RealityMode(str, Enum):
    """Categorizes how the scene relates to real-world physics."""

    strict_physical = "strict_physical"
    physically_grounded_artistic = "physically_grounded_artistic"
    speculative_but_coherent = "speculative_but_coherent"
    explicitly_nonphysical = "explicitly_nonphysical"


class Priority(str, Enum):
    """Priority level for questions, research requirements, and constraints."""

    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AmbiguityResolution(str, Enum):
    """Strategy for resolving prompt or technical ambiguities."""

    defer_to_research_or_user = "defer_to_research_or_user"
    art_directable = "art_directable"
    requires_validation = "requires_validation"
    user_input_required = "user_input_required"


class CreativeIntent(StrictModel):
    """High-level creative goals, mood, and reality mode."""

    core_idea: str = Field(..., min_length=1)
    desired_emotion: list[str]
    visual_priorities: list[str]
    reality_mode: RealityMode


class SceneEntity(StrictModel):
    """An object, participant, or geometric element present in the scene."""

    id: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class MaterialIntent(StrictModel):
    """Artistic material properties and physical unknowns associated with an entity."""

    entity_id: str = Field(..., min_length=1)
    material_family: str = Field(..., min_length=1)
    desired_properties: list[str]
    unknown_parameters: list[str]


class LightingIntent(StrictModel):
    """Artistic lighting setup, roles, and interaction targets."""

    id: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    color_intent: str = Field(..., min_length=1)
    interaction_target: Optional[str] = None


class EnvironmentIntent(StrictModel):
    """Environmental context, atmosphere, background, and surface properties."""

    setting: str = Field(..., min_length=1)
    surface: Optional[str] = None
    atmosphere: Optional[str] = None
    background_priority: Optional[str] = None
    environmental_effects: list[str]


class CinematicIntent(StrictModel):
    """Cinematic camera, motion, visual style, and timing requirements."""

    visual_style: list[str]
    subject_priority: Optional[str] = None
    contrast_strategy: Optional[str] = None
    camera_requirements: list[str]
    motion_requirements: list[str]
    temporal_requirements: list[str]


class PhysicalQuestion(StrictModel):
    """Technical question regarding physical feasibility or material behavior."""

    id: str = Field(..., min_length=1)
    domain: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    related_entities: list[str]
    priority: Priority


class ResearchRequirement(StrictModel):
    """Topic requiring scientific lookup or evidence gathering."""

    id: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    desired_evidence: list[str]
    priority: Priority


class ArtisticFreedom(StrictModel):
    """Explicit area where artistic expression overrides physical realism."""

    aspect: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class Ambiguity(StrictModel):
    """Identified ambiguity in the prompt or technical specification."""

    id: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    impact: str = Field(..., min_length=1)
    resolution: AmbiguityResolution


class ValidationTarget(StrictModel):
    """Target condition to be validated by downstream validation agents."""

    id: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    domain: str = Field(..., min_length=1)


class DirectorIntentContract(StrictModel):
    """Top-level validated Cinematic Intent Contract produced by the Director Agent."""

    contract_version: Literal["0.1"]
    agent: Literal["director_agent"]
    creative_intent: CreativeIntent
    scene_entities: list[SceneEntity]
    material_intent: list[MaterialIntent]
    lighting_intent: list[LightingIntent]
    environment_intent: EnvironmentIntent
    cinematic_intent: CinematicIntent
    physical_questions: list[PhysicalQuestion]
    research_required: list[ResearchRequirement]
    artistic_freedoms: list[ArtisticFreedom]
    hard_constraints: list[str]
    ambiguities: list[Ambiguity]
    validation_targets: list[ValidationTarget]
    director_summary: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_cross_entity_references(self) -> "DirectorIntentContract":
        """Strictly validate cross-entity reference integrity without silent repair."""
        entity_ids = [entity.id for entity in self.scene_entities]

        # 1. SceneEntity.id values must be unique
        if len(entity_ids) != len(set(entity_ids)):
            seen = set()
            duplicates = set()
            for eid in entity_ids:
                if eid in seen:
                    duplicates.add(eid)
                seen.add(eid)
            raise ValueError(f"Duplicate SceneEntity IDs found: {sorted(duplicates)}")

        entity_id_set = set(entity_ids)

        # 2. MaterialIntent.entity_id must reference an existing SceneEntity.id
        for idx, mat in enumerate(self.material_intent):
            if mat.entity_id not in entity_id_set:
                raise ValueError(
                    f"MaterialIntent[{idx}] references unknown entity_id: '{mat.entity_id}'"
                )

        # 3. PhysicalQuestion.related_entities items must reference existing SceneEntity.ids
        for idx, pq in enumerate(self.physical_questions):
            for rent in pq.related_entities:
                if rent not in entity_id_set:
                    raise ValueError(
                        f"PhysicalQuestion[{idx}] ('{pq.id}') references unknown related_entity: '{rent}'"
                    )

        # 4. LightingIntent.interaction_target (if set) must reference an existing SceneEntity.id
        for idx, light in enumerate(self.lighting_intent):
            if light.interaction_target is not None:
                if light.interaction_target not in entity_id_set:
                    raise ValueError(
                        f"LightingIntent[{idx}] ('{light.id}') references unknown interaction_target: '{light.interaction_target}'"
                    )

        return self
