"""Deterministic runtime gates for Physical Constraints Agent synthesis."""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Sequence

from src.contracts.director_intent import DirectorIntentContract
from src.contracts.physical_constraints import (
    PhysicalConstraintsContract,
    PhysicalConstraintsScope,
    ResearchFindingProvenanceReference,
)
from src.contracts.research_evidence import ResearchEvidenceContract, ResearchScope
from src.services.research_retrieval import derive_research_scope


class PhysicalConstraintsScopeValidationError(ValueError):
    """Raised when agent output does not faithfully preserve runtime-derived input scope."""


class DirectorResearchScopeValidationError(ValueError):
    """Raised when accepted Research scope is not faithful to the supplied Director contract."""


class EpistemicNonEscalationError(ValueError):
    """Raised when bounded candidate wording strengthens accepted evidence deterministically."""


def _normalize_epistemic_text(value: str) -> str:
    """NFKC/casefold/token normalization for bounded deterministic matching."""
    import unicodedata

    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = normalized.translate(
        str.maketrans({chr(codepoint): "-" for codepoint in range(0x2010, 0x2016)})
    )
    tokens = re.findall(r"\d+(?:[.,]\d+)?(?:e[+-]?\d+)?|[^\W_]+|[.;:]", normalized, flags=re.UNICODE)
    return " ".join(token.replace(",", ".") for token in tokens)


def _assertion_segments(text: str) -> list[str]:
    """Split bounded assertions without splitting deterministic decimal literals."""
    normalized = _normalize_epistemic_text(text)
    protected = re.sub(r"(?<=\d)\.(?=\d)", "__decimal_point__", normalized)
    return [
        segment.replace("__decimal_point__", ".").strip()
        for segment in re.split(
            r"[.;:]|\b(?:but|however|therefore|yet|although|while)\b",
            protected,
        )
        if segment.strip()
    ]

def _has_forbidden_affirmative_relation(
    text: str,
    affirmative_patterns: Sequence[str],
    negated_patterns: Sequence[str],
) -> bool:
    """Reject an affirmative relation unless that exact match is inside its negated form."""
    for segment in _assertion_segments(text):
        negated_spans = [match.span() for pattern in negated_patterns for match in re.finditer(pattern, segment)]
        for pattern in affirmative_patterns:
            for match in re.finditer(pattern, segment):
                if not any(start <= match.start() < end for start, end in negated_spans):
                    return True
    return False


def _canonical_decimal(value: str) -> Decimal | None:
    """Canonicalize deterministic decimal syntax only; never convert units or evaluate expressions."""
    try:
        return Decimal(value.replace(",", "."))
    except InvalidOperation:
        return None


def _numeric_literals(text: str) -> set[Decimal]:
    return {
        decimal
        for token in re.findall(r"\b\d+(?:[.,]\d+)?(?:e[+-]?\d+)?\b", text, flags=re.IGNORECASE)
        if (decimal := _canonical_decimal(token)) is not None
    }


def _contextual_generalization_asserted(text: str) -> bool:
    affirmative = (
        r"\b(?:represent|represents|representing)\b.{0,48}?\b(?:transparent|material|media|class)\b",
        r"\b(?:is|are)\s+(?:representative|typical|generic)\b.{0,32}?\b(?:transparent|material|media|class)\b",
        r"\b(?:representative|typical|generic)\s+\b(?:transparent|material|media|class)\b",
        r"\b(?:is|are|may be)\s+used\s+as\s+(?:a\s+)?(?:reference range|benchmark|proxy|calibration)\b",
        r"\b(?:serve as|serves as|form|forms)\s+(?:a\s+)?(?:reference range|benchmark|proxy|calibration)\b",
        r"\b(?:is|are)\s+generalized\s+to\b.{0,32}?\b(?:transparent|material|media|class)\b",
        r"\b(?:establish|establishes|provide|provides|form|forms)\b.{0,48}?\b(?:reference range|benchmark|proxy|calibration|physical scale|generic refractive reference|baseline|scale)\b",
    )
    negated = (
        r"\b(?:do not|does not)\s+represent\b.{0,48}?\b(?:transparent|material|media|class)\b",
        r"\b(?:is|are)\s+not\s+(?:representative|typical|generic)\b.{0,32}?\b(?:transparent|material|media|class)\b",
        r"\b(?:cannot|must not)\s+be\s+used\s+as\s+(?:a\s+)?(?:reference range|benchmark|proxy|calibration)\b",
        r"\b(?:cannot|must not)\s+be\s+generalized\s+(?:to|into)\b.{0,32}?\b(?:transparent|material|media|class)\b",
        r"\b(?:do not|does not)\s+establish\b.{0,48}?\b(?:reference range|benchmark|proxy|calibration|physical scale|generic refractive reference|baseline|scale)\b",
        r"\b(?:is|are)\s+not\s+(?:a\s+)?reference range\b.{0,32}?\b(?:transparent|material|media|class)\b",
    )
    return _has_forbidden_affirmative_relation(text, affirmative, negated)


