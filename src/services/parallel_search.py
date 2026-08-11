"""Official Parallel Search SDK adapter for CineVerity Step 2.3A."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Protocol, Sequence


PARALLEL_SEARCH_MODE = "advanced"
PARALLEL_MAX_CHARS_TOTAL = 10_000


class ParallelSearchClient(Protocol):
    def search(self, **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class ParallelSearchResult:
    url: str | None
    title: str | None
    publish_date: str | None
    excerpts: list[str]


@dataclass(frozen=True)
class ParallelSearchResponse:
    search_id: str
    session_id: str
    results: list[ParallelSearchResult]


class ParallelSearchAdapter:
    """Bounded adapter around the official SDK; clients are injectable for offline tests."""

    def __init__(self, client: ParallelSearchClient | None = None) -> None:
        if client is None:
            api_key = os.getenv("PARALLEL_API_KEY")
            if not api_key:
                raise ValueError("PARALLEL_API_KEY must be set for Parallel Search.")
            from parallel import Parallel

            client = Parallel(api_key=api_key, max_retries=0)
        self._client = client

    def search(self, *, objective: str, search_queries: Sequence[str]) -> ParallelSearchResponse:
        """Execute exactly one bounded Parallel Search request without retry policy."""
        queries = list(search_queries)
        if len(queries) != 2:
            raise ValueError("Parallel Search requires exactly two deterministic search queries.")

        response = self._client.search(
            objective=objective,
            search_queries=queries,
            mode=PARALLEL_SEARCH_MODE,
            max_chars_total=PARALLEL_MAX_CHARS_TOTAL,
        )
        return ParallelSearchResponse(
            search_id=response.search_id,
            session_id=response.session_id,
            results=[
                ParallelSearchResult(
                    url=getattr(result, "url", None),
                    title=getattr(result, "title", None),
                    publish_date=getattr(result, "publish_date", None),
                    excerpts=list(getattr(result, "excerpts", None) or []),
                )
                for result in response.results
            ],
        )
