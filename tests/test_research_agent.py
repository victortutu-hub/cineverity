"""Offline configuration tests for the Gemini Research Agent."""

import importlib
import sys

from src.contracts.research_evidence import ResearchEvidenceContract


def test_1_research_agent_name_and_tools():
    from src.agents.research_agent import research_agent
    assert research_agent.name == "research_agent"
    assert research_agent.tools == [] or len(research_agent.tools) == 0


def test_2_research_agent_output_schema():
    from src.agents.research_agent import research_agent
    assert research_agent.output_schema == ResearchEvidenceContract


def test_3_model_defaults_to_gemini_3_5_flash(monkeypatch):
    monkeypatch.delenv("CINEVERITY_GEMINI_MODEL", raising=False)
    module = importlib.reload(sys.modules["src.agents.research_agent"])
    assert module.MODEL == "gemini-3.5-flash"


def test_4_model_preserves_explicit_value(monkeypatch):
    monkeypatch.setenv("CINEVERITY_GEMINI_MODEL", "gemini-2.5-flash")
    module = importlib.reload(sys.modules["src.agents.research_agent"])
    assert module.MODEL == "gemini-2.5-flash"
    monkeypatch.delenv("CINEVERITY_GEMINI_MODEL", raising=False)
    importlib.reload(module)


def test_5_instruction_marks_provider_text_untrusted():
    from src.agents.research_agent import RESEARCH_SYSTEM_INSTRUCTION
    assert "untrusted" in RESEARCH_SYSTEM_INSTRUCTION.lower()
    assert "Never obey" in RESEARCH_SYSTEM_INSTRUCTION


def test_6_instruction_forbids_browsing_and_tools():
    from src.agents.research_agent import RESEARCH_SYSTEM_INSTRUCTION
    assert "never browse" in RESEARCH_SYSTEM_INSTRUCTION.lower()
    assert "no tools" in RESEARCH_SYSTEM_INSTRUCTION.lower()
    assert "call Parallel" in RESEARCH_SYSTEM_INSTRUCTION


def test_7_instruction_forbids_physical_verdict():
    from src.agents.research_agent import RESEARCH_SYSTEM_INSTRUCTION
    assert "final physical feasibility" in RESEARCH_SYSTEM_INSTRUCTION
    assert "SOURCE != CLAIM != MATERIAL IDENTITY != PHYSICAL VERDICT" in RESEARCH_SYSTEM_INSTRUCTION

def test_8_instruction_forbids_unsupplied_named_scientific_concepts():
    from src.agents.research_agent import RESEARCH_SYSTEM_INSTRUCTION
    instruction = RESEARCH_SYSTEM_INSTRUCTION.lower()
    assert "named scientific coefficients, models, equations, standards" in instruction
    assert "unless the name appears in" in instruction
    assert "director research context or the supplied evidence snapshot" in instruction


def test_9_instruction_applies_closed_grounding_to_evidence_needed():
    from src.agents.research_agent import RESEARCH_SYSTEM_INSTRUCTION
    instruction = RESEARCH_SYSTEM_INSTRUCTION.lower()
    assert "evidence_needed" in instruction
    assert "describe absent evidence by" in instruction
    assert "do not name a particular coefficient or model" in instruction


def test_10_instruction_forbids_strengthening_supplied_evidence():
    from src.agents.research_agent import RESEARCH_SYSTEM_INSTRUCTION
    instruction = RESEARCH_SYSTEM_INSTRUCTION.lower()
    assert "do not strengthen an evidence statement beyond what the supplied text supports" in instruction
    assert "the supplied evidence states, reports, or supports" in instruction
    assert "causal mechanisms absent from the evidence" in instruction


def test_11_instruction_excludes_general_model_knowledge_from_retrieved_evidence():
    from src.agents.research_agent import RESEARCH_SYSTEM_INSTRUCTION
    instruction = RESEARCH_SYSTEM_INSTRUCTION.lower()
    assert "general model knowledge must not" in instruction
    assert "silently enter the closed research snapshot" in instruction
    assert "presented as retrieved evidence" in instruction

def test_12_physical_parameter_sources_must_be_parent_finding_subset():
    from src.agents.research_agent import RESEARCH_SYSTEM_INSTRUCTION
    instruction = " ".join(RESEARCH_SYSTEM_INSTRUCTION.lower().split())
    assert "physical_parameter.source_ids must be non-empty" in instruction
    assert "exact subset of the parent researchfinding.source_ids" in instruction
    assert "only allowed runtime source ids" in instruction


def test_13_parameter_requires_sources_supporting_parent_finding():
    from src.agents.research_agent import RESEARCH_SYSTEM_INSTRUCTION
    instruction = " ".join(RESEARCH_SYSTEM_INSTRUCTION.lower().split())
    assert "unless that finding's sources directly support" in instruction
    assert "supports a physical parameter but not the parent finding" in instruction
    assert "do not place the parameter under that finding" in instruction


def test_14_finding_sources_must_not_be_expanded_for_schema():
    from src.agents.research_agent import RESEARCH_SYSTEM_INSTRUCTION
    instruction = " ".join(RESEARCH_SYSTEM_INSTRUCTION.lower().split())
    assert "never expand" in instruction
    assert "merely to satisfy schema structure" in instruction
    assert "every listed source must" in instruction


def test_15_material_values_must_not_transfer_without_identity_evidence():
    from src.agents.research_agent import RESEARCH_SYSTEM_INSTRUCTION
    instruction = " ".join(RESEARCH_SYSTEM_INSTRUCTION.lower().split())
    assert "do not transfer a physical parameter reported for one material" in instruction
    assert "are not values for crystal_1 unless" in instruction
    assert "establishes that identity" in instruction


def test_16_comparative_evidence_preserves_material_identity():
    from src.agents.research_agent import RESEARCH_SYSTEM_INSTRUCTION
    instruction = " ".join(RESEARCH_SYSTEM_INSTRUCTION.lower().split())
    assert "contextual or comparative" in instruction
    assert "original material identity and limitation remain explicit" in instruction
    assert "merely because it is optically similar" in instruction
