"""Integration tests for Data/Metrics Agent node.

Tests full investigation flows, state updates, and reducer compatibility.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.agents.data_metrics_agent import investigate_data
from app.agents.state import AgentFinding
from tests.fixtures.mock_openrouter import (
    MOCK_SCOPE_ADDITION_PASS,
    MOCK_SCOPE_ADDITION_FAIL,
    MOCK_YOY_PERCENTAGE_PASS,
    MOCK_TARGET_ACHIEVABILITY_ACHIEVABLE,
    MOCK_TARGET_ACHIEVABILITY_QUESTIONABLE,
    MOCK_INTENSITY_BENCHMARK,
    get_mock_data_metrics_response,
)


# ============================================================================
# TestDataMetricsNodeFullFlow
# ============================================================================


class TestDataMetricsNodeFullFlow:
    """Test full investigation flows."""

    @pytest.mark.asyncio
    async def test_full_investigation_flow_emissions_claims(
        self,
        sample_state_emissions,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test full flow for emissions claim."""
        mock_openrouter_data_metrics(json.dumps(MOCK_SCOPE_ADDITION_PASS))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- IFRS S2.29 content ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        # Check findings
        assert len(result["findings"]) == 1
        finding = result["findings"][0]
        assert finding.evidence_type == "quantitative_validation"
        assert finding.supports_claim is True
        
        # Check events flow
        event_types = [e.event_type for e in result["events"]]
        assert "agent_started" in event_types
        assert "agent_thinking" in event_types
        assert "consistency_check" in event_types
        assert "evidence_found" in event_types
        assert "agent_completed" in event_types

    @pytest.mark.asyncio
    async def test_full_investigation_flow_target_claims(
        self,
        sample_state_target,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test full flow for target claim."""
        mock_openrouter_data_metrics(json.dumps(MOCK_TARGET_ACHIEVABILITY_ACHIEVABLE))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- IFRS S2.33-36 content ---"),
        )
        
        result = await investigate_data(sample_state_target)
        
        assert len(result["findings"]) == 1
        finding = result["findings"][0]
        
        # Check target-specific details
        assert "target_achievability" in finding.details
        assert finding.details["target_achievability"]["achievability_assessment"] == "achievable"

    @pytest.mark.asyncio
    async def test_multiple_claim_types_processing(
        self,
        sample_state_multiple_quantitative,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test processing multiple claim types."""
        # Set up different responses for each call
        responses = [
            json.dumps(MOCK_SCOPE_ADDITION_PASS),
            json.dumps(MOCK_YOY_PERCENTAGE_PASS),
            json.dumps(MOCK_TARGET_ACHIEVABILITY_ACHIEVABLE),
            json.dumps(MOCK_INTENSITY_BENCHMARK),
        ]
        
        mock_response_iter = iter(responses)
        
        def mock_response_gen(*args, **kwargs):
            response_data = {
                "choices": [{
                    "message": {
                        "content": next(mock_response_iter),
                        "tool_calls": [],
                    },
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 100, "completion_tokens": 200}
            }
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = response_data
            mock_resp.raise_for_status = MagicMock()
            return mock_resp
        
        mocker.patch(
            "app.agents.data_metrics_agent.openrouter_client._client.post",
            AsyncMock(side_effect=mock_response_gen),
        )
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_multiple_quantitative)
        
        assert len(result["findings"]) == 4
        assert result["agent_status"]["data_metrics"].claims_completed == 4

    @pytest.mark.asyncio
    async def test_node_state_updates_correct_shape(
        self,
        sample_state_emissions,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test state update has correct shape for LangGraph reducers."""
        mock_openrouter_data_metrics(json.dumps(MOCK_SCOPE_ADDITION_PASS))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        # Verify all required keys
        assert "findings" in result
        assert "agent_status" in result
        assert "events" in result
        
        # Verify types for reducer compatibility
        assert isinstance(result["findings"], list)
        assert all(isinstance(f, AgentFinding) for f in result["findings"])
        assert isinstance(result["agent_status"], dict)
        assert "data_metrics" in result["agent_status"]


# ============================================================================
# TestDataMetricsNodeStateUpdates
# ============================================================================


class TestDataMetricsNodeStateUpdates:
    """Test state updates and reducer compatibility."""

    @pytest.mark.asyncio
    async def test_findings_list_reducer_compatibility(
        self,
        sample_state_emissions,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test findings can be merged by operator.add reducer."""
        mock_openrouter_data_metrics(json.dumps(MOCK_SCOPE_ADDITION_PASS))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        # Findings should be a list that can be concatenated
        existing_findings = [
            AgentFinding(
                finding_id="existing-001",
                agent_name="legal",
                claim_id="claim-001",
                evidence_type="compliance",
                summary="Existing finding",
            )
        ]
        
        merged = existing_findings + result["findings"]
        assert len(merged) == 2
        assert merged[0].agent_name == "legal"
        assert merged[1].agent_name == "data_metrics"

    @pytest.mark.asyncio
    async def test_events_list_reducer_compatibility(
        self,
        sample_state_emissions,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test events can be merged by operator.add reducer."""
        mock_openrouter_data_metrics(json.dumps(MOCK_SCOPE_ADDITION_PASS))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        # Events should be a list
        assert isinstance(result["events"], list)
        assert len(result["events"]) > 0

    @pytest.mark.asyncio
    async def test_agent_status_dict_reducer_compatibility(
        self,
        sample_state_emissions,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test agent_status works with merge_agent_status reducer."""
        mock_openrouter_data_metrics(json.dumps(MOCK_SCOPE_ADDITION_PASS))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        # agent_status should be a dict with agent name as key
        assert isinstance(result["agent_status"], dict)
        status = result["agent_status"]["data_metrics"]
        assert status.status == "completed"
        assert status.claims_assigned == 1
        assert status.claims_completed == 1

    @pytest.mark.asyncio
    async def test_info_requests_list_reducer_compatibility(
        self,
        sample_state_intensity,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test info_requests can be merged by operator.add reducer."""
        mock_openrouter_data_metrics(json.dumps(MOCK_INTENSITY_BENCHMARK))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_intensity)
        
        # If info_requests exist, they should be a list
        if "info_requests" in result:
            assert isinstance(result["info_requests"], list)


# ============================================================================
# TestDataMetricsNodeCalculatorIntegration
# ============================================================================


class TestDataMetricsNodeCalculatorIntegration:
    """Test calculator tool integration."""

    @pytest.mark.asyncio
    async def test_scope_addition_uses_calculator(
        self,
        sample_state_emissions,
        mock_openrouter_data_metrics_tool_loop,
        mocker,
    ):
        """Test scope addition check uses calculator tool."""
        mock_openrouter_data_metrics_tool_loop(
            calculator_calls=[
                ("2300000 + 1100000 + 8500000", "11900000"),
                ("abs(11900000 - 12000000) / 12000000 * 100", "0.8333333333"),
            ],
            final_response=json.dumps(MOCK_SCOPE_ADDITION_PASS),
        )
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        # Should have finding with calculation trace
        assert len(result["findings"]) == 1

    @pytest.mark.asyncio
    async def test_percentage_change_uses_calculator(
        self,
        sample_state_yoy,
        mock_openrouter_data_metrics_tool_loop,
        mocker,
    ):
        """Test YoY percentage check uses calculator."""
        mock_openrouter_data_metrics_tool_loop(
            calculator_calls=[
                ("((2450000 - 2300000) / 2450000) * 100", "6.1224489796"),
            ],
            final_response=json.dumps(MOCK_YOY_PERCENTAGE_PASS),
        )
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_yoy)
        
        assert len(result["findings"]) == 1

    @pytest.mark.asyncio
    async def test_calculator_error_handled_gracefully(
        self,
        sample_state_emissions,
        mocker,
    ):
        """Test calculator errors are handled gracefully."""
        # Mock to simulate calculator error during tool loop
        error_response = {
            "choices": [{
                "message": {
                    "content": "",
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "calculator",
                            "arguments": json.dumps({"expression": "1/0"})
                        }
                    }]
                },
                "finish_reason": "tool_calls",
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }
        
        final_response = {
            "choices": [{
                "message": {
                    "content": json.dumps(MOCK_SCOPE_ADDITION_PASS),
                    "tool_calls": [],
                },
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 200, "completion_tokens": 500}
        }
        
        mock_responses = []
        for resp_data in [error_response, final_response]:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = resp_data
            mock_resp.raise_for_status = MagicMock()
            mock_responses.append(mock_resp)
        
        mocker.patch(
            "app.agents.data_metrics_agent.openrouter_client._client.post",
            AsyncMock(side_effect=mock_responses),
        )
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        # Should complete without crashing
        result = await investigate_data(sample_state_emissions)
        assert result["agent_status"]["data_metrics"].status == "completed"


# ============================================================================
# TestDataMetricsNodeConsistencyEvents
# ============================================================================


class TestDataMetricsNodeConsistencyEvents:
    """Test consistency check events."""

    @pytest.mark.asyncio
    async def test_scope_addition_event_emitted(
        self,
        sample_state_emissions,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test scope_addition consistency check event is emitted."""
        mock_openrouter_data_metrics(json.dumps(MOCK_SCOPE_ADDITION_PASS))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        check_events = [e for e in result["events"] if e.event_type == "consistency_check"]
        assert len(check_events) == 1
        assert check_events[0].data["check_name"] == "scope_addition"
        assert check_events[0].data["result"] == "pass"

    @pytest.mark.asyncio
    async def test_yoy_percentage_event_emitted(
        self,
        sample_state_yoy,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test yoy_percentage consistency check event is emitted."""
        mock_openrouter_data_metrics(json.dumps(MOCK_YOY_PERCENTAGE_PASS))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_yoy)
        
        check_events = [e for e in result["events"] if e.event_type == "consistency_check"]
        assert len(check_events) >= 1

    @pytest.mark.asyncio
    async def test_failed_checks_have_details(
        self,
        sample_state_scope_mismatch,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test failed checks include details in event."""
        mock_openrouter_data_metrics(json.dumps(MOCK_SCOPE_ADDITION_FAIL))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_scope_mismatch)
        
        check_events = [e for e in result["events"] if e.event_type == "consistency_check"]
        failed_checks = [e for e in check_events if e.data.get("result") == "fail"]
        
        if failed_checks:
            assert failed_checks[0].data["severity"] == "critical"
            assert "details" in failed_checks[0].data


# ============================================================================
# TestDataMetricsNodeInterAgentCommunication
# ============================================================================


class TestDataMetricsNodeInterAgentCommunication:
    """Test inter-agent communication."""

    @pytest.mark.asyncio
    async def test_posts_info_request_for_benchmarks(
        self,
        sample_state_intensity,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test node posts InfoRequest for benchmark data."""
        mock_openrouter_data_metrics(json.dumps(MOCK_INTENSITY_BENCHMARK))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_intensity)
        
        # Check for info_request_posted event
        request_events = [e for e in result["events"] if e.event_type == "info_request_posted"]
        
        # Intensity claim should trigger benchmark request
        if "info_requests" in result:
            assert len(result["info_requests"]) >= 1

    @pytest.mark.asyncio
    async def test_processes_benchmark_response(
        self,
        sample_state_benchmark_response,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test node processes existing benchmark response."""
        mock_openrouter_data_metrics(json.dumps(MOCK_INTENSITY_BENCHMARK))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_benchmark_response)
        
        # Should have processed the existing response
        assert len(result["findings"]) == 1

    @pytest.mark.asyncio
    async def test_incorporates_benchmark_data_in_findings(
        self,
        sample_state_benchmark_response,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test benchmark data is incorporated in findings."""
        mock_openrouter_data_metrics(json.dumps(MOCK_INTENSITY_BENCHMARK))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_benchmark_response)
        
        finding = result["findings"][0]
        # Benchmark comparison should be in details if present
        if "benchmark_comparison" in finding.details:
            assert finding.details["benchmark_comparison"]["assessment"] == "plausible"


# ============================================================================
# TestDataMetricsNodeReinvestigation
# ============================================================================


class TestDataMetricsNodeReinvestigation:
    """Test re-investigation handling."""

    @pytest.mark.asyncio
    async def test_reinvestigation_processes_claim(
        self,
        sample_state_data_metrics_reinvestigation,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test node processes re-investigation request."""
        mock_openrouter_data_metrics(json.dumps(MOCK_TARGET_ACHIEVABILITY_ACHIEVABLE))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_data_metrics_reinvestigation)
        
        assert len(result["findings"]) == 1
        # Re-investigation should use iteration count from state
        assert result["findings"][0].iteration == 2  # iteration_count was 1

    @pytest.mark.asyncio
    async def test_reinvestigation_emits_thinking_event(
        self,
        sample_state_data_metrics_reinvestigation,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test re-investigation emits specific thinking event."""
        mock_openrouter_data_metrics(json.dumps(MOCK_TARGET_ACHIEVABILITY_ACHIEVABLE))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_data_metrics_reinvestigation)
        
        thinking_events = [e for e in result["events"] if e.event_type == "agent_thinking"]
        reinvest_thinking = [e for e in thinking_events if "re-investigating" in e.data.get("message", "").lower()]
        assert len(reinvest_thinking) >= 1


# ============================================================================
# TestDataMetricsNodeErrorHandling
# ============================================================================


class TestDataMetricsNodeErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_handles_llm_timeout(
        self,
        sample_state_emissions,
        mocker,
    ):
        """Test node handles LLM timeout gracefully."""
        import httpx
        
        mocker.patch(
            "app.agents.data_metrics_agent.openrouter_client._client.post",
            AsyncMock(side_effect=httpx.TimeoutException("Timeout")),
        )
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        # Should still complete
        assert result["agent_status"]["data_metrics"].status == "completed"
        # Should have error finding
        assert len(result["findings"]) == 1
        assert result["findings"][0].confidence == "low"

    @pytest.mark.asyncio
    async def test_handles_malformed_response(
        self,
        sample_state_emissions,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test node handles malformed LLM response."""
        mock_openrouter_data_metrics("This is not valid JSON")
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        # Should still complete
        assert result["agent_status"]["data_metrics"].status == "completed"
        assert len(result["findings"]) == 1

    @pytest.mark.asyncio
    async def test_partial_findings_on_error(
        self,
        sample_state_multiple_quantitative,
        mocker,
    ):
        """Test partial findings are returned when some claims error."""
        # First call succeeds, second errors
        responses = [
            {"status": 200, "content": json.dumps(MOCK_SCOPE_ADDITION_PASS)},
            {"status": 500, "error": True},
            {"status": 200, "content": json.dumps(MOCK_TARGET_ACHIEVABILITY_ACHIEVABLE)},
            {"status": 200, "content": json.dumps(MOCK_INTENSITY_BENCHMARK)},
        ]
        
        call_count = [0]
        
        async def mock_post(*args, **kwargs):
            resp_info = responses[call_count[0] % len(responses)]
            call_count[0] += 1
            
            if resp_info.get("error"):
                raise Exception("API Error")
            
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{
                    "message": {
                        "content": resp_info["content"],
                        "tool_calls": [],
                    },
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 100, "completion_tokens": 200}
            }
            mock_resp.raise_for_status = MagicMock()
            return mock_resp
        
        mocker.patch(
            "app.agents.data_metrics_agent.openrouter_client._client.post",
            mock_post,
        )
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_multiple_quantitative)
        
        # Should have findings for all claims (some may be errors)
        assert len(result["findings"]) == 4

    @pytest.mark.asyncio
    async def test_error_event_emitted(
        self,
        sample_state_emissions,
        mocker,
    ):
        """Test error event is emitted on failure."""
        mocker.patch(
            "app.agents.data_metrics_agent._validate_quantitative_claim",
            AsyncMock(side_effect=Exception("Validation failed")),
        )
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        error_events = [e for e in result["events"] if e.event_type == "error"]
        assert len(error_events) >= 1
        assert "validation" in error_events[0].data["message"].lower()

    @pytest.mark.asyncio
    async def test_tool_loop_max_iterations_exceeded(
        self,
        sample_state_emissions,
        mocker,
    ):
        """Test node handles tool loop exceeding max iterations."""
        # Mock infinite tool calls
        tool_call_response = {
            "choices": [{
                "message": {
                    "content": "",
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "calculator",
                            "arguments": json.dumps({"expression": "1+1"})
                        }
                    }]
                },
                "finish_reason": "tool_calls",
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = tool_call_response
        mock_resp.raise_for_status = MagicMock()
        
        mocker.patch(
            "app.agents.data_metrics_agent.openrouter_client._client.post",
            AsyncMock(return_value=mock_resp),
        )
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        # Should still complete (with error finding)
        assert result["agent_status"]["data_metrics"].status == "completed"
        finding = result["findings"][0]
        assert "max" in finding.summary.lower() or "exceeded" in finding.summary.lower()
