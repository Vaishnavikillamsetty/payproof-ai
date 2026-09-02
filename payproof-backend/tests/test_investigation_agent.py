"""
Tests for the DisputeInvestigationAgent, Tool Registry, Schema Validation, and Fallback logic.
Also verifies the four canonical demo cases deterministically.
"""

import json
from unittest.mock import MagicMock, patch
import pytest
from pydantic import ValidationError

from app.agents.schemas import AgentRecommendation, RecommendedAction, RiskLevel, EvidenceStrength, SourceStatus
from app.agents.tools import execute_tool
from app.agents.investigation_agent import investigate, _parse_final_json, _deterministic_fallback

# --------------------------------------------------------------------------- #
# Schema Validation Tests
# --------------------------------------------------------------------------- #

def test_agent_recommendation_schema_valid():
    valid_json = {
        "recommended_action": "CONTEST",
        "confidence": 0.85,
        "risk_level": "LOW",
        "evidence_strength": "HIGH",
        "summary": "Valid summary",
        "key_findings": [
            {"finding": "f1", "source": "db", "importance": "high"}
        ],
        "missing_evidence": [],
        "contradictions": [],
        "human_approval_required": True,
        "source_status": "COMPLETE"
    }
    obj = AgentRecommendation(**valid_json)
    assert obj.recommended_action == RecommendedAction.CONTEST
    assert obj.confidence == 0.85
    assert len(obj.key_findings) == 1

def test_agent_recommendation_invalid_action():
    invalid_json = {
        "recommended_action": "INVALID_ACTION",
        "confidence": 0.85,
        "risk_level": "LOW",
        "evidence_strength": "HIGH",
        "summary": "Summary",
        "key_findings": [],
        "missing_evidence": [],
        "contradictions": [],
        "human_approval_required": True,
        "source_status": "COMPLETE"
    }
    with pytest.raises(ValidationError):
        AgentRecommendation(**invalid_json)

def test_agent_recommendation_confidence_range():
    invalid_json = {
        "recommended_action": "CONTEST",
        "confidence": 1.5,  # Out of range
        "risk_level": "LOW",
        "evidence_strength": "HIGH",
        "summary": "Summary",
        "key_findings": [],
        "missing_evidence": [],
        "contradictions": [],
        "human_approval_required": True,
        "source_status": "COMPLETE"
    }
    with pytest.raises(ValidationError):
        AgentRecommendation(**invalid_json)

def test_parse_final_json_strips_markdown():
    markdown_text = "```json\n" + json.dumps({
        "recommended_action": "ACCEPT",
        "confidence": 0.5,
        "risk_level": "MEDIUM",
        "evidence_strength": "LOW",
        "summary": "Test",
        "key_findings": [],
        "missing_evidence": [],
        "contradictions": [],
        "human_approval_required": True,
        "source_status": "LIMITED"
    }) + "\n```"
    
    obj = _parse_final_json(markdown_text)
    assert obj.recommended_action == RecommendedAction.ACCEPT

# --------------------------------------------------------------------------- #
# Tool Dispatch Tests
# --------------------------------------------------------------------------- #

def test_execute_tool_unknown_raises_value_error():
    with pytest.raises(ValueError, match="Unknown tool: not_a_real_tool"):
        execute_tool("not_a_real_tool", {}, MagicMock())

# --------------------------------------------------------------------------- #
# Fallback Logic Tests
# --------------------------------------------------------------------------- #

def test_deterministic_fallback_escalates_on_contradiction():
    res = _deterministic_fallback(["payment", "delivery"], contradictions_found=True, completeness=100)
    assert res.ai_status == "FALLBACK"
    assert res.recommended_action == RecommendedAction.ESCALATE
    assert res.risk_level == RiskLevel.HIGH
    assert res.evidence_strength == EvidenceStrength.MEDIUM
    assert "Contradiction detected by rule engine" in res.contradictions