def _unresolved_quantitative_escalation_asserted(text: str) -> bool:
    affirmative = (
        r"\b(?:is|becomes|became|produces|produce)\s+non\s+physical(?:\s+behavior)?\b",
        r"\b(?:is|becomes|became)\s+physically\s+impossible\b",
        r"\b(?:exceed|exceeds|exceeded|violate|violates|violated|go beyond|goes beyond|went beyond|depart from|departs from|departed from)\b.{0,40}?\b(?:physical|dispersion|quantitative|standard|normal|typical)\b.{0,24}?\b(?:limit|limits|constraint|constraints|baseline|behavior)\b",
        r"\b(?:exceed|exceeds|exceeded|violate|violates|violated|go beyond|goes beyond|went beyond|depart from|departs from|departed from)\b.{0,24}?\b(?:limit|limits|constraint|constraints|baseline|behavior)\b",
    )
    negated = (
        r"\b(?:does not|do not|cannot be shown to|is not known to)\s+(?:exceed|violate|go beyond|depart from)\b.{0,40}?\b(?:limit|limits|constraint|constraints|baseline|behavior)\b",
        r"\b(?:is|are)\s+not\s+(?:established\s+as\s+)?non\s+physical\b",
        r"\b(?:is|are)\s+not\s+physically\s+impossible\b",
        r"\b(?:cannot be called|insufficient evidence to call)\b.{0,24}?\bnon\s+physical\b",
        r"\b(?:no|insufficient)\s+(?:quantitative\s+)?(?:physical\s+|dispersion\s+)?(?:limit|limits|baseline)\b.{0,40}?\b(?:established|resolve)\b",
    )
    return _has_forbidden_affirmative_relation(text, affirmative, negated)


def _scene_numeric_promotion_asserted(text: str, entity_id: str, values: set[Decimal]) -> bool:
    entity = _normalize_epistemic_text(entity_id)
    affirmative = (
        rf"\b{re.escape(entity)}\b(?:\s+\w+){{0,4}}\s+refractive\s+index\s+is\b",
        rf"\b{re.escape(entity)}\b\s+(?:has|uses|use|may use)\b",
        rf"\b{re.escape(entity)}\b\s+(?:may be|can be)\s+approximated\s+(?:as|by)\b",
        rf"\b{re.escape(entity)}\b\s+has\s+(?:a\s+)?range\s+of\b",
        rf"\b(?:use|assign|assigned|approximate|approximated)\b.{{0,24}}\b(?:for|to|as|by)\b.{{0,12}}\b{re.escape(entity)}\b",
        rf"\b(?:is|as)\s+(?:an?\s+)?(?:approximation|approximate\s+refractive\s+index)\b.{{0,32}}\b(?:for|to)\b.{{0,12}}\b{re.escape(entity)}\b",
    )
    negated = (
        rf"\b{re.escape(entity)}\b\s+is\s+not\s+established\s+to\s+have\s+refractive\s+index\b",
        rf"\b{re.escape(entity)}\b\s+must\s+not\s+be\s+approximated\s+(?:as|by)\b",
        r"\b(?:must not|do not|does not|cannot)\s+(?:be\s+)?(?:use|assign|assigned|approximate|approximated|treated)\b",
        rf"\bmust\s+not\s+be\s+treated\s+as\s+(?:an?\s+)?approximation\b.{{0,32}}?\b(?:for|to)\b.{{0,12}}?\b{re.escape(entity)}\b",
        rf"\b(?:is|are)\s+not\s+(?:an?\s+)?(?:approximation|approximate\s+refractive\s+index)\b.{{0,32}}\b(?:for|to)\b.{{0,12}}\b{re.escape(entity)}\b",
        r"\bdoes not resolve\b",
        rf"\b(?:no|not)\s+(?:range|value)\b.{{0,48}}\b(?:established|resolve)\b.{{0,24}}\b{re.escape(entity)}\b",
    )
    for segment in _assertion_segments(text):
        if _numeric_literals(segment).intersection(values) and _has_forbidden_affirmative_relation(
            segment, affirmative, negated
        ):
            return True
    return False

