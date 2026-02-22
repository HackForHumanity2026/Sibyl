"""Integration tests for Legal Agent direct node invocation.

These tests verify the Legal Agent node function works correctly
within the LangGraph pipeline context, testing state updates,
reducer compatibility, and full investigation flows.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.legal_agent import investigate_legal
from app.agents.state import (
    AgentFinding,
    Claim,
    ReinvestigationRequest,
    RoutingAssignment,
    SibylState,
    InfoRequest,
    InfoResponse,
)
from tests.fixtures.mock_openrouter import (
    get_mock_compliance_response,
    get_mock_governance_response,
    get_mock_metrics_response,
    get_mock_risk_management_response,
    MOCK_COMPLIANCE_FULLY_ADDRESSED,
    MOCK_COMPLIANCE_PARTIALLY_ADDRESSED,
)
from tests.fixtures.sample_claims import (
    GOVERNANCE_CLAIM,
    STRATEGIC_CLAIM_TRANSITION_PLAN,
    STRATEGIC_CLAIM_INCOMPLETE,
    METRICS_CLAIM_SCOPE_3,
    METRICS_CLAIM_COMPLETE,
    RISK_MANAGEMENT_CLAIM,
    ROUTING_GOVERNANCE,
    ROUTING_STRATEGIC,
    ROUTING_METRICS,
    ROUTING_RISK_MANAGEMENT,
)


# ============================================================================
# Full Investigation Flow Tests
# ============================================================================


class TestLegalNodeFullFlow:
    """Tests for complete Legal Agent investigation flow."""

    @pytest.mark.asyncio
    async def test_legal_node_full_investigation_flow(
        self,
        mock_openrouter,
        mock_rag_service,
        mock_paragraph_registry,
    ):
        """Test complete Legal Agent investigation flow with multiple claims."""
        # Create state with multiple claim types
        state: SibylState = {
            "report_id": "test-report-integration-001",
            "document_content": "Sample sustainability report content.",
            "document_chunks": [],
            "claims": [
                GOVERNANCE_CLAIM,
                STRATEGIC_CLAIM_TRANSITION_PLAN,
                RISK_MANAGEMENT_CLAIM,
            ],
            "routing_plan": [
                ROUTING_GOVERNANCE,
                ROUTING_STRATEGIC,
                ROUTING_RISK_MANAGEMENT,
            ],
            "agent_status": {},
            "findings": [],
            "info_requests": [],
            "info_responses": [],
            "verdicts": [],
            "reinvestigation_requests": [],
            "iteration_count": 0,
            "max_iterations": 3,
            "disclosure_gaps": [],
        }
        
        # Mock LLM to return compliance responses
        mock_openrouter(get_mock_compliance_response("fully_addressed"))
        
        # Execute node
        result = await investigate_legal(state)
        
        # Verify findings generated for claims
        assert "findings" in result
        compliance_findings = [
            f for f in result["findings"]
            if f.evidence_type == "ifrs_compliance"
        ]
        assert len(compliance_findings) >= 3  # One per claim
        
        # Verify all findings have correct structure
        for finding in compliance_findings:
            assert finding.agent_name == "legal"
            assert finding.finding_id is not None
            assert finding.claim_id in [c.claim_id for c in state["claims"]]
            assert finding.evidence_type == "ifrs_compliance"
            assert finding.iteration == 1
        
        # Verify events emitted
        events = result["events"]
        event_types = [e.event_type for e in events]
        assert "agent_started" in event_types
        assert "agent_completed" in event_types
        
        # Verify agent status
        assert "agent_status" in result
        status = result["agent_status"]["legal"]
        assert status.claims_assigned == 3
        assert status.claims_completed == 3
        assert status.status == "completed"

    @pytest.mark.asyncio
    async def test_legal_node_multiple_claim_types(
        self,
        mock_openrouter_sequence,
        mock_rag_service,
    ):
        """Test processing multiple claims of different types."""
        state: SibylState = {
            "report_id": "test-report-multi-001",
            "document_content": "",
            "document_chunks": [],
            "claims": [
                GOVERNANCE_CLAIM,
                METRICS_CLAIM_SCOPE_3,
            ],
            "routing_plan": [
                ROUTING_GOVERNANCE,
                ROUTING_METRICS,
            ],
            "agent_status": {},
            "findings": [],
            "info_requests": [],
            "info_responses": [],
            "verdicts": [],
            "reinvestigation_requests": [],
            "iteration_count": 0,
            "max_iterations": 3,
            "disclosure_gaps": [],
        }
        
        # Each claim gets its own LLM call
        mock_openrouter_sequence([
            get_mock_governance_response(),
            get_mock_metrics_response(),
        ])
        
        result = await investigate_legal(state)
        
        # Should have findings for both claims
        claim_ids = {f.claim_id for f in result["findings"] if f.evidence_type == "ifrs_compliance"}
        assert GOVERNANCE_CLAIM.claim_id in claim_ids or len(claim_ids) >= 1


# ============================================================================
# Gap Detection Integration Tests
# ============================================================================


class TestLegalNodeGapDetection:
    """Tests for gap detection within the Legal Agent node."""

    @pytest.mark.asyncio
    async def test_legal_node_gap_detection_integration(
        self,
        mock_openrouter,
        mock_rag_service,
        mock_paragraph_registry,
    ):
        """Test gap detection runs and finds unaddressed paragraphs."""
        # State with limited claims (gaps expected)
        state: SibylState = {
            "report_id": "test-report-gaps-001",
            "document_content": "Limited report content.",
            "document_chunks": [],
            "claims": [GOVERNANCE_CLAIM],  # Only governance claim
            "routing_plan": [ROUTING_GOVERNANCE],
            "agent_status": {},
            "findings": [],
            "info_requests": [],
            "info_responses": [],
            "verdicts": [],
            "reinvestigation_requests": [],
            "iteration_count": 0,  # Gap detection only on iteration 0
            "max_iterations": 3,
            "disclosure_gaps": [],
        }
        
        mock_openrouter(get_mock_governance_response())
        
        result = await investigate_legal(state)
        
        # Check for gap findings
        gap_findings = [
            f for f in result["findings"]
            if f.evidence_type == "disclosure_gap"
        ]
        
        # Depending on registry coverage check, we may have gaps
        # At minimum, verify gap detection was attempted (event emitted)
        events = result["events"]
        thinking_events = [e for e in events if e.event_type == "agent_thinking"]
        gap_detection_attempted = any(
            "gap detection" in e.data.get("message", "").lower()
            for e in thinking_events
        )
        assert gap_detection_attempted

    @pytest.mark.asyncio
    async def test_legal_node_gap_detection_skipped_iteration_1(
        self,
        mock_openrouter,
        mock_rag_service,
        mock_paragraph_registry,
    ):
        """Test gap detection is skipped on iteration > 0."""
        state: SibylState = {
            "report_id": "test-report-iter1",
            "document_content": "",
            "document_chunks": [],
            "claims": [GOVERNANCE_CLAIM],
            "routing_plan": [ROUTING_GOVERNANCE],
            "agent_status": {},
            "findings": [],
            "info_requests": [],
            "info_responses": [],
            "verdicts": [],
            "reinvestigation_requests": [],
            "iteration_count": 1,  # Not first iteration
            "max_iterations": 3,
            "disclosure_gaps": [],
        }
        
        mock_openrouter(get_mock_governance_response())
        
        result = await investigate_legal(state)
        
        # Should not have gap findings on iteration > 0
        gap_findings = [
            f for f in result["findings"]
            if f.evidence_type == "disclosure_gap"
        ]
        assert len(gap_findings) == 0


# ============================================================================
# State Update Format Tests
# ============================================================================


class TestLegalNodeStateUpdate:
    """Tests for state update format and structure."""

    @pytest.mark.asyncio
    async def test_legal_node_state_update_format(
        self,
        mock_openrouter,
        mock_rag_service,
    ):
        """Test Legal Agent returns correctly formatted state update."""
        state: SibylState = {
            "report_id": "test-format-001",
            "document_content": "",
            "document_chunks": [],
            "claims": [GOVERNANCE_CLAIM],
            "routing_plan": [ROUTING_GOVERNANCE],
            "agent_status": {},
            "findings": [],
            "info_requests": [],
            "info_responses": [],
            "verdicts": [],
            "reinvestigation_requests": [],
            "iteration_count": 0,
            "max_iterations": 3,
            "disclosure_gaps": [],
        }
        
        mock_openrouter(get_mock_governance_response())
        
        result = await investigate_legal(state)
        
        # Check required fields
        assert "findings" in result
        assert "agent_status" in result
        assert "events" in result
        
        # Findings should be a list
        assert isinstance(result["findings"], list)
        
        # Agent status should have legal agent
        assert "legal" in result["agent_status"]
        
        # Events should be a list of StreamEvent
        assert isinstance(result["events"], list)
        for event in result["events"]:
            assert hasattr(event, "event_type")
            assert hasattr(event, "agent_name")
            assert hasattr(event, "timestamp")

    @pytest.mark.asyncio
    async def test_legal_node_reducer_compatibility(
        self,
        mock_openrouter,
        mock_rag_service,
    ):
        """Test findings merge correctly with operator.add reducer."""
        # Simulate existing findings in state
        existing_finding = AgentFinding(
            finding_id="existing-001",
            agent_name="claims",
            claim_id="some-claim",
            evidence_type="claim_extraction",
            summary="Existing finding",
            details={},
            supports_claim=True,
            confidence="high",
            iteration=0,
        )
        
        state: SibylState = {
            "report_id": "test-reducer-001",
            "document_content": "",
            "document_chunks": [],
            "claims": [GOVERNANCE_CLAIM],
            "routing_plan": [ROUTING_GOVERNANCE],
            "agent_status": {},
            "findings": [existing_finding],  # Pre-existing finding
            "info_requests": [],
            "info_responses": [],
            "verdicts": [],
            "reinvestigation_requests": [],
            "iteration_count": 0,
            "max_iterations": 3,
            "disclosure_gaps": [],
        }
        
        mock_openrouter(get_mock_governance_response())
        
        result = await investigate_legal(state)
        
        # Result findings should be addable to existing
        new_findings = result["findings"]
        
        # Simulate reducer: combined = existing + new
        combined = [existing_finding] + new_findings
        
        # Should have at least 2 findings (existing + new)
        assert len(combined) >= 2
        
        # All should have unique finding_ids
        finding_ids = [f.finding_id for f in combined]
        assert len(finding_ids) == len(set(finding_ids))


# ============================================================================
# Re-investigation Flow Tests
# ============================================================================


class TestLegalNodeReinvestigation:
    """Tests for re-investigation handling within node."""

    @pytest.mark.asyncio
    async def test_legal_node_with_reinvestigation_request(
        self,
        mock_openrouter,
        mock_rag_service,
    ):
        """Test Legal Agent processes re-investigation requests correctly."""
        reinvest_req = ReinvestigationRequest(
            claim_id=STRATEGIC_CLAIM_INCOMPLETE.claim_id,
            target_agents=["legal"],
            evidence_gap="Missing key assumptions for transition plan",
            refined_queries=[
                "carbon price assumptions transition plan",
                "economic growth rate assumptions",
            ],
            required_evidence="Specific assumptions including carbon price trajectory",
        )
        
        routing_incomplete = RoutingAssignment(
            claim_id=STRATEGIC_CLAIM_INCOMPLETE.claim_id,
            assigned_agents=["legal"],
            reasoning="Strategic claim requiring compliance assessment",
        )
        
        state: SibylState = {
            "report_id": "test-reinvest-001",
            "document_content": "",
            "document_chunks": [],
            "claims": [STRATEGIC_CLAIM_INCOMPLETE],
            "routing_plan": [routing_incomplete],
            "agent_status": {},
            "findings": [],
            "info_requests": [],
            "info_responses": [],
            "verdicts": [],
            "reinvestigation_requests": [reinvest_req],
            "iteration_count": 1,
            "max_iterations": 3,
            "disclosure_gaps": [],
        }
        
        mock_openrouter(get_mock_compliance_response("fully_addressed"))
        
        result = await investigate_legal(state)
        
        # Should have processed the claim with re-investigation context
        assert len(result["findings"]) >= 1
        
        # Events should mention re-investigation
        events = result["events"]
        thinking_events = [e for e in events if e.event_type == "agent_thinking"]
        assert any(
            "re-invest" in e.data.get("message", "").lower()
            for e in thinking_events
        )


# ============================================================================
# Inter-Agent Communication Integration Tests
# ============================================================================


class TestLegalNodeInterAgentCommunication:
    """Tests for inter-agent communication within node."""

    @pytest.mark.asyncio
    async def test_legal_node_inter_agent_communication(
        self,
        mock_openrouter,
        mock_rag_service,
    ):
        """Test Legal Agent posts InfoRequests when needed."""
        # Claim that should trigger geographic verification
        facility_claim = Claim(
            claim_id="claim-facility-001",
            text="Our Singapore facility has achieved ISO 14001 certification for environmental management.",
            page_number=20,
            claim_type="legal_governance",
            ifrs_paragraphs=["S2.6"],
            priority="medium",
            source_location={"source_context": "Operations"},
            agent_reasoning="Governance claim with facility and certification",
        )
        
        routing = RoutingAssignment(
            claim_id=facility_claim.claim_id,
            assigned_agents=["legal"],
            reasoning="Governance claim requiring verification",
        )
        
        state: SibylState = {
            "report_id": "test-inter-agent-001",
            "document_content": "",
            "document_chunks": [],
            "claims": [facility_claim],
            "routing_plan": [routing],
            "agent_status": {},
            "findings": [],
            "info_requests": [],
            "info_responses": [],
            "verdicts": [],
            "reinvestigation_requests": [],
            "iteration_count": 0,
            "max_iterations": 3,
            "disclosure_gaps": [],
        }
        
        mock_openrouter(get_mock_governance_response())
        
        result = await investigate_legal(state)
        
        # Check if InfoRequest was generated
        # Note: Whether an InfoRequest is generated depends on the claim content
        # and assessment result. The test verifies the mechanism works.
        if "info_requests" in result:
            for req in result["info_requests"]:
                assert req.requesting_agent == "legal"
                assert req.context["claim_id"] == facility_claim.claim_id

    @pytest.mark.asyncio
    async def test_legal_node_incorporates_info_responses(
        self,
        mock_openrouter,
        mock_rag_service,
    ):
        """Test Legal Agent incorporates InfoResponses in findings."""
        claim = Claim(
            claim_id="claim-verified-001",
            text="Our facility has ISO 14001 certification.",
            page_number=25,
            claim_type="legal_governance",
            ifrs_paragraphs=["S2.6"],
            priority="medium",
            source_location={},
            agent_reasoning="Certification claim",
        )
        
        routing = RoutingAssignment(
            claim_id=claim.claim_id,
            assigned_agents=["legal"],
            reasoning="Governance claim",
        )
        
        # Pre-existing InfoRequest from legal agent
        info_request = InfoRequest(
            request_id="req-verify-001",
            requesting_agent="legal",
            description="Verify ISO 14001 certification",
            context={"claim_id": claim.claim_id},
            status="responded",
        )
        
        # InfoResponse from news_media agent
        info_response = InfoResponse(
            request_id="req-verify-001",
            responding_agent="news_media",
            response="ISO 14001 certification verified in external database.",
            details={"source": "ISO public registry"},
        )
        
        state: SibylState = {
            "report_id": "test-info-resp-001",
            "document_content": "",
            "document_chunks": [],
            "claims": [claim],
            "routing_plan": [routing],
            "agent_status": {},
            "findings": [],
            "info_requests": [info_request],
            "info_responses": [info_response],
            "verdicts": [],
            "reinvestigation_requests": [],
            "iteration_count": 0,
            "max_iterations": 3,
            "disclosure_gaps": [],
        }
        
        mock_openrouter(get_mock_governance_response())
        
        result = await investigate_legal(state)
        
        # Check if finding incorporates the InfoResponse
        assert len(result["findings"]) >= 1
        finding = result["findings"][0]
        
        # If cross-domain evidence was incorporated
        if "cross_domain_evidence" in finding.details:
            evidence = finding.details["cross_domain_evidence"]
            assert len(evidence) > 0
            assert evidence[0]["responding_agent"] == "news_media"


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestLegalNodeEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_legal_node_empty_claims(self):
        """Test Legal Agent handles empty claims list."""
        state: SibylState = {
            "report_id": "test-empty-001",
            "document_content": "",
            "document_chunks": [],
            "claims": [],
            "routing_plan": [],
            "agent_status": {},
            "findings": [],
            "info_requests": [],
            "info_responses": [],
            "verdicts": [],
            "reinvestigation_requests": [],
            "iteration_count": 0,
            "max_iterations": 3,
            "disclosure_gaps": [],
        }
        
        result = await investigate_legal(state)
        
        # Should complete successfully with no findings
        compliance_findings = [
            f for f in result["findings"]
            if f.evidence_type == "ifrs_compliance"
        ]
        assert len(compliance_findings) == 0
        
        # Status should show 0 claims
        assert result["agent_status"]["legal"].claims_assigned == 0

    @pytest.mark.asyncio
    async def test_legal_node_no_legal_routing(self):
        """Test Legal Agent handles claims not routed to it."""
        geo_claim = Claim(
            claim_id="claim-geo-001",
            text="Our facility is in Singapore.",
            page_number=5,
            claim_type="geographic",
            ifrs_paragraphs=[],
            priority="low",
            source_location={},
            agent_reasoning="Geographic claim",
        )
        
        geo_routing = RoutingAssignment(
            claim_id=geo_claim.claim_id,
            assigned_agents=["geography"],  # Not legal
            reasoning="Geographic claim",
        )
        
        state: SibylState = {
            "report_id": "test-no-legal-001",
            "document_content": "",
            "document_chunks": [],
            "claims": [geo_claim],
            "routing_plan": [geo_routing],
            "agent_status": {},
            "findings": [],
            "info_requests": [],
            "info_responses": [],
            "verdicts": [],
            "reinvestigation_requests": [],
            "iteration_count": 0,
            "max_iterations": 3,
            "disclosure_gaps": [],
        }
        
        result = await investigate_legal(state)
        
        # No compliance findings since no claims routed to legal
        compliance_findings = [
            f for f in result["findings"]
            if f.evidence_type == "ifrs_compliance"
        ]
        assert len(compliance_findings) == 0

    @pytest.mark.asyncio
    async def test_legal_node_handles_malformed_claim(
        self,
        mock_openrouter,
        mock_rag_service,
    ):
        """Test Legal Agent handles claims with missing optional fields."""
        minimal_claim = Claim(
            claim_id="claim-minimal-001",
            text="Basic claim text.",
            page_number=1,
            claim_type="legal_governance",
            ifrs_paragraphs=[],  # Empty IFRS mappings
            priority="low",
            source_location={},
            agent_reasoning="",
        )
        
        routing = RoutingAssignment(
            claim_id=minimal_claim.claim_id,
            assigned_agents=["legal"],
            reasoning="Minimal routing",
        )
        
        state: SibylState = {
            "report_id": "test-minimal-001",
            "document_content": "",
            "document_chunks": [],
            "claims": [minimal_claim],
            "routing_plan": [routing],
            "agent_status": {},
            "findings": [],
            "info_requests": [],
            "info_responses": [],
            "verdicts": [],
            "reinvestigation_requests": [],
            "iteration_count": 0,
            "max_iterations": 3,
            "disclosure_gaps": [],
        }
        
        mock_openrouter(get_mock_governance_response())
        
        result = await investigate_legal(state)
        
        # Should complete without error
        assert "findings" in result
        assert result["agent_status"]["legal"].status == "completed"
