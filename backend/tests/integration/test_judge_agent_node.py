"""Integration tests for Judge Agent node invocation (FRD 11).

Tests the full judge_evidence node with mocked external dependencies.
All tests mock OpenRouter API calls to avoid consuming tokens.
"""

import pytest

from app.agents.judge_agent import judge_evidence
from app.agents.graph import should_continue_or_compile
from app.agents.state import ReinvestigationRequest
from tests.fixtures.mock_openrouter import get_mock_judge_verdict_response
from tests.fixtures.sample_states import (
    create_state_with_verified_evidence,
    create_state_with_insufficient_evidence,
    create_state_with_contradicting_evidence,
    create_state_with_no_evidence,
    create_state_with_errored_agents,
    create_state_for_reinvestigation,
    create_state_at_max_iterations,
    create_state_with_multiple_claims_mixed_verdicts,
)


# ============================================================================
# Full Flow Tests
# ============================================================================


class TestJudgeNodeFullFlow:
    """Tests for complete judge_evidence node execution."""

    @pytest.mark.asyncio
    async def test_judge_node_produces_verified_verdict(
        self, mock_openrouter_judge
    ):
        """Test Judge produces verified verdict with sufficient evidence."""
        state = create_state_with_verified_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("verified"))
        
        result = await judge_evidence(state)
        
        assert "verdicts" in result
        assert len(result["verdicts"]) >= 1
        
        # Should have at least one verified verdict
        verified = [v for v in result["verdicts"] if v.verdict == "verified"]
        assert len(verified) >= 1
        
        # No reinvestigation needed for verified
        assert result["reinvestigation_requests"] == []

    @pytest.mark.asyncio
    async def test_judge_node_produces_contradicted_verdict(
        self, mock_openrouter_judge
    ):
        """Test Judge produces contradicted verdict when evidence conflicts."""
        state = create_state_with_contradicting_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("contradicted"))
        
        result = await judge_evidence(state)
        
        assert len(result["verdicts"]) >= 1
        
        # Verdict should be contradicted (majority contradict)
        verdict = result["verdicts"][0]
        assert verdict.verdict == "contradicted"
        assert "CONTRADICTED" in verdict.reasoning

    @pytest.mark.asyncio
    async def test_judge_node_produces_unverified_verdict(
        self, mock_openrouter_judge
    ):
        """Test Judge produces unverified verdict when no evidence found."""
        state = create_state_with_no_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("unverified"))
        
        result = await judge_evidence(state)
        
        assert len(result["verdicts"]) >= 1
        
        verdict = result["verdicts"][0]
        assert verdict.verdict == "unverified"
        assert "UNVERIFIED" in verdict.reasoning

    @pytest.mark.asyncio
    async def test_judge_node_produces_insufficient_verdict(
        self, mock_openrouter_judge
    ):
        """Test Judge produces insufficient_evidence verdict with weak evidence."""
        state = create_state_with_insufficient_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("insufficient"))
        
        result = await judge_evidence(state)
        
        assert len(result["verdicts"]) >= 1
        
        verdict = result["verdicts"][0]
        assert verdict.verdict == "insufficient_evidence"
        assert "INSUFFICIENT" in verdict.reasoning


# ============================================================================
# Re-investigation Cycle Tests
# ============================================================================


