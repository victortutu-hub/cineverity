"""Offline tests for Step 2.3A Parallel retrieval and provenance utilities."""

from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.contracts.director_intent import DirectorIntentContract
from src.contracts.research_evidence import EvidenceSource, ResearchEvidenceContract, SourceType
from src.services.parallel_search import PARALLEL_MAX_CHARS_TOTAL, PARALLEL_SEARCH_MODE, ParallelSearchAdapter
from src.services import research_retrieval as retrieval
from src.services.research_retrieval import (
    MAX_RESEARCH_REQUIREMENTS,
    ProvenanceValidationError,
    RetrievalRegistry,
    SearchPlan,
    build_search_plans,
    derive_research_scope,
    execute_search_plans,
    normalize_url,
    source_identity,
    validate_research_contract_provenance,
)


class FakeParallelClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def search(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def provider_response(*, search_id="search_1", session_id="session_1", results=None):
    return SimpleNamespace(search_id=search_id, session_id=session_id, results=results or [])


def provider_result(url="https://Example.test/a?utm_source=x&b=2&a=1#fragment", title="Example title", publish_date="2026-08-01", excerpts=None):
    return SimpleNamespace(url=url, title=title, publish_date=publish_date, excerpts=excerpts or ["exact excerpt"])


def director(count=1):
    requirements = [
        {"id": f"rr_{index}", "topic": f"optics evidence {index}", "reason": "Need source grounded material data", "desired_evidence": ["refractive index"] , "priority": "high"}
        for index in range(count)
    ]
    return DirectorIntentContract(
        contract_version="0.1", agent="director_agent",
        creative_intent={"core_idea": "crystal", "desired_emotion": [], "visual_priorities": [], "reality_mode": "physically_grounded_artistic"},
        scene_entities=[{"id": "crystal_1", "type": "crystal", "description": "crystal"}],
        material_intent=[{"entity_id": "crystal_1", "material_family": "crystal", "desired_properties": [], "unknown_parameters": ["refractive_index"]}],
        lighting_intent=[], environment_intent={"setting": "studio", "environmental_effects": []},
        cinematic_intent={"visual_style": [], "camera_requirements": [], "motion_requirements": [], "temporal_requirements": []},
        physical_questions=[{"id": "pq_1", "domain": "optics", "question": "question", "related_entities": ["crystal_1"], "priority": "high"}],
        research_required=requirements, artistic_freedoms=[], hard_constraints=[], ambiguities=[], validation_targets=[], director_summary="summary",
    )


def registry_with_source():
    plan = SearchPlan("rr_0", "objective", ("optics evidence", "refractive index"))
    registry = RetrievalRegistry()
    registry.record_response(plan, ParallelSearchAdapter(FakeParallelClient([provider_response(results=[provider_result()])])).search(objective="objective", search_queries=plan.search_queries), retrieved_at_utc=datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc))
    return registry


def contract_for_registry(registry):
    source = next(iter(registry.sources_by_id.values()))
    occurrence = source.occurrences[0]
    return ResearchEvidenceContract(
        contract_version="0.1", agent="research_agent",
        research_scope={"director_research_requirement_ids": ["rr_0"], "director_physical_question_ids": [], "director_scene_entity_ids": [], "director_material_unknown_parameters": []},
        sources=[EvidenceSource(id=source.source_id, title=source.provider_title, url=source.provider_url, publication_date=source.provider_publication_date, accessed_at=occurrence.retrieved_at_utc, publisher=None, source_type=SourceType.other)],
        findings=[], conflicts=[], unresolved_questions=[], coverage=[{"director_research_requirement_id": "rr_0", "state": "unresolved"}], research_summary="summary",
    )


def test_1_scope_is_faithfully_derived_from_director():
    scope = derive_research_scope(director())
    assert scope.director_research_requirement_ids == ["rr_0"]
    assert scope.director_physical_question_ids == ["pq_1"]
    assert scope.director_material_unknown_parameters[0].parameter == "refractive_index"


def test_2_search_plan_objective_is_deterministic():
    assert build_search_plans(director())[0].objective == build_search_plans(director())[0].objective


def test_3_search_plan_has_exactly_two_queries():
    assert len(build_search_plans(director())[0].search_queries) == 2


def test_4_too_many_requirements_fail_before_calls():
    with pytest.raises(ValueError, match="At most"):
        build_search_plans(director(MAX_RESEARCH_REQUIREMENTS + 1))


def test_5_one_adapter_call_per_requirement():
    plans = build_search_plans(director(2))
    client = FakeParallelClient([provider_response(), provider_response(search_id="search_2")])
    execute_search_plans(plans, ParallelSearchAdapter(client), clock=lambda: datetime(2026, 8, 11, tzinfo=timezone.utc))
    assert len(client.calls) == 2