def iter_model_authored_semantic_text(candidate: PhysicalConstraintsContract):
    """Yield every current model-authored prose field as (path, text, semantic_role)."""
    for constraint_index, constraint in enumerate(candidate.constraints):
        yield (f"constraints[{constraint_index}].statement", constraint.statement, "constraint")
        for field_name in ("conditions", "limitations", "safe_downstream_assumptions", "unsafe_downstream_assumptions"):
            for value_index, value in enumerate(getattr(constraint, field_name)):
                yield (f"constraints[{constraint_index}].{field_name}[{value_index}]", value, "constraint")
        for identity_index, identity in enumerate(constraint.material_identity_references):
            if identity.identity_label is not None:
                yield (f"constraints[{constraint_index}].material_identity_references[{identity_index}].identity_label", identity.identity_label, "identity")
            if identity.limitation is not None:
                yield (f"constraints[{constraint_index}].material_identity_references[{identity_index}].limitation", identity.limitation, "identity")
    for conflict_index, conflict in enumerate(candidate.conflicts):
        yield (f"conflicts[{conflict_index}].statement", conflict.statement, "conflict")
        for field_name in ("conditions", "limitations"):
            for value_index, value in enumerate(getattr(conflict, field_name)):
                yield (f"conflicts[{conflict_index}].{field_name}[{value_index}]", value, "conflict")
    for unresolved_index, unresolved in enumerate(candidate.unresolved_constraints):
        yield (f"unresolved_constraints[{unresolved_index}].why_indeterminate", unresolved.why_indeterminate, "unresolved")
        for field_name in ("evidence_needed", "limitations"):
            for value_index, value in enumerate(getattr(unresolved, field_name)):
                yield (f"unresolved_constraints[{unresolved_index}].{field_name}[{value_index}]", value, "unresolved")
    for deviation_index, deviation in enumerate(candidate.artistic_deviations):
        yield (f"artistic_deviations[{deviation_index}].statement", deviation.statement, "deviation")
        yield (f"artistic_deviations[{deviation_index}].physical_tradeoff", deviation.physical_tradeoff, "deviation")
    for coverage_index, coverage in enumerate(candidate.coverage):
        if coverage.notes is not None:
            yield (f"coverage[{coverage_index}].notes", coverage.notes, "coverage")
    yield ("physical_summary", candidate.physical_summary, "summary")


def _scene_specific_quantitative_evidence_exists(research: ResearchEvidenceContract, entity_id: str, parameter: str) -> bool:
    for finding in research.findings:
        if (entity_id, parameter) not in {(item.entity_id, item.parameter) for item in finding.related_material_unknown_parameters}:
            continue
        if finding.evidence_status.value not in {"supported", "partially_supported"}:
            continue
        if any(item.related_entity == entity_id and _numeric_literals(_normalize_epistemic_text(item.value_text)) for item in finding.physical_parameters):
            return True
    return False


def _contextual_numeric_values(candidate: PhysicalConstraintsContract, research: ResearchEvidenceContract) -> set[Decimal]:
    cited_finding_ids = {
        finding_id for constraint in candidate.constraints for identity in constraint.material_identity_references
        if identity.status.value == "contextual_only" for finding_id in identity.research_finding_ids
    }
    return {
        decimal for finding in research.findings if finding.id in cited_finding_ids
        for parameter in finding.physical_parameters
        for decimal in _numeric_literals(_normalize_epistemic_text(parameter.value_text))
    }