def test_deterministic_fallback_contests_strong_evidence():
    res = _deterministic_fallback(["payment", "delivery", "otp", "communication"], contradictions_found=False, completeness=100)
    assert res.ai_status == "FALLBACK"
    assert res.recommended_action == RecommendedAction.CONTEST
    assert res.risk_level == RiskLevel.LOW
    assert res.evidence_strength == EvidenceStrength.HIGH
    assert not res.missing_evidence

def test_deterministic_fallback_accepts_weak_evidence():
    res = _deterministic_fallback(["payment"], contradictions_found=False, completeness=15)
    assert res.ai_status == "FALLBACK"
    assert res.recommended_action == RecommendedAction.ACCEPT
    assert res.risk_level == RiskLevel.HIGH
    assert res.evidence_strength == EvidenceStrength.LOW
    assert "delivery" in res.missing_evidence

# --------------------------------------------------------------------------- #
# Demo Case Logic Tests (MOCK_VERIFIER=true)
# --------------------------------------------------------------------------- #

@patch("app.agents.investigation_agent.settings.mock_verifier", True)
def test_investigate_mock_strong_case():
    # Case 1: Strong Contest
    res = investigate("case_123", MagicMock(), ["payment", "delivery", "communication", "otp"], False, 100)
    assert res.recommended_action == RecommendedAction.CONTEST
    assert res.ai_status == "OK"
    assert res.confidence == 0.85
    assert not res.contradictions

@patch("app.agents.investigation_agent.settings.mock_verifier", True)
def test_investigate_mock_weak_case():
    # Case 2: Insufficient Evidence
    res = investigate("case_123", MagicMock(), ["payment"], False, 35)
    assert res.recommended_action == RecommendedAction.REQUEST_MORE_EVIDENCE
    assert res.ai_status == "OK"
    assert res.confidence == 0.55
    assert "delivery" in res.missing_evidence

@patch("app.agents.investigation_agent.settings.mock_verifier", True)
def test_investigate_mock_contradiction_case():
    # Case 4: Contradictory Evidence
    res = investigate("case_123", MagicMock(), ["payment", "delivery"], True, 60)
    assert res.recommended_action == RecommendedAction.ESCALATE
    assert res.ai_status == "OK"
    assert len(res.contradictions) > 0

# --------------------------------------------------------------------------- #
# Real Agent Mock Tests (Anthropic Mocked)
# --------------------------------------------------------------------------- #

@patch("app.agents.investigation_agent.settings.mock_verifier", False)
@patch("app.agents.investigation_agent.settings.anthropic_api_key", "fake_key")
@patch("anthropic.Anthropic")
def test_run_anthropic_agent_success(mock_anthropic):
    # Setup mock client
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    
    # Setup mock response without tool calls
    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="text", text=json.dumps({
        "recommended_action": "CONTEST",
        "confidence": 0.9,
        "risk_level": "LOW",
        "evidence_strength": "HIGH",
        "summary": "AI says contest",
        "key_findings": [],
        "missing_evidence": [],
        "contradictions": [],
        "human_approval_required": True,
        "source_status": "COMPLETE"
    }))]
    mock_client.messages.create.return_value = mock_response

    res = investigate("case_123", MagicMock(), ["payment", "delivery"], False, 100)
    assert res.recommended_action == RecommendedAction.CONTEST
    assert res.confidence == 0.9
    assert res.ai_status == "OK"

@patch("app.agents.investigation_agent.settings.mock_verifier", False)
@patch("app.agents.investigation_agent.settings.anthropic_api_key", "fake_key")
@patch("anthropic.Anthropic")
def test_run_anthropic_agent_invalid_json_fallback(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="text", text="Not valid JSON")]
    mock_client.messages.create.return_value = mock_response

    # Even though LLM fails, should fallback to deterministic gracefully
    res = investigate("case_123", MagicMock(), ["payment", "delivery"], False, 100)
    assert res.ai_status == "FALLBACK"
    assert res.recommended_action == RecommendedAction.CONTEST # Deterministic logic for 100% completeness