def test_6_fixed_mode_and_max_chars_total():
    client = FakeParallelClient([provider_response()])
    ParallelSearchAdapter(client).search(objective="objective", search_queries=["one", "two"])
    assert client.calls[0]["mode"] == PARALLEL_SEARCH_MODE == "advanced"
    assert client.calls[0]["max_chars_total"] == PARALLEL_MAX_CHARS_TOTAL == 10000


def test_7_provider_response_is_normalized():
    response = ParallelSearchAdapter(FakeParallelClient([provider_response(results=[provider_result()])])).search(objective="objective", search_queries=["one", "two"])
    assert response.search_id == "search_1" and response.results[0].title == "Example title"


def test_8_missing_url_is_not_promoted():
    registry = RetrievalRegistry(); plan = SearchPlan("rr_0", "o", ("a", "b"))
    registry.record_response(plan, ParallelSearchAdapter(FakeParallelClient([provider_response(results=[provider_result(url=None)])])).search(objective="o", search_queries=plan.search_queries), retrieved_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert not registry.sources_by_id and registry.searches[0].eligible_source_ids == []


def test_9_missing_title_is_not_promoted():
    registry = RetrievalRegistry(); plan = SearchPlan("rr_0", "o", ("a", "b"))
    registry.record_response(plan, ParallelSearchAdapter(FakeParallelClient([provider_response(results=[provider_result(title=None)])])).search(objective="o", search_queries=plan.search_queries), retrieved_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert not registry.sources_by_id


def test_10_invalid_publish_date_is_not_invented():
    registry = registry_with_source(); source = next(iter(registry.sources_by_id.values()))
    assert source.provider_publication_date == date(2026, 8, 1)
    registry = RetrievalRegistry(); plan = SearchPlan("rr_0", "o", ("a", "b")); response = ParallelSearchAdapter(FakeParallelClient([provider_response(results=[provider_result(publish_date="not-a-date")])])).search(objective="o", search_queries=plan.search_queries)
    registry.record_response(plan, response, retrieved_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert next(iter(registry.sources_by_id.values())).provider_publication_date is None


def test_11_excerpts_are_preserved_exactly():
    registry = registry_with_source(); assert next(iter(registry.sources_by_id.values())).occurrences[0].excerpts == ["exact excerpt"]


def test_12_search_id_and_session_id_are_preserved():
    registry = registry_with_source(); occurrence = next(iter(registry.sources_by_id.values())).occurrences[0]
    assert (occurrence.search_id, occurrence.session_id) == ("search_1", "session_1")


def test_13_source_to_requirement_traceability_is_preserved():
    registry = registry_with_source(); assert next(iter(registry.sources_by_id.values())).occurrences[0].director_research_requirement_id == "rr_0"


def test_14_normalized_url_deduplicates_sources():
    registry = RetrievalRegistry(); plan = SearchPlan("rr_0", "o", ("a", "b")); response = ParallelSearchAdapter(FakeParallelClient([provider_response(results=[provider_result(), provider_result(url="https://example.test/a?a=1&b=2")])])).search(objective="o", search_queries=plan.search_queries)
    registry.record_response(plan, response, retrieved_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert len(registry.sources_by_id) == 1


def test_15_same_source_across_requirements_keeps_occurrences():
    client = FakeParallelClient([provider_response(search_id="s1", results=[provider_result()]), provider_response(search_id="s2", results=[provider_result(url="https://example.test/a?a=1&b=2")])])
    registry = execute_search_plans(build_search_plans(director(2)), ParallelSearchAdapter(client), clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert len(next(iter(registry.sources_by_id.values())).occurrences) == 2


def test_16_source_id_is_deterministic():
    assert source_identity(normalize_url("https://example.test/a")) == source_identity(normalize_url("https://example.test/a"))


def test_17_tracking_parameters_are_removed():
    assert "utm_source" not in normalize_url("https://example.test/a?utm_source=x&gclid=y&keep=z")


def test_18_semantic_query_parameters_are_preserved_and_sorted():
    assert normalize_url("https://example.test/a?z=2&a=1").endswith("?a=1&z=2")


def test_19_fragment_is_removed():
    assert "#" not in normalize_url("https://example.test/a#fragment")


def test_20_default_ports_are_normalized():
    assert normalize_url("HTTPS://Example.test:443/a") == "https://example.test/a"


def test_21_path_case_is_preserved():
    assert normalize_url("https://example.test/CasePath") == "https://example.test/CasePath"


def test_22_source_id_prefix_collision_fails(monkeypatch):
    monkeypatch.setattr(retrieval, "source_identity", lambda url: ("source_collision", "a" if url.endswith("one") else "b"))
    registry = RetrievalRegistry(); plan = SearchPlan("rr_0", "o", ("a", "b"))
    response = ParallelSearchAdapter(FakeParallelClient([provider_response(results=[provider_result(url="https://x/one"), provider_result(url="https://x/two")])])).search(objective="o", search_queries=plan.search_queries)
    with pytest.raises(ValueError, match="prefix collision"):
        registry.record_response(plan, response, retrieved_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc))


def test_23_clock_controlled_accessed_at_is_utc():
    timestamp = datetime(2026, 8, 11, 14, tzinfo=timezone.utc)
    registry = execute_search_plans(build_search_plans(director()), ParallelSearchAdapter(FakeParallelClient([provider_response(results=[provider_result()])])), clock=lambda: timestamp)
    assert next(iter(registry.sources_by_id.values())).occurrences[0].retrieved_at_utc == timestamp


def test_24_provenance_gate_accepts_exact_metadata():
    registry = registry_with_source(); validate_research_contract_provenance(contract_for_registry(registry), registry)


@pytest.mark.parametrize("field,value", [
    ("id", "source_invented"), ("url", "https://invented.test"), ("title", "Mutated"),
    ("publication_date", date(2020, 1, 1)), ("accessed_at", datetime(2020, 1, 1, tzinfo=timezone.utc)),
    ("publisher", "Invented Publisher"), ("source_type", SourceType.academic_reference),
])
def test_25_to_31_provenance_gate_rejects_mutated_authoritative_metadata(field, value):
    registry = registry_with_source(); contract = contract_for_registry(registry)
    source = contract.sources[0].model_copy(update={field: value})
    contract = contract.model_copy(update={"sources": [source]})
    with pytest.raises(ProvenanceValidationError):
        validate_research_contract_provenance(contract, registry)


def test_32_zero_eligible_results_creates_no_fake_evidence():
    registry = execute_search_plans(build_search_plans(director()), ParallelSearchAdapter(FakeParallelClient([provider_response(results=[provider_result(url=None), provider_result(title=None)])])), clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert not registry.sources_by_id and registry.searches[0].result_count == 2


def test_33_adapter_rejects_non_two_query_request():
    with pytest.raises(ValueError, match="exactly two"):
        ParallelSearchAdapter(FakeParallelClient([])).search(objective="o", search_queries=["only"])


def test_34_missing_key_rejected_without_client(monkeypatch):
    monkeypatch.delenv("PARALLEL_API_KEY", raising=False)
    with pytest.raises(ValueError, match="PARALLEL_API_KEY"):
        ParallelSearchAdapter()


def test_35_research_contract_validation_still_executes():
    registry = registry_with_source(); contract = contract_for_registry(registry)
    invalid = contract.model_dump(mode="json"); invalid["coverage"] = []
    with pytest.raises(ValidationError, match="exactly one entry"):
        ResearchEvidenceContract.model_validate(invalid)

def test_36_ineligible_results_remain_in_raw_snapshot():
    registry = execute_search_plans(
        build_search_plans(director()),
        ParallelSearchAdapter(FakeParallelClient([provider_response(results=[provider_result(url=None), provider_result(title=None)])])),
        clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    search = registry.searches[0]
    assert len(search.raw_results) == 2
    assert search.raw_results[0].url is None
    assert search.raw_results[1].title is None
    assert search.eligible_source_ids == []


def test_37_first_retrieval_time_is_canonical_across_occurrences():
    plan_a = SearchPlan("rr_a", "a", ("one", "two"))
    plan_b = SearchPlan("rr_b", "b", ("three", "four"))
    adapter = ParallelSearchAdapter(FakeParallelClient([
        provider_response(search_id="search_a", results=[provider_result()]),
        provider_response(search_id="search_b", results=[provider_result(url="https://example.test/a?a=1&b=2")]),
    ]))
    times = iter([datetime(2026, 1, 1, 10, tzinfo=timezone.utc), datetime(2026, 1, 2, 10, tzinfo=timezone.utc)])
    registry = execute_search_plans([plan_a, plan_b], adapter, clock=lambda: next(times))
    source = next(iter(registry.sources_by_id.values()))
    assert source.first_retrieved_at_utc == datetime(2026, 1, 1, 10, tzinfo=timezone.utc)
    assert len(source.occurrences) == 2
    contract = contract_for_registry(registry)
    contract = contract.model_copy(update={"research_scope": {"director_research_requirement_ids": ["rr_a", "rr_b"], "director_physical_question_ids": [], "director_scene_entity_ids": [], "director_material_unknown_parameters": []}, "coverage": [{"director_research_requirement_id": "rr_a", "state": "unresolved"}, {"director_research_requirement_id": "rr_b", "state": "unresolved"}]})
    validate_research_contract_provenance(contract, registry)
    changed = contract.sources[0].model_copy(update={"accessed_at": datetime(2026, 1, 2, 10, tzinfo=timezone.utc)})
    with pytest.raises(ProvenanceValidationError, match="accessed_at"):
        validate_research_contract_provenance(contract.model_copy(update={"sources": [changed]}), registry)


def _contract_with_finding(registry, requirement_ids, source_ids, status="supported"):
    sources = []
    for source_id in source_ids:
        source = registry.sources_by_id[source_id]
        sources.append({"id": source.source_id, "title": source.provider_title, "url": source.provider_url, "publication_date": source.provider_publication_date, "accessed_at": source.first_retrieved_at_utc, "publisher": None, "source_type": "other"})
    payload = {
        "contract_version": "0.1", "agent": "research_agent",
        "research_scope": {"director_research_requirement_ids": requirement_ids, "director_physical_question_ids": [], "director_scene_entity_ids": [], "director_material_unknown_parameters": []},
        "sources": sources,
        "findings": [{"id": "finding", "claim": "claim", "domain": "optics", "evidence_status": status, "source_ids": source_ids, "director_research_requirement_ids": requirement_ids, "director_physical_question_ids": [], "related_scene_entities": [], "related_material_unknown_parameters": [], "conditions": [], "limitations": [], "missing_context": [], "physical_parameters": []}],
        "conflicts": [], "unresolved_questions": [],
        "coverage": [{"director_research_requirement_id": requirement_id, "state": "unresolved"} for requirement_id in requirement_ids],
        "research_summary": "summary",
    }
    return ResearchEvidenceContract.model_validate(payload)


def test_38_requirement_source_gate_accepts_matching_occurrence():
    registry = registry_with_source(); source_id = next(iter(registry.sources_by_id))
    validate_research_contract_provenance(_contract_with_finding(registry, ["rr_0"], [source_id]), registry)


def test_39_requirement_source_gate_rejects_unmatched_requirement():
    registry = registry_with_source(); source_id = next(iter(registry.sources_by_id))
    contract = _contract_with_finding(registry, ["rr_0", "rr_b"], [source_id])
    with pytest.raises(ProvenanceValidationError, match="rr_b"):
        validate_research_contract_provenance(contract, registry)


def test_40_requirement_source_gate_accepts_multiple_sources_for_multiple_requirements():
    plans = [SearchPlan("rr_a", "a", ("one", "two")), SearchPlan("rr_b", "b", ("three", "four"))]
    registry = execute_search_plans(plans, ParallelSearchAdapter(FakeParallelClient([
        provider_response(results=[provider_result(url="https://example.test/a")]),
        provider_response(results=[provider_result(url="https://example.test/b")]),
    ])), clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc))
    validate_research_contract_provenance(_contract_with_finding(registry, ["rr_a", "rr_b"], list(registry.sources_by_id)), registry)


def test_41_source_free_unsupported_finding_is_allowed_by_gate():
    registry = registry_with_source()
    payload = contract_for_registry(registry).model_dump(mode="json")
    payload["findings"] = [{"id": "finding", "claim": "no evidence", "domain": "optics", "evidence_status": "unsupported", "source_ids": [], "director_research_requirement_ids": ["rr_0"], "director_physical_question_ids": [], "related_scene_entities": [], "related_material_unknown_parameters": [], "conditions": [], "limitations": [], "missing_context": [], "physical_parameters": []}]
    validate_research_contract_provenance(ResearchEvidenceContract.model_validate(payload), registry)


@pytest.mark.parametrize("url", ["not-a-url", "https:///missing-host", "mailto:test@example.test"])
def test_42_to_44_malformed_or_nonweb_urls_stay_raw(url):
    registry = execute_search_plans(build_search_plans(director()), ParallelSearchAdapter(FakeParallelClient([provider_response(results=[provider_result(url=url)])])), clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert len(registry.searches[0].raw_results) == 1
    assert not registry.sources_by_id


def test_45_duplicate_director_requirement_ids_fail_before_adapter_call():
    duplicate_director = director(2)
    duplicate_director.research_required[1].id = "rr_0"
    client = FakeParallelClient([])
    with pytest.raises(ValueError, match="must be unique"):
        build_search_plans(duplicate_director)
    assert client.calls == []


def test_46_canonical_provider_metadata_is_trimmed_while_raw_is_preserved():
    raw_url = "  https://example.test/a  "
    raw_title = "  Provider title  "
    registry = execute_search_plans(build_search_plans(director()), ParallelSearchAdapter(FakeParallelClient([provider_response(results=[provider_result(url=raw_url, title=raw_title)])])), clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc))
    source = next(iter(registry.sources_by_id.values()))
    assert source.provider_url == raw_url.strip()
    assert source.provider_title == raw_title.strip()
    assert registry.searches[0].raw_results[0].url == raw_url
    assert registry.searches[0].raw_results[0].title == raw_title
