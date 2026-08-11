"""Deterministic Parallel retrieval registry and provenance gate for Step 2.3A."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from hashlib import sha256
from typing import Callable, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from src.contracts.director_intent import DirectorIntentContract
from src.contracts.research_evidence import (
    EvidenceSource,
    MaterialUnknownParameterReference,
    ResearchEvidenceContract,
    ResearchScope,
    SourceType,
)
from src.services.parallel_search import ParallelSearchAdapter, ParallelSearchResponse, ParallelSearchResult


MAX_RESEARCH_REQUIREMENTS = 5
_TRACKING_PARAMETERS = {"gclid", "fbclid"}


class ProvenanceValidationError(ValueError):
    """Raised when structured evidence differs from authoritative retrieval metadata."""


@dataclass(frozen=True)
class SearchPlan:
    director_research_requirement_id: str
    objective: str
    search_queries: tuple[str, str]


@dataclass(frozen=True)
class RetrievedEvidenceOccurrence:
    director_research_requirement_id: str
    search_id: str
    session_id: str
    excerpts: list[str]
    result_rank: int
    retrieved_at_utc: datetime


@dataclass
class RetrievedEvidence:
    source_id: str
    full_url_hash: str
    normalized_url: str
    provider_url: str
    provider_title: str
    provider_publish_date_raw: str | None
    provider_publication_date: date | None
    first_retrieved_at_utc: datetime
    occurrences: list[RetrievedEvidenceOccurrence] = field(default_factory=list)


@dataclass(frozen=True)
class RetrievedSearch:
    director_research_requirement_id: str
    objective: str
    search_queries: tuple[str, str]
    search_id: str
    session_id: str
    retrieved_at_utc: datetime
    result_count: int
    raw_results: tuple[ParallelSearchResult, ...]
    eligible_source_ids: list[str]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _concise_query(*parts: str) -> str:
    words = " ".join(parts).split()
    return " ".join(words[:6])


def derive_research_scope(director: DirectorIntentContract) -> ResearchScope:
    """Faithfully snapshot Director identifiers without inferring semantic links."""
    return ResearchScope(
        director_research_requirement_ids=[item.id for item in director.research_required],
        director_physical_question_ids=[item.id for item in director.physical_questions],
        director_scene_entity_ids=[item.id for item in director.scene_entities],
        director_material_unknown_parameters=[
            MaterialUnknownParameterReference(entity_id=item.entity_id, parameter=parameter)
            for item in director.material_intent
            for parameter in item.unknown_parameters
        ],
    )


def build_search_plans(director: DirectorIntentContract) -> list[SearchPlan]:
    """Build one bounded, deterministic two-query plan per Director requirement."""
    requirements = director.research_required
    requirement_ids = [requirement.id for requirement in requirements]
    if len(requirement_ids) != len(set(requirement_ids)):
        raise ValueError("Director research requirement IDs must be unique before Parallel execution.")
    if len(requirements) > MAX_RESEARCH_REQUIREMENTS:
        raise ValueError(f"At most {MAX_RESEARCH_REQUIREMENTS} Director research requirements are allowed per run.")

    plans: list[SearchPlan] = []
    for requirement in requirements:
        desired = " ".join(requirement.desired_evidence)
        objective = f"{requirement.topic}. {requirement.reason}. Evidence requested: {desired}."
        plans.append(
            SearchPlan(
                director_research_requirement_id=requirement.id,
                objective=objective,
                search_queries=(
                    _concise_query(requirement.topic, "evidence"),
                    _concise_query(requirement.topic, desired),
                ),
            )
        )
    return plans


def normalize_url(url: str) -> str:
    """Conservatively normalize a URL for deterministic identity and deduplication."""
    split = urlsplit(url.strip())
    scheme = split.scheme.lower()
    hostname = (split.hostname or "").lower()
    port = split.port
    netloc = hostname
    if port is not None and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{hostname}:{port}"
    query = [
        (key, value)
        for key, value in parse_qsl(split.query, keep_blank_values=True)
        if not (key.lower().startswith("utm_") or key.lower() in _TRACKING_PARAMETERS)
    ]
    return urlunsplit((scheme, netloc, split.path, urlencode(sorted(query)), ""))


def is_usable_web_url(url: str | None) -> bool:
    """Return whether an unmodified provider value is eligible for source identity."""
    if not url or not url.strip():
        return False
    try:
        split = urlsplit(url.strip())
        _ = split.port
    except ValueError:
        return False
    return split.scheme.lower() in {"http", "https"} and bool(split.hostname)

def source_identity(normalized_url: str) -> tuple[str, str]:
    """Return the stable public source ID and complete collision-detection hash."""
    full_hash = sha256(normalized_url.encode("utf-8")).hexdigest()
    return f"source_{full_hash[:20]}", full_hash


def _parse_provider_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


class RetrievalRegistry:
    """Canonical evidence records plus all Parallel retrieval occurrences."""

    def __init__(self) -> None:
        self.sources_by_id: dict[str, RetrievedEvidence] = {}
        self.searches: list[RetrievedSearch] = []

    def record_response(
        self,
        plan: SearchPlan,
        response: ParallelSearchResponse,
        *,
        retrieved_at_utc: datetime,
    ) -> RetrievedSearch:
        if retrieved_at_utc.tzinfo is None:
            raise ValueError("retrieved_at_utc must be timezone-aware.")
        timestamp = retrieved_at_utc.astimezone(timezone.utc)
        eligible_source_ids: list[str] = []
        for rank, result in enumerate(response.results, start=1):
            if not is_usable_web_url(result.url) or not result.title or not result.title.strip():
                continue
            provider_url = result.url.strip()
            normalized = normalize_url(provider_url)
            source_id, full_hash = source_identity(normalized)
            existing = self.sources_by_id.get(source_id)
            if existing is not None and existing.full_url_hash != full_hash:
                raise ValueError(f"Source ID prefix collision for '{source_id}'.")
            if existing is None:
                existing = RetrievedEvidence(
                    source_id=source_id,
                    full_url_hash=full_hash,
                    normalized_url=normalized,
                    provider_url=provider_url,
                    provider_title=result.title.strip(),
                    provider_publish_date_raw=result.publish_date,
                    provider_publication_date=_parse_provider_date(result.publish_date),
                    first_retrieved_at_utc=timestamp,
                )
                self.sources_by_id[source_id] = existing
            existing.occurrences.append(
                RetrievedEvidenceOccurrence(
                    director_research_requirement_id=plan.director_research_requirement_id,
                    search_id=response.search_id,
                    session_id=response.session_id,
                    excerpts=list(result.excerpts),
                    result_rank=rank,
                    retrieved_at_utc=timestamp,
                )
            )
            eligible_source_ids.append(source_id)
        search = RetrievedSearch(
            director_research_requirement_id=plan.director_research_requirement_id,
            objective=plan.objective,
            search_queries=plan.search_queries,
            search_id=response.search_id,
            session_id=response.session_id,
            retrieved_at_utc=timestamp,
            result_count=len(response.results),
            raw_results=tuple(response.results),
            eligible_source_ids=eligible_source_ids,
        )
        self.searches.append(search)
        return search


def execute_search_plans(
    plans: Iterable[SearchPlan],
    adapter: ParallelSearchAdapter,
    *,
    clock: Callable[[], datetime] = _utc_now,
) -> RetrievalRegistry:
    """Execute the pre-validated finite plan exactly once per requirement."""
    plans = list(plans)
    if len(plans) > MAX_RESEARCH_REQUIREMENTS:
        raise ValueError(f"At most {MAX_RESEARCH_REQUIREMENTS} search plans are allowed per run.")
    registry = RetrievalRegistry()
    for plan in plans:
        response = adapter.search(objective=plan.objective, search_queries=plan.search_queries)
        registry.record_response(plan, response, retrieved_at_utc=clock())
    return registry


def validate_research_contract_provenance(
    contract: ResearchEvidenceContract,
    registry: RetrievalRegistry,
) -> None:
    """Reject any source metadata not owned by the authoritative retrieval registry."""
    for source in contract.sources:
        retrieved = registry.sources_by_id.get(source.id)
        if retrieved is None:
            raise ProvenanceValidationError(f"EvidenceSource '{source.id}' was not retrieved by Parallel Search.")
        expected = EvidenceSource(
            id=retrieved.source_id,
            url=retrieved.provider_url,
            title=retrieved.provider_title,
            publication_date=retrieved.provider_publication_date,
            accessed_at=retrieved.first_retrieved_at_utc,
            publisher=None,
            source_type=SourceType.other,
        )
        for field_name in ("id", "url", "title", "publication_date", "accessed_at", "publisher", "source_type"):
            if getattr(source, field_name) != getattr(expected, field_name):
                raise ProvenanceValidationError(
                    f"EvidenceSource '{source.id}' has non-authoritative {field_name}."
                )

    for finding in contract.findings:
        if not finding.source_ids or not finding.director_research_requirement_ids:
            continue
        for requirement_id in finding.director_research_requirement_ids:
            backed = any(
                any(
                    occurrence.director_research_requirement_id == requirement_id
                    for occurrence in registry.sources_by_id[source_id].occurrences
                )
                for source_id in finding.source_ids
                if source_id in registry.sources_by_id
            )
            if not backed:
                raise ProvenanceValidationError(
                    f"ResearchFinding '{finding.id}' has no retrieved source for Director research requirement '{requirement_id}'."
                )