class TestJudgeNodeReinvestigation:
    """Tests for re-investigation request generation."""

    @pytest.mark.asyncio
    async def test_generates_reinvestigation_request(
        self, mock_openrouter_judge
    ):
        """Test Judge generates request when evidence insufficient."""
        state = create_state_with_insufficient_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("insufficient"))
        
        result = await judge_evidence(state)
        
        assert len(result["reinvestigation_requests"]) >= 1
        
        req = result["reinvestigation_requests"][0]
        assert len(req.target_agents) >= 1
        assert req.evidence_gap != ""
        assert req.claim_id == state["claims"][0].claim_id

    @pytest.mark.asyncio
    async def test_increments_iteration_count(
        self, mock_openrouter_judge
    ):
        """Test iteration_count increases when reinvestigation requested."""
        state = create_state_with_insufficient_evidence()
        initial_iteration = state.get("iteration_count", 0)
        mock_openrouter_judge(get_mock_judge_verdict_response("insufficient"))
        
        result = await judge_evidence(state)
        
        # If reinvestigation requested, iteration should increment
        if result["reinvestigation_requests"]:
            assert result["iteration_count"] > initial_iteration

    @pytest.mark.asyncio
    async def test_no_reinvestigation_at_max_iterations(
        self, mock_openrouter_judge
    ):
        """Test final verdicts issued at max iterations."""
        state = create_state_at_max_iterations()
        mock_openrouter_judge(get_mock_judge_verdict_response("insufficient"))
        
        result = await judge_evidence(state)
        
        # Should not request reinvestigation at max iterations
        assert result["reinvestigation_requests"] == []
        
        # Should still produce verdicts
        assert len(result["verdicts"]) >= 1

    @pytest.mark.asyncio
    async def test_reinvestigation_request_has_refined_queries(
        self, mock_openrouter_judge
    ):
        """Test reinvestigation request includes refined queries."""
        state = create_state_with_insufficient_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("insufficient"))
        
        result = await judge_evidence(state)
        
        if result["reinvestigation_requests"]:
            req = result["reinvestigation_requests"][0]
            assert len(req.refined_queries) >= 1
            assert req.required_evidence != ""

    @pytest.mark.asyncio
    async def test_second_iteration_state(
        self, mock_openrouter_judge
    ):
        """Test judge processes second iteration state correctly."""
        state = create_state_for_reinvestigation()
        mock_openrouter_judge(get_mock_judge_verdict_response("insufficient"))
        
        result = await judge_evidence(state)
        
        # Should still be able to produce verdicts
        assert len(result["verdicts"]) >= 1
        
        # iteration_count from state should be respected
        assert result["iteration_count"] >= state["iteration_count"]


# ============================================================================
# State Update Tests
# ============================================================================


class TestJudgeNodeStateUpdate:
    """Tests for state update format and compatibility."""

    @pytest.mark.asyncio
    async def test_state_update_format(
        self, mock_openrouter_judge
    ):
        """Test returns correctly formatted partial state."""
        state = create_state_with_verified_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("verified"))
        
        result = await judge_evidence(state)
        
        # All required keys present
        assert "verdicts" in result
        assert "reinvestigation_requests" in result
        assert "iteration_count" in result
        assert "events" in result

    @pytest.mark.asyncio
    async def test_verdicts_have_required_fields(
        self, mock_openrouter_judge
    ):
        """Test each verdict has all required fields."""
        state = create_state_with_verified_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("verified"))
        
        result = await judge_evidence(state)
        
        for verdict in result["verdicts"]:
            assert verdict.claim_id is not None
            assert verdict.verdict in ["verified", "unverified", "contradicted", "insufficient_evidence"]
            assert verdict.reasoning != ""
            assert verdict.ifrs_mapping is not None
            assert verdict.evidence_summary is not None
            assert verdict.iteration_count >= 1

    @pytest.mark.asyncio
    async def test_verdict_includes_ifrs_mapping(
        self, mock_openrouter_judge
    ):
        """Test verdicts include IFRS paragraph mappings."""
        state = create_state_with_verified_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("verified"))
        
        result = await judge_evidence(state)
        
        verdict = result["verdicts"][0]
        assert isinstance(verdict.ifrs_mapping, list)
        # Should have at least one IFRS mapping
        assert len(verdict.ifrs_mapping) >= 1
        
        for mapping in verdict.ifrs_mapping:
            assert "paragraph" in mapping
            assert "status" in mapping

    @pytest.mark.asyncio
    async def test_verdict_includes_evidence_summary(
        self, mock_openrouter_judge
    ):
        """Test verdicts include evidence summary."""
        state = create_state_with_verified_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("verified"))
        
        result = await judge_evidence(state)
        
        verdict = result["verdicts"][0]
        summary = verdict.evidence_summary
        
        assert "findings_count" in summary
        assert "agents_consulted" in summary
        assert summary["findings_count"] >= 0

    @pytest.mark.asyncio
    async def test_reducer_compatibility(
        self, mock_openrouter_judge
    ):
        """Test verdicts list is compatible with operator.add reducer."""
        state = create_state_with_verified_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("verified"))
        
        result = await judge_evidence(state)
        
        # Must be a list for the operator.add reducer
        assert isinstance(result["verdicts"], list)
        assert isinstance(result["reinvestigation_requests"], list)
        assert isinstance(result["events"], list)


# ============================================================================
# StreamEvent Tests
# ============================================================================


class TestJudgeNodeEvents:
    """Tests for StreamEvent emissions."""

    @pytest.mark.asyncio
    async def test_emits_agent_started_event(
        self, mock_openrouter_judge
    ):
        """Test agent_started event is emitted."""
        state = create_state_with_verified_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("verified"))
        
        result = await judge_evidence(state)
        
        started_events = [e for e in result["events"] if e.event_type == "agent_started"]
        assert len(started_events) >= 1
        assert started_events[0].agent_name == "judge"

    @pytest.mark.asyncio
    async def test_emits_verdict_issued_events(
        self, mock_openrouter_judge
    ):
        """Test verdict_issued event emitted for each claim."""
        state = create_state_with_verified_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("verified"))
        
        result = await judge_evidence(state)
        
        verdict_events = [e for e in result["events"] if e.event_type == "verdict_issued"]
        
        # Should have one verdict event per claim
        assert len(verdict_events) == len(state["claims"])
        
        # Each event should have claim_id and verdict
        for event in verdict_events:
            assert "claim_id" in event.data
            assert "verdict" in event.data

    @pytest.mark.asyncio
    async def test_emits_reinvestigation_event(
        self, mock_openrouter_judge
    ):
        """Test reinvestigation event emitted when requests generated."""
        state = create_state_with_insufficient_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("insufficient"))
        
        result = await judge_evidence(state)
        
        if result["reinvestigation_requests"]:
            reinvest_events = [e for e in result["events"] if e.event_type == "reinvestigation"]
            assert len(reinvest_events) >= 1
            
            event = reinvest_events[0]
            assert "claim_ids" in event.data
            assert "target_agents" in event.data

    @pytest.mark.asyncio
    async def test_emits_agent_completed_event(
        self, mock_openrouter_judge
    ):
        """Test agent_completed event is emitted."""
        state = create_state_with_verified_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("verified"))
        
        result = await judge_evidence(state)
        
        completed_events = [e for e in result["events"] if e.event_type == "agent_completed"]
        assert len(completed_events) >= 1
        
        event = completed_events[0]
        assert event.agent_name == "judge"
        assert "verdicts_issued" in event.data
        assert "reinvestigation_requests" in event.data

    @pytest.mark.asyncio
    async def test_emits_evidence_evaluation_event(
        self, mock_openrouter_judge
    ):
        """Test evidence_evaluation event is emitted for each claim."""
        state = create_state_with_verified_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("verified"))
        
        result = await judge_evidence(state)
        
        eval_events = [e for e in result["events"] if e.event_type == "evidence_evaluation"]
        
        # Should have one evaluation event per claim
        assert len(eval_events) == len(state["claims"])
        
        for event in eval_events:
            assert "overall_score" in event.data
            assert "sufficiency" in event.data
            assert "consistency" in event.data


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestJudgeNodeErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_handles_empty_claims(
        self, mock_openrouter_judge
    ):
        """Test gracefully handles state with no claims."""
        from tests.fixtures.sample_states import create_base_state
        
        state = create_base_state(claims=[])
        mock_openrouter_judge(get_mock_judge_verdict_response("verified"))
        
        result = await judge_evidence(state)
        
        assert result["verdicts"] == []
        assert result["reinvestigation_requests"] == []
        assert len(result["events"]) >= 2  # started + completed

    @pytest.mark.asyncio
    async def test_handles_empty_findings(
        self, mock_openrouter_judge
    ):
        """Test handles claims with no findings."""
        state = create_state_with_no_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("unverified"))
        
        result = await judge_evidence(state)
        
        # Should produce unverified verdicts
        assert len(result["verdicts"]) >= 1
        assert result["verdicts"][0].verdict == "unverified"

    @pytest.mark.asyncio
    async def test_handles_errored_agents(
        self, mock_openrouter_judge
    ):
        """Test accounts for errored agents in evaluation."""
        state = create_state_with_errored_agents()
        mock_openrouter_judge(get_mock_judge_verdict_response("insufficient"))
        
        result = await judge_evidence(state)
        
        # Should still produce verdicts
        assert len(result["verdicts"]) >= 1
        
        # Errored agents should be noted in evidence summary
        verdict = result["verdicts"][0]
        assert verdict.evidence_summary is not None

    @pytest.mark.asyncio
    async def test_handles_llm_error_gracefully(
        self, mock_openrouter_judge_error
    ):
        """Test falls back to rule-based when LLM fails."""
        state = create_state_with_contradicting_evidence()
        mock_openrouter_judge_error(Exception("API timeout"))
        
        result = await judge_evidence(state)
        
        # Should still produce verdicts using rule-based logic
        assert len(result["verdicts"]) >= 1
        
        # Verdict should be based on evaluation (contradicted)
        verdict = result["verdicts"][0]
        assert verdict.verdict in ["contradicted", "insufficient_evidence"]

    @pytest.mark.asyncio
    async def test_handles_multiple_claims(
        self, mock_openrouter_judge
    ):
        """Test processes multiple claims correctly."""
        state = create_state_with_multiple_claims_mixed_verdicts()
        mock_openrouter_judge(get_mock_judge_verdict_response("verified"))
        
        result = await judge_evidence(state)
        
        # Should have verdict for each claim
        assert len(result["verdicts"]) == len(state["claims"])
        
        # Different claims should potentially have different verdicts
        verdicts_set = set(v.verdict for v in result["verdicts"])
        # At least one type of verdict
        assert len(verdicts_set) >= 1