def validate_epistemic_non_escalation(
    candidate: PhysicalConstraintsContract,
    director: DirectorIntentContract,
    research: ResearchEvidenceContract,
) -> None:
    """Fail closed for documented bounded affirmative escalation patterns.

    This is not scientific entailment validation. It checks every current model-authored prose field
    with NFKC/casefold/token normalization and a bounded local negation grammar.
    """
    unknown_pairs = {
        (item.entity_id, item.parameter)
        for item in candidate.input_scope.director_material_unknown_parameters
        if not _scene_specific_quantitative_evidence_exists(research, item.entity_id, item.parameter)
    }
    contextual_identity_present = any(
        identity.status.value == "contextual_only"
        for constraint in candidate.constraints
        for identity in constraint.material_identity_references
    )
    contextual_values = _contextual_numeric_values(candidate, research)

    for path, raw_text, _role in iter_model_authored_semantic_text(candidate):
        text = _normalize_epistemic_text(raw_text)
        if contextual_identity_present and _contextual_generalization_asserted(text):
            raise EpistemicNonEscalationError(f"E_CONTEXT_GENERALIZATION at {path}: Contextual-only evidence cannot be promoted to a broader material baseline.")
        if unknown_pairs and _unresolved_quantitative_escalation_asserted(text):
            raise EpistemicNonEscalationError(f"E_UNRESOLVED_PHYSICAL_LIMIT at {path}: Unresolved quantitative evidence cannot establish non-physicality or a physical limit.")
        if unknown_pairs and contextual_values:
            for entity_id, _parameter in unknown_pairs:
                if _scene_numeric_promotion_asserted(text, entity_id, contextual_values):
                    raise EpistemicNonEscalationError(f"E_SCENE_NUMERIC_PROMOTION at {path}: Contextual-only numeric evidence cannot establish a scene-material unknown parameter.")

def _canonical_research_scope(scope: ResearchScope) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[tuple[str, str], ...]]:
    """Compare ResearchScope membership without hiding duplicate or blank identifiers."""
    def members(values: list[str], label: str) -> tuple[str, ...]:
        if any(not value for value in values) or len(values) != len(set(values)):
            raise DirectorResearchScopeValidationError(f"{label} contains duplicate or blank identifiers.")
        return tuple(sorted(values))

    pairs = [(item.entity_id, item.parameter) for item in scope.director_material_unknown_parameters]
    if any(not entity_id or not parameter for entity_id, parameter in pairs) or len(pairs) != len(set(pairs)):
        raise DirectorResearchScopeValidationError("Research material unknown scope contains duplicate or blank pairs.")
    return (
        members(scope.director_research_requirement_ids, "Research requirement scope"),
        members(scope.director_physical_question_ids, "Physical question scope"),
        members(scope.director_scene_entity_ids, "Scene entity scope"),
        tuple(sorted(pairs)),
    )

def validate_exact_research_scope_for_director(
    director: DirectorIntentContract,
    research: ResearchEvidenceContract,
) -> None:
    """Require the accepted Research scope to match the supplied Director before synthesis."""
    expected = _canonical_research_scope(derive_research_scope(director))
    actual = _canonical_research_scope(research.research_scope)
    if actual != expected:
        raise DirectorResearchScopeValidationError(
            "ResearchEvidenceContract scope does not exactly match the supplied Director contract."
        )

def derive_physical_constraints_scope(
    director: DirectorIntentContract,
    research: ResearchEvidenceContract,
) -> PhysicalConstraintsScope:
    """Derive the authoritative Physical Constraints scope from validated upstream contracts."""
    return PhysicalConstraintsScope(
        director_physical_question_ids=[item.id for item in director.physical_questions],
        director_research_requirement_ids=[item.id for item in director.research_required],
        director_scene_entity_ids=[item.id for item in director.scene_entities],
        director_material_unknown_parameters=[
            {"entity_id": item.entity_id, "parameter": parameter}
            for item in director.material_intent
            for parameter in item.unknown_parameters
        ],
        director_validation_target_ids=[item.id for item in director.validation_targets],
        research_finding_provenance=[
            ResearchFindingProvenanceReference(
                finding_id=item.id,
                source_ids=list(item.source_ids),
                evidence_status=item.evidence_status,
            )
            for item in research.findings
        ],
        research_conflict_ids=[item.id for item in research.conflicts],
        research_unresolved_question_ids=[item.id for item in research.unresolved_questions],
    )


