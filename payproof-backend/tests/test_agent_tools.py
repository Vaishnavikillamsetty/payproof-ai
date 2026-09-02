import json
from unittest.mock import MagicMock, patch
import pytest
from app.agents.schemas import AgentRecommendation, RecommendedAction, RiskLevel, EvidenceStrength, SourceStatus
from app.agents.investigation_agent import investigate

@patch("app.agents.investigation_agent.settings.mock_verifier", False)
@patch("app.agents.investigation_agent.settings.anthropic_api_key", "fake_key")
@patch("app.agents.investigation_agent.execute_tool")
@patch("anthropic.Anthropic")
def test_run_anthropic_agent_sequential_tools(mock_anthropic, mock_execute_tool):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    
    # Step 1: LLM returns a tool call for get_case_details
    response_1 = MagicMock()
    block_1 = MagicMock(type="tool_use", id="call_1")
    block_1.name = "get_case_details"
    block_1.input = {"case_id": "123"}
    response_1.content = [block_1]
    
    # Step 2: LLM returns a tool call for search_case_evidence
    response_2 = MagicMock()
    block_2 = MagicMock(type="tool_use", id="call_2")
    block_2.name = "search_case_evidence"
    block_2.input = {"case_id": "123"}
    response_2.content = [block_2]
    
    # Step 3: LLM returns final recommendation
    response_3 = MagicMock()
    response_3.content = [MagicMock(type="text", text=json.dumps({
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
    
    # Configure the mock to return these responses sequentially
    mock_client.messages.create.side_effect = [response_1, response_2, response_3]
    
    # Configure execute_tool to return fake tool results
    mock_execute_tool.side_effect = [
        {"status": "open", "amount": 100}, # Result of get_case_details
        {"evidence_count": 2, "evidence": []} # Result of search_case_evidence
    ]

    res = investigate("case_123", MagicMock(), ["payment", "delivery"], False, 100)
    
    # Assert final result
    assert res.recommended_action == RecommendedAction.CONTEST
    assert res.ai_status == "OK"
    
    # Assert tool was actually called
    assert mock_execute_tool.call_count == 2
    calls = mock_execute_tool.call_args_list
    assert calls[0][0][0] == "get_case_details"
    assert calls[0][0][1] == {"case_id": "123"}
    assert calls[1][0][0] == "search_case_evidence"
    assert calls[1][0][1] == {"case_id": "123"}

@patch("app.agents.investigation_agent.settings.mock_verifier", False)
@patch("app.agents.investigation_agent.settings.anthropic_api_key", "fake_key")
@patch("app.agents.investigation_agent.execute_tool")
@patch("anthropic.Anthropic")
def test_run_anthropic_agent_max_steps_limit(mock_anthropic, mock_execute_tool):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    
    # The LLM gets stuck in an infinite tool-calling loop
    infinite_tool_response = MagicMock()
    block_x = MagicMock(type="tool_use", id="call_x")
    block_x.name = "get_case_details"
    block_x.input = {"case_id": "123"}
    infinite_tool_response.content = [block_x]
    
    # After MAX_AGENT_STEPS, it is forced to provide text
    forced_text_response = MagicMock()
    forced_text_response.content = [MagicMock(type="text", text=json.dumps({
        "recommended_action": "REQUEST_MORE_EVIDENCE",
        "confidence": 0.5,
        "risk_level": "MEDIUM",
        "evidence_strength": "LOW",
        "summary": "Forced exit",
        "key_findings": [],
        "missing_evidence": [],
        "contradictions": [],
        "human_approval_required": True,
        "source_status": "PARTIAL"
    }))]
    
    mock_client.messages.create.side_effect = [
        infinite_tool_response, # 1
        infinite_tool_response, # 2
        infinite_tool_response, # 3
        infinite_tool_response, # 4
        infinite_tool_response, # 5 (reaches max steps)
        forced_text_response    # The forced non-tool call
    ]
    
    mock_execute_tool.return_value = {"ok": True}

    res = investigate("case_123", MagicMock(), [], False, 0)
    
    assert mock_client.messages.create.call_count == 6
    assert mock_execute_tool.call_count == 5 # Executed exactly 5 times
    assert res.recommended_action == RecommendedAction.REQUEST_MORE_EVIDENCE