# ============================================================================
# Conditional Edge Integration Tests
# ============================================================================


class TestConditionalEdgeIntegration:
    """Tests for should_continue_or_compile conditional edge routing."""

    def test_routes_to_orchestrate_with_requests(self):
        """Test routing back when reinvestigation_requests exist."""
        state = {
            "reinvestigation_requests": [
                ReinvestigationRequest(
                    claim_id="claim-001",
                    target_agents=["geography"],
                    evidence_gap="Need satellite imagery",
                    refined_queries=["Verify location"],
                    required_evidence="NDVI analysis",
                )
            ],
            "iteration_count": 1,
            "max_iterations": 3,
        }
        
        result = should_continue_or_compile(state)
        
        assert result == "orchestrate"

    def test_routes_to_compile_when_empty(self):
        """Test routing to compile when no reinvestigation requests."""
        state = {
            "reinvestigation_requests": [],
            "iteration_count": 1,
            "max_iterations": 3,
        }
        
        result = should_continue_or_compile(state)
        
        assert result == "compile_report"

    def test_routes_to_compile_at_max_iterations(self):
        """Test routing to compile at max iterations even with requests."""
        state = {
            "reinvestigation_requests": [
                ReinvestigationRequest(
                    claim_id="claim-001",
                    target_agents=["geography"],
                    evidence_gap="Need satellite imagery",
                    refined_queries=["Verify location"],
                    required_evidence="NDVI analysis",
                )
            ],
            "iteration_count": 3,
            "max_iterations": 3,
        }
        
        result = should_continue_or_compile(state)
        
        assert result == "compile_report"

    @pytest.mark.asyncio
    async def test_judge_output_compatible_with_edge(
        self, mock_openrouter_judge
    ):
        """Test judge output works with conditional edge function."""
        state = create_state_with_insufficient_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("insufficient"))
        
        result = await judge_evidence(state)
        
        # Build state with judge output
        test_state = {
            "reinvestigation_requests": result["reinvestigation_requests"],
            "iteration_count": result["iteration_count"],
            "max_iterations": 3,
        }
        
        # Should route appropriately based on requests
        edge_result = should_continue_or_compile(test_state)
        
        if result["reinvestigation_requests"]:
            assert edge_result == "orchestrate"
        else:
            assert edge_result == "compile_report"


# ============================================================================
# IFRS Mapping Integration Tests
# ============================================================================


class TestJudgeNodeIfrsMapping:
    """Tests for IFRS mapping in verdicts."""

    @pytest.mark.asyncio
    async def test_verdict_includes_ifrs_mapping_from_claim(
        self, mock_openrouter_judge
    ):
        """Test verdict includes IFRS mapping from claim."""
        state = create_state_with_verified_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("verified"))
        
        result = await judge_evidence(state)
        
        verdict = result["verdicts"][0]
        
        # Claim has IFRS paragraphs defined
        claim = state["claims"][0]
        if claim.ifrs_paragraphs:
            paragraphs = [m["paragraph"] for m in verdict.ifrs_mapping]
            # Should include at least one from the claim
            assert any(p in paragraphs for p in claim.ifrs_paragraphs) or len(paragraphs) > 0

    @pytest.mark.asyncio
    async def test_maps_from_legal_agent_findings(
        self, mock_openrouter_judge
    ):
        """Test extracts IFRS mapping from Legal Agent findings."""
        state = create_state_with_verified_evidence()
        mock_openrouter_judge(get_mock_judge_verdict_response("verified"))
        
        result = await judge_evidence(state)
        
        verdict = result["verdicts"][0]
        
        # Should have compliance status from legal agent
        statuses = [m["status"] for m in verdict.ifrs_mapping]
        assert len(statuses) >= 1
        # Legal agent should provide "compliant" status for supporting findings
        assert any(s in statuses for s in ["compliant", "partial", "pending"])