def _canonical_scope(scope: PhysicalConstraintsScope) -> tuple[Any, ...]:
    """Compare membership-based scope collections without masking record structure."""
    pairs = tuple(sorted((item.entity_id, item.parameter) for item in scope.director_material_unknown_parameters))
    provenance = tuple(sorted(
        (item.finding_id, tuple(sorted(item.source_ids)), item.evidence_status.value)
        for item in scope.research_finding_provenance
    ))
    return (
        tuple(sorted(scope.director_physical_question_ids)),
        tuple(sorted(scope.director_research_requirement_ids)),
        tuple(sorted(scope.director_scene_entity_ids)),
        pairs,
        tuple(sorted(scope.director_validation_target_ids)),
        provenance,
        tuple(sorted(scope.research_conflict_ids)),
        tuple(sorted(scope.research_unresolved_question_ids)),
    )


def validate_exact_physical_constraints_scope(
    candidate: PhysicalConstraintsContract,
    director: DirectorIntentContract,
    research: ResearchEvidenceContract,
) -> None:
    """Require exact semantic fidelity to the scope derived from actual validated inputs."""
    expected = _canonical_scope(derive_physical_constraints_scope(director, research))
    actual = _canonical_scope(candidate.input_scope)
    if actual != expected:
        raise PhysicalConstraintsScopeValidationError(
            "Candidate PhysicalConstraintsScope does not exactly match Director and Research input scope."
        )


def build_physical_constraints_packet(
    director: DirectorIntentContract,
    research: ResearchEvidenceContract,
) -> dict[str, Any]:
    """Build a deterministic closed packet with explicit structural/data trust boundaries."""
    return {
        "authoritative_runtime": {
            "expected_input_scope": derive_physical_constraints_scope(director, research).model_dump(mode="json"),
        },
        "untrusted_input_data": {
            "director_context": director.model_dump(mode="json"),
            "research_context": research.model_dump(mode="json"),
        },
    }


def render_physical_constraints_packet(packet: dict[str, Any]) -> str:
    """Render a deterministic JSON packet while preserving semantically ordered lists."""
    return json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False)


def extract_physical_constraints_text_from_adk_events(events: Sequence[dict[str, Any]]) -> str:
    """Extract non-thought text from ADK-shaped events and reject metadata-only responses."""
    chunks: list[str] = []
    for event in events:
        for part in (event.get("content") or {}).get("parts") or []:
            if not part.get("thought") and part.get("text"):
                chunks.append(part["text"])
    text = "".join(chunks).strip()
    if not text:
        raise ValueError("No model text response found in ADK events.")
    return text


def validate_runtime_inputs(
    director_json: str,
    research_json: str,
) -> tuple[DirectorIntentContract, ResearchEvidenceContract]:
    """Parse upstream JSON before a model can be invoked."""
    director = DirectorIntentContract.model_validate_json(director_json)
    research = ResearchEvidenceContract.model_validate_json(research_json)
    validate_exact_research_scope_for_director(director, research)
    return director, research


def accept_physical_constraints_candidate(
    raw_text: str,
    director: DirectorIntentContract,
    research: ResearchEvidenceContract,
) -> PhysicalConstraintsContract:
    """Parse once, preserve frozen validators, then apply cross-contract fidelity gate."""
    candidate = PhysicalConstraintsContract.model_validate_json(raw_text)
    validate_exact_physical_constraints_scope(candidate, director, research)
    validate_epistemic_non_escalation(candidate, director, research)
    return candidate


async def synthesize_physical_constraints(
    app: Any,
    director: DirectorIntentContract,
    research: ResearchEvidenceContract,
) -> PhysicalConstraintsContract:
    """Invoke the supplied app exactly once; no repair, retry, or critique pass exists."""
    validate_exact_research_scope_for_director(director, research)
    message = render_physical_constraints_packet(build_physical_constraints_packet(director, research))
    events = []
    async for event in app.async_stream_query(
        user_id="cineverity-local-physical-constraints",
        message=message,
    ):
        events.append(event)
    return accept_physical_constraints_candidate(
        extract_physical_constraints_text_from_adk_events(events), director, research
    )