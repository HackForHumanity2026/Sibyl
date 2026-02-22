"""Unit tests for the Legal Agent.

Tests all Legal Agent functions with mocked OpenRouter API calls
and mocked RAG service to ensure no external dependencies are hit.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.legal_agent import (
    SubRequirementAssessment,
    IFRSMapping,
    LegalAssessmentResult,
    GapCoverageResult,
    investigate_legal,
    _build_rag_query,
    _assess_compliance,
    _create_compliance_finding,
    _should_request_cross_domain_verification,
    _create_info_request,
    _process_info_responses,
    _get_reinvestigation_context,
    _get_claims_by_paragraph,
    CLAIM_TYPE_IFRS_FOCUS,
)
from app.agents.state import (
    Claim,
    SibylState,
    RoutingAssignment,
    ReinvestigationRequest,
    InfoRequest,
    InfoResponse,
    AgentFinding,
)
from tests.fixtures.mock_openrouter import (
    get_mock_compliance_response,
    get_mock_governance_response,
    get_mock_metrics_response,
    get_mock_risk_management_response,
    MOCK_COMPLIANCE_FULLY_ADDRESSED,
    MOCK_COMPLIANCE_PARTIALLY_ADDRESSED,
    MOCK_COMPLIANCE_NOT_ADDRESSED,
)
from tests.fixtures.sample_claims import (
    GOVERNANCE_CLAIM,
    STRATEGIC_CLAIM_TRANSITION_PLAN,
    STRATEGIC_CLAIM_INCOMPLETE,
    METRICS_CLAIM_SCOPE_3,
    RISK_MANAGEMENT_CLAIM,
)


# ============================================================================
# Schema Tests
# ============================================================================


class TestResponseSchemas:
    """Tests for Pydantic response schemas."""

    def test_sub_requirement_assessment_addressed(self):
        """Test SubRequirementAssessment with addressed requirement."""
        assessment = SubRequirementAssessment(
            requirement="key_assumptions",
            addressed=True,
            evidence="The report states carbon price assumption of $75/tCO2e.",
        )
        assert assessment.addressed is True
        assert assessment.evidence is not None
        assert assessment.gap_reason is None

    def test_sub_requirement_assessment_not_addressed(self):
        """Test SubRequirementAssessment with gap."""
        assessment = SubRequirementAssessment(
            requirement="dependencies",
            addressed=False,
            gap_reason="No dependencies disclosed for transition plan.",
        )
        assert assessment.addressed is False
        assert assessment.evidence is None
        assert assessment.gap_reason is not None

    def test_ifrs_mapping_fully_addressed(self):
        """Test IFRSMapping with full compliance."""
        mapping = IFRSMapping(
            paragraph_id="S2.14(a)(iv)",
            pillar="strategy",
            section="Decision-Making",
            requirement_text="Transition plan requirements",
            sub_requirements=[
                SubRequirementAssessment(requirement="key_assumptions", addressed=True, evidence="..."),
                SubRequirementAssessment(requirement="dependencies", addressed=True, evidence="..."),
                SubRequirementAssessment(requirement="timeline", addressed=True, evidence="..."),
            ],
            compliance_status="fully_addressed",
            s1_counterpart="S1.33",
        )
        assert mapping.compliance_status == "fully_addressed"
        assert len(mapping.sub_requirements) == 3
        assert all(sr.addressed for sr in mapping.sub_requirements)

    def test_legal_assessment_result_with_gaps(self):
        """Test LegalAssessmentResult with gaps."""
        result = LegalAssessmentResult(
            ifrs_mappings=[
                IFRSMapping(
                    paragraph_id="S2.14(a)(iv)",
                    pillar="strategy",
                    section="Decision-Making",
                    requirement_text="Transition plan",
                    compliance_status="partially_addressed",
                )
            ],
            evidence=["Timeline provided"],
            gaps=["Missing key assumptions", "Missing dependencies"],
            confidence="high",
        )
        assert result.confidence == "high"
        assert len(result.gaps) == 2


# ============================================================================
# RAG Query Building Tests
# ============================================================================


class TestRAGQueryBuilding:
    """Tests for RAG query construction."""

    def test_build_query_governance_claim(self):
        """Test query building for governance claim."""
        query, source_types = _build_rag_query(GOVERNANCE_CLAIM)
        
        assert "governance" in query.lower()
        assert "S2.6" in query or "board oversight" in query.lower()
        assert "ifrs_s1" in source_types
        assert "ifrs_s2" in source_types

    def test_build_query_strategic_claim(self):
        """Test query building for strategic claim."""
        query, source_types = _build_rag_query(STRATEGIC_CLAIM_TRANSITION_PLAN)
        
        assert "transition plan" in query.lower() or "strategy" in query.lower()
        assert "ifrs_s2" in source_types

    def test_build_query_metrics_claim(self):
        """Test query building for quantitative claim."""
        query, source_types = _build_rag_query(METRICS_CLAIM_SCOPE_3)
        
        assert "metrics" in query.lower() or "ghg" in query.lower() or "scope" in query.lower()
        assert "ifrs_s2" in source_types

    def test_claim_type_focus_mapping_coverage(self):
        """Test that all expected claim types have IFRS focus mappings."""
        expected_types = ["legal_governance", "strategic", "quantitative", "environmental"]
        for claim_type in expected_types:
            assert claim_type in CLAIM_TYPE_IFRS_FOCUS
            focus = CLAIM_TYPE_IFRS_FOCUS[claim_type]
            assert "paragraphs" in focus
            assert "query_suffix" in focus
            assert "source_types" in focus


# ============================================================================
# Compliance Assessment Tests
# ============================================================================


class TestComplianceAssessment:
    """Tests for compliance assessment functions."""

    @pytest.mark.asyncio
    async def test_assess_compliance_fully_addressed(self, mock_openrouter):
        """Test compliance assessment returns fully addressed status."""
        mock_openrouter(get_mock_compliance_response("fully_addressed"))
        
        rag_results = "S2.14(a)(iv): Transition plan with key assumptions, dependencies, timeline."
        result = await _assess_compliance(STRATEGIC_CLAIM_TRANSITION_PLAN, rag_results)
        
        assert result.confidence == "high"
        assert len(result.ifrs_mappings) > 0
        assert result.ifrs_mappings[0].compliance_status == "fully_addressed"
        assert len(result.gaps) == 0

    @pytest.mark.asyncio
    async def test_assess_compliance_partially_addressed(self, mock_openrouter):
        """Test compliance assessment returns partially addressed status."""
        mock_openrouter(get_mock_compliance_response("partially_addressed"))
        
        rag_results = "S2.14(a)(iv): Transition plan with key assumptions, dependencies, timeline."
        result = await _assess_compliance(STRATEGIC_CLAIM_INCOMPLETE, rag_results)
        
        assert len(result.ifrs_mappings) > 0
        assert result.ifrs_mappings[0].compliance_status == "partially_addressed"
        assert len(result.gaps) > 0

    @pytest.mark.asyncio
    async def test_assess_compliance_not_addressed(self, mock_openrouter):
        """Test compliance assessment returns not addressed status."""
        mock_openrouter(get_mock_compliance_response("not_addressed"))
        
        vague_claim = Claim(
            claim_id="vague-001",
            text="We are committed to sustainability.",
            page_number=1,
            claim_type="strategic",
            ifrs_paragraphs=["S2.14"],
            priority="low",
            source_location={},
            agent_reasoning="Vague claim",
        )
        
        rag_results = "S2.14(a)(iv): Transition plan with key assumptions, dependencies, timeline."
        result = await _assess_compliance(vague_claim, rag_results)
        
        assert len(result.ifrs_mappings) > 0
        assert result.ifrs_mappings[0].compliance_status == "not_addressed"

    @pytest.mark.asyncio
    async def test_assess_compliance_handles_malformed_json(self, mock_openrouter):
        """Test compliance assessment handles malformed LLM response."""
        mock_openrouter("This is not valid JSON at all")
        
        rag_results = "Some IFRS content"
        result = await _assess_compliance(GOVERNANCE_CLAIM, rag_results)
        
        assert result.confidence == "low"
        assert len(result.gaps) > 0

    @pytest.mark.asyncio
    async def test_assess_compliance_handles_api_error(self, mock_openrouter_error):
        """Test compliance assessment handles API errors gracefully."""
        mock_openrouter_error(500, "Internal Server Error")
        
        rag_results = "Some IFRS content"
        result = await _assess_compliance(GOVERNANCE_CLAIM, rag_results)
        
        assert result.confidence == "low"


# ============================================================================
# Finding Generation Tests
# ============================================================================


class TestFindingGeneration:
    """Tests for finding generation functions."""

    def test_create_compliance_finding_fully_addressed(self):
        """Test finding creation for fully compliant claim."""
        assessment = LegalAssessmentResult(**MOCK_COMPLIANCE_FULLY_ADDRESSED)
        
        finding = _create_compliance_finding(
            STRATEGIC_CLAIM_TRANSITION_PLAN,
            assessment,
            iteration=0,
        )
        
        assert finding.agent_name == "legal"
        assert finding.claim_id == STRATEGIC_CLAIM_TRANSITION_PLAN.claim_id
        assert finding.evidence_type == "ifrs_compliance"
        assert finding.supports_claim is True
        assert finding.confidence == "high"
        assert "S2.14(a)(iv)" in finding.summary

    def test_create_compliance_finding_partially_addressed(self):
        """Test finding creation for partially compliant claim."""
        assessment = LegalAssessmentResult(**MOCK_COMPLIANCE_PARTIALLY_ADDRESSED)
        
        finding = _create_compliance_finding(
            STRATEGIC_CLAIM_INCOMPLETE,
            assessment,
            iteration=0,
        )
        
        assert finding.supports_claim is None  # Partial compliance
        assert "partially_addressed" in finding.summary.lower() or "gaps" in finding.summary.lower()

    def test_create_compliance_finding_not_addressed(self):
        """Test finding creation for non-compliant claim."""
        assessment = LegalAssessmentResult(**MOCK_COMPLIANCE_NOT_ADDRESSED)
        
        finding = _create_compliance_finding(
            STRATEGIC_CLAIM_INCOMPLETE,
            assessment,
            iteration=0,
        )
        
        assert finding.supports_claim is False

    def test_create_compliance_finding_with_info_responses(self):
        """Test finding includes cross-domain evidence."""
        assessment = LegalAssessmentResult(**MOCK_COMPLIANCE_FULLY_ADDRESSED)
        info_responses = [
            {"responding_agent": "news_media", "response": "Certification verified"}
        ]
        
        finding = _create_compliance_finding(
            GOVERNANCE_CLAIM,
            assessment,
            iteration=0,
            info_responses=info_responses,
        )
        
        assert "cross_domain_evidence" in finding.details
        assert len(finding.details["cross_domain_evidence"]) == 1

    def test_create_compliance_finding_empty_assessment(self):
        """Test finding creation with no IFRS mappings."""
        assessment = LegalAssessmentResult(
            ifrs_mappings=[],
            evidence=[],
            gaps=["Failed to assess"],
            confidence="low",
        )
        
        finding = _create_compliance_finding(
            GOVERNANCE_CLAIM,
            assessment,
            iteration=0,
        )
        
        assert finding.supports_claim is None
        assert finding.confidence == "low"


# ============================================================================
# Inter-Agent Communication Tests
# ============================================================================


class TestInterAgentCommunication:
    """Tests for inter-agent communication functions."""

    def test_should_request_geographic_verification(self):
        """Test geographic verification request detection."""
        claim_with_facility = Claim(
            claim_id="test-001",
            text="Our Singapore facility has achieved ISO 14001 certification.",
            page_number=1,
            claim_type="legal_governance",
            ifrs_paragraphs=["S2.6"],
            priority="medium",
            source_location={},
            agent_reasoning="Governance with geographic element",
        )
        assessment = LegalAssessmentResult(**MOCK_COMPLIANCE_FULLY_ADDRESSED)
        
        result = _should_request_cross_domain_verification(claim_with_facility, assessment)
        
        assert result is not None
        assert result[0] == "geography"

    def test_should_request_news_verification_for_certification(self):
        """Test news verification request for certification claims."""
        claim_with_cert = Claim(
            claim_id="test-002",
            text="We have been certified under ISO 14001 for environmental management.",
            page_number=1,
            claim_type="legal_governance",
            ifrs_paragraphs=["S2.6"],
            priority="medium",
            source_location={},
            agent_reasoning="Certification claim",
        )
        assessment = LegalAssessmentResult(**MOCK_COMPLIANCE_FULLY_ADDRESSED)
        
        result = _should_request_cross_domain_verification(claim_with_cert, assessment)
        
        assert result is not None
        assert result[0] == "news_media"

    def test_should_not_request_verification_standard_claim(self):
        """Test no verification needed for standard compliance claim."""
        assessment = LegalAssessmentResult(**MOCK_COMPLIANCE_FULLY_ADDRESSED)
        
        result = _should_request_cross_domain_verification(GOVERNANCE_CLAIM, assessment)
        
        # GOVERNANCE_CLAIM doesn't mention specific facilities or certifications
        assert result is None

    def test_create_info_request(self):
        """Test InfoRequest creation."""
        info_req = _create_info_request(
            GOVERNANCE_CLAIM,
            target_agent="geography",
            description="Verify facility location",
        )
        
        assert info_req.requesting_agent == "legal"
        assert info_req.context["claim_id"] == GOVERNANCE_CLAIM.claim_id
        assert info_req.context["target_agent"] == "geography"
        assert info_req.status == "pending"

    def test_process_info_responses_finds_matching(self):
        """Test processing of InfoResponses for a claim."""
        info_req = InfoRequest(
            request_id="req-001",
            requesting_agent="legal",
            description="Verify certification",
            context={"claim_id": GOVERNANCE_CLAIM.claim_id},
            status="responded",
        )
        info_resp = InfoResponse(
            request_id="req-001",
            responding_agent="news_media",
            response="Certification verified in external sources.",
            details={"source": "ISO database"},
        )
        state: SibylState = {
            "report_id": "test",
            "claims": [],
            "routing_plan": [],
            "findings": [],
            "info_requests": [info_req],
            "info_responses": [info_resp],
            "agent_status": {},
            "iteration_count": 0,
            "max_iterations": 3,
            "document_content": "",
            "document_chunks": [],
            "verdicts": [],
            "reinvestigation_requests": [],
            "disclosure_gaps": [],
        }
        
        responses = _process_info_responses(state, GOVERNANCE_CLAIM)
        
        assert len(responses) == 1
        assert responses[0]["responding_agent"] == "news_media"
        assert "verified" in responses[0]["response"].lower()

    def test_process_info_responses_no_matching(self):
        """Test processing when no InfoResponses match."""
        state: SibylState = {
            "report_id": "test",
            "claims": [],
            "routing_plan": [],
            "findings": [],
            "info_requests": [],
            "info_responses": [],
            "agent_status": {},
            "iteration_count": 0,
            "max_iterations": 3,
            "document_content": "",
            "document_chunks": [],
            "verdicts": [],
            "reinvestigation_requests": [],
            "disclosure_gaps": [],
        }
        
        responses = _process_info_responses(state, GOVERNANCE_CLAIM)
        
        assert len(responses) == 0


# ============================================================================
# Re-investigation Tests
# ============================================================================


class TestReinvestigation:
    """Tests for re-investigation handling."""

    def test_get_reinvestigation_context_found(self):
        """Test finding re-investigation request for a claim."""
        reinvest_req = ReinvestigationRequest(
            claim_id=STRATEGIC_CLAIM_INCOMPLETE.claim_id,
            target_agents=["legal"],
            evidence_gap="Missing key assumptions",
            refined_queries=["Search for transition plan assumptions"],
            required_evidence="Carbon price assumptions",
        )
        state: SibylState = {
            "report_id": "test",
            "claims": [STRATEGIC_CLAIM_INCOMPLETE],
            "routing_plan": [],
            "findings": [],
            "info_requests": [],
            "info_responses": [],
            "agent_status": {},
            "iteration_count": 1,
            "max_iterations": 3,
            "reinvestigation_requests": [reinvest_req],
            "document_content": "",
            "document_chunks": [],
            "verdicts": [],
            "disclosure_gaps": [],
        }
        
        result = _get_reinvestigation_context(state, STRATEGIC_CLAIM_INCOMPLETE.claim_id)
        
        assert result is not None
        assert result.evidence_gap == "Missing key assumptions"
        assert len(result.refined_queries) > 0

    def test_get_reinvestigation_context_not_found(self):
        """Test no re-investigation request for a claim."""
        state: SibylState = {
            "report_id": "test",
            "claims": [GOVERNANCE_CLAIM],
            "routing_plan": [],
            "findings": [],
            "info_requests": [],
            "info_responses": [],
            "agent_status": {},
            "iteration_count": 0,
            "max_iterations": 3,
            "reinvestigation_requests": [],
            "document_content": "",
            "document_chunks": [],
            "verdicts": [],
            "disclosure_gaps": [],
        }
        
        result = _get_reinvestigation_context(state, GOVERNANCE_CLAIM.claim_id)
        
        assert result is None

    def test_get_reinvestigation_context_different_agent(self):
        """Test re-investigation request targeting different agent."""
        reinvest_req = ReinvestigationRequest(
            claim_id=METRICS_CLAIM_SCOPE_3.claim_id,
            target_agents=["data_metrics"],  # Not legal
            evidence_gap="Numerical inconsistency",
            refined_queries=["Verify emission calculations"],
        )
        state: SibylState = {
            "report_id": "test",
            "claims": [METRICS_CLAIM_SCOPE_3],
            "routing_plan": [],
            "findings": [],
            "info_requests": [],
            "info_responses": [],
            "agent_status": {},
            "iteration_count": 1,
            "max_iterations": 3,
            "reinvestigation_requests": [reinvest_req],
            "document_content": "",
            "document_chunks": [],
            "verdicts": [],
            "disclosure_gaps": [],
        }
        
        result = _get_reinvestigation_context(state, METRICS_CLAIM_SCOPE_3.claim_id)
        
        assert result is None


# ============================================================================
# Gap Detection Helper Tests
# ============================================================================


class TestGapDetectionHelpers:
    """Tests for gap detection helper functions."""

    def test_get_claims_by_paragraph(self):
        """Test building paragraph to claims mapping."""
        claims = [GOVERNANCE_CLAIM, STRATEGIC_CLAIM_TRANSITION_PLAN]
        findings = [
            AgentFinding(
                finding_id="f-001",
                agent_name="legal",
                claim_id=GOVERNANCE_CLAIM.claim_id,
                evidence_type="ifrs_compliance",
                summary="Test",
                details={
                    "ifrs_mappings": [
                        {"paragraph_id": "S2.6", "compliance_status": "fully_addressed"}
                    ]
                },
                supports_claim=True,
                confidence="high",
                iteration=1,
            )
        ]
        
        mapping = _get_claims_by_paragraph(claims, findings)
        
        # GOVERNANCE_CLAIM has S2.6 in preliminary + finding
        assert "S2.6" in mapping
        assert GOVERNANCE_CLAIM.claim_id in mapping["S2.6"]
        
        # STRATEGIC_CLAIM has S2.14(a)(iv) in preliminary
        assert "S2.14(a)(iv)" in mapping or "S1.33" in mapping


# ============================================================================
# Main Node Function Tests
# ============================================================================


class TestInvestigateLegalNode:
    """Tests for the main investigate_legal node function."""

    @pytest.mark.asyncio
    async def test_investigate_legal_governance_claim(
        self, 
        mock_openrouter, 
        mock_rag_service,
        sample_state_governance,
    ):
        """Test Legal Agent correctly assesses a governance claim."""
        mock_openrouter(get_mock_governance_response())
        
        result = await investigate_legal(sample_state_governance)
        
        assert "findings" in result
        assert len(result["findings"]) >= 1
        assert result["findings"][0].evidence_type == "ifrs_compliance"
        assert result["findings"][0].agent_name == "legal"
        
        # Check events
        assert "events" in result
        event_types = [e.event_type for e in result["events"]]
        assert "agent_started" in event_types
        assert "agent_completed" in event_types

    @pytest.mark.asyncio
    async def test_investigate_legal_strategic_claim(
        self,
        mock_openrouter,
        mock_rag_service,
        sample_state_strategic,
    ):
        """Test Legal Agent assesses strategic transition plan claim."""
        mock_openrouter(get_mock_compliance_response("fully_addressed"))
        
        result = await investigate_legal(sample_state_strategic)
        
        assert len(result["findings"]) >= 1
        finding = result["findings"][0]
        assert finding.claim_id == STRATEGIC_CLAIM_TRANSITION_PLAN.claim_id
        assert finding.supports_claim is True

    @pytest.mark.asyncio
    async def test_investigate_legal_partial_compliance(
        self,
        mock_openrouter,
        mock_rag_service,
        sample_state_strategic_incomplete,
    ):
        """Test Legal Agent identifies partial compliance."""
        mock_openrouter(get_mock_compliance_response("partially_addressed"))
        
        result = await investigate_legal(sample_state_strategic_incomplete)
        
        assert len(result["findings"]) >= 1
        finding = result["findings"][0]
        # Partial compliance should have supports_claim=None
        assert finding.supports_claim is None or finding.supports_claim is False

    @pytest.mark.asyncio
    async def test_investigate_legal_metrics_claim(
        self,
        mock_openrouter,
        mock_rag_service,
        sample_state_metrics,
    ):
        """Test Legal Agent assesses metrics claim."""
        mock_openrouter(get_mock_metrics_response())
        
        result = await investigate_legal(sample_state_metrics)
        
        assert len(result["findings"]) >= 1
        finding = result["findings"][0]
        assert "S2.29" in str(finding.details) or "scope" in finding.summary.lower()

    @pytest.mark.asyncio
    async def test_investigate_legal_empty_routing(
        self,
        sample_state_no_legal_claims,
    ):
        """Test Legal Agent returns empty findings when no claims assigned."""
        result = await investigate_legal(sample_state_no_legal_claims)
        
        # Should have 0 compliance findings (might have gap findings)
        compliance_findings = [
            f for f in result["findings"] 
            if f.evidence_type == "ifrs_compliance"
        ]
        assert len(compliance_findings) == 0
        
        # Check agent status
        assert "agent_status" in result
        assert "legal" in result["agent_status"]
        assert result["agent_status"]["legal"].claims_assigned == 0

    @pytest.mark.asyncio
    async def test_investigate_legal_emits_correct_events(
        self,
        mock_openrouter,
        mock_rag_service,
        sample_state_governance,
    ):
        """Test Legal Agent emits correct StreamEvents."""
        mock_openrouter(get_mock_governance_response())
        
        result = await investigate_legal(sample_state_governance)
        
        events = result["events"]
        event_types = [e.event_type for e in events]
        
        assert "agent_started" in event_types
        assert "agent_thinking" in event_types
        assert "evidence_found" in event_types
        assert "agent_completed" in event_types

    @pytest.mark.asyncio
    async def test_investigate_legal_rag_failure_graceful_degradation(
        self,
        mock_openrouter,
        mock_rag_service_error,
        sample_state_governance,
    ):
        """Test Legal Agent handles RAG failure gracefully."""
        mock_openrouter(get_mock_governance_response())
        
        result = await investigate_legal(sample_state_governance)
        
        # Should still produce findings, just with RAG failure noted
        assert "findings" in result
        # Agent should complete despite RAG error
        event_types = [e.event_type for e in result["events"]]
        assert "agent_completed" in event_types

    @pytest.mark.asyncio
    async def test_investigate_legal_llm_error_handling(
        self,
        mock_openrouter_error,
        mock_rag_service,
        sample_state_governance,
    ):
        """Test Legal Agent handles LLM errors gracefully."""
        mock_openrouter_error(500, "Server Error")
        
        result = await investigate_legal(sample_state_governance)
        
        # Should still produce a finding with low confidence
        assert len(result["findings"]) >= 1
        finding = result["findings"][0]
        assert finding.confidence == "low"

    @pytest.mark.asyncio
    async def test_investigate_legal_multiple_claims(
        self,
        mock_openrouter,
        mock_rag_service,
        sample_state_multiple_claims,
    ):
        """Test Legal Agent processes multiple claims."""
        # Mock will be called multiple times
        mock_openrouter(get_mock_compliance_response("fully_addressed"))
        
        result = await investigate_legal(sample_state_multiple_claims)
        
        # Should have findings for multiple claims
        compliance_findings = [
            f for f in result["findings"]
            if f.evidence_type == "ifrs_compliance"
        ]
        assert len(compliance_findings) >= 1

    @pytest.mark.asyncio
    async def test_investigate_legal_reinvestigation(
        self,
        mock_openrouter,
        mock_rag_service,
        sample_state_reinvestigation,
    ):
        """Test Legal Agent handles re-investigation requests."""
        mock_openrouter(get_mock_compliance_response("fully_addressed"))
        
        result = await investigate_legal(sample_state_reinvestigation)
        
        # Should have processed the re-investigation
        assert len(result["findings"]) >= 1
        
        # Check for re-investigation event
        events = result["events"]
        thinking_events = [e for e in events if e.event_type == "agent_thinking"]
        reinvest_mentioned = any(
            "re-invest" in e.data.get("message", "").lower() 
            for e in thinking_events
        )
        assert reinvest_mentioned

    @pytest.mark.asyncio
    async def test_investigate_legal_incorporates_info_responses(
        self,
        mock_openrouter,
        mock_rag_service,
        sample_state_info_response,
    ):
        """Test Legal Agent incorporates InfoResponses from other agents."""
        mock_openrouter(get_mock_governance_response())
        
        result = await investigate_legal(sample_state_info_response)
        
        assert len(result["findings"]) >= 1
        finding = result["findings"][0]
        
        # If there was a matching InfoResponse, it should be in details
        if "cross_domain_evidence" in finding.details:
            assert len(finding.details["cross_domain_evidence"]) > 0
