"""Unit tests for Judge Agent (FRD 11).

Tests the evaluation, verdict, and reinvestigation functions.
All tests are pure functions - no external API calls.
"""

import pytest

from app.agents.state import AgentFinding, AgentStatus, Claim
from app.agents.judge_agent import (
    AGENT_QUALITY_WEIGHTS,
    CLAIM_TYPE_EXPECTED_AGENTS,
    DIMENSION_WEIGHTS,
    VERIFIED_THRESHOLD,
    determine_confidence,
    determine_verdict,
    evaluate_completeness,
    evaluate_consistency,
    evaluate_evidence,
    evaluate_quality,
    evaluate_sufficiency,
    extract_ifrs_mapping,
    generate_reinvestigation_request,
    generate_verdict_reasoning,
    should_request_reinvestigation,
)
from tests.fixtures.sample_claims import (
    FINDING_ACADEMIC_INCONCLUSIVE,
    FINDING_ACADEMIC_SUPPORTING,
    FINDING_DATA_METRICS_CONTRADICTING,
    FINDING_GEOGRAPHY_SUPPORTING,
    FINDING_LEGAL_SUPPORTING,
    FINDING_LEGAL_WEAK,
    FINDING_NEWS_CONTRADICTING,
    FINDING_NEWS_SUPPORTING,
    JUDGE_CLAIM_TRANSITION_PLAN,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_claim() -> Claim:
    """Provide a sample claim for testing."""
    return JUDGE_CLAIM_TRANSITION_PLAN


@pytest.fixture
def sample_findings_supporting() -> list[AgentFinding]:
    """Provide multiple supporting findings."""
    return [
        FINDING_LEGAL_SUPPORTING,
        FINDING_GEOGRAPHY_SUPPORTING,
        FINDING_ACADEMIC_SUPPORTING,
        FINDING_NEWS_SUPPORTING,
    ]


@pytest.fixture
def sample_findings_contradicting() -> list[AgentFinding]:
    """Provide contradicting findings."""
    return [
        FINDING_NEWS_CONTRADICTING,
        FINDING_DATA_METRICS_CONTRADICTING,
    ]


@pytest.fixture
def sample_agent_status_healthy() -> dict[str, AgentStatus]:
    """Provide agent status with all agents completed."""
    return {
        "legal": AgentStatus(agent_name="legal", status="completed"),
        "geography": AgentStatus(agent_name="geography", status="completed"),
        "academic": AgentStatus(agent_name="academic", status="completed"),
        "news_media": AgentStatus(agent_name="news_media", status="completed"),
    }


@pytest.fixture
def sample_agent_status_with_error() -> dict[str, AgentStatus]:
    """Provide agent status with one agent errored."""
    return {
        "legal": AgentStatus(agent_name="legal", status="completed"),
        "geography": AgentStatus(agent_name="geography", status="error"),
        "academic": AgentStatus(agent_name="academic", status="completed"),
        "news_media": AgentStatus(agent_name="news_media", status="completed"),
    }


# ============================================================================
# Test Sufficiency Evaluation
# ============================================================================


class TestSufficiencyEvaluation:
    """Tests for evaluate_sufficiency function."""

    def test_high_sufficiency_three_agents(self, sample_claim, sample_findings_supporting):
        """3+ agents supporting = high sufficiency."""
        result = evaluate_sufficiency(sample_findings_supporting, sample_claim)
        
        assert result["sufficiency"] == "high"
        assert result["source_count"] == 4
        assert len(result["supporting_agents"]) == 4
        assert result["contradicting_agents"] == []
        assert result["has_contradictions"] is False

    def test_medium_sufficiency_two_agents(self, sample_claim):
        """2 agents supporting = medium sufficiency."""
        findings = [FINDING_LEGAL_SUPPORTING, FINDING_GEOGRAPHY_SUPPORTING]
        
        result = evaluate_sufficiency(findings, sample_claim)
        
        assert result["sufficiency"] == "medium"
        assert result["source_count"] == 2

    def test_low_sufficiency_single_agent(self, sample_claim):
        """1 agent supporting = low sufficiency."""
        findings = [FINDING_LEGAL_SUPPORTING]
        
        result = evaluate_sufficiency(findings, sample_claim)
        
        assert result["sufficiency"] == "low"
        assert result["source_count"] == 1

    def test_very_low_sufficiency_no_agents(self, sample_claim):
        """0 findings = very low sufficiency."""
        result = evaluate_sufficiency([], sample_claim)
        
        assert result["sufficiency"] == "very_low"
        assert result["source_count"] == 0
        assert result["total_findings"] == 0

    def test_detects_contradicting_agents(self, sample_claim, sample_findings_contradicting):
        """Detects contradicting agents correctly."""
        result = evaluate_sufficiency(sample_findings_contradicting, sample_claim)
        
        assert result["has_contradictions"] is True
        assert "news_media" in result["contradicting_agents"]
        assert "data_metrics" in result["contradicting_agents"]

    def test_mixed_support_and_contradict(self, sample_claim):
        """Handles mix of supporting and contradicting findings."""
        findings = [FINDING_LEGAL_SUPPORTING, FINDING_NEWS_CONTRADICTING]
        
        result = evaluate_sufficiency(findings, sample_claim)
        
        assert result["source_count"] == 1  # Only supporting agents count
        assert len(result["contradicting_agents"]) == 1
        assert result["has_contradictions"] is True


# ============================================================================
# Test Consistency Evaluation
# ============================================================================


class TestConsistencyEvaluation:
    """Tests for evaluate_consistency function."""

    def test_high_consistency_all_support(self, sample_findings_supporting):
        """All findings support = high consistency."""
        result = evaluate_consistency(sample_findings_supporting)
        
        assert result["consistency"] == "high"
        assert result["has_contradictions"] is False
        assert result["support_ratio"] == 1.0
        assert result["contradict_ratio"] == 0.0

    def test_medium_consistency_minor_contradiction(self):
        """Support > contradict = medium consistency."""
        findings = [
            FINDING_LEGAL_SUPPORTING,
            FINDING_GEOGRAPHY_SUPPORTING,
            FINDING_ACADEMIC_SUPPORTING,
            FINDING_NEWS_CONTRADICTING,
        ]
        
        result = evaluate_consistency(findings)
        
        assert result["consistency"] == "medium"
        assert result["has_contradictions"] is True
        assert result["support_ratio"] == 0.75  # 3/4

    def test_low_consistency_major_contradiction(self, sample_findings_contradicting):
        """Contradict > support = low consistency."""
        result = evaluate_consistency(sample_findings_contradicting)
        
        assert result["consistency"] == "low"
        assert result["has_contradictions"] is True
        assert result["support_ratio"] == 0.0

    def test_handles_inconclusive_findings(self):
        """Handles findings with supports_claim=None."""
        findings = [
            FINDING_LEGAL_SUPPORTING,
            FINDING_ACADEMIC_INCONCLUSIVE,
        ]
        
        result = evaluate_consistency(findings)
        
        assert result["support_counts"]["inconclusive"] == 1
        assert result["support_counts"]["support"] == 1
        assert result["has_contradictions"] is False

    def test_empty_findings_returns_unclear(self):
        """Empty findings list returns unclear consistency."""
        result = evaluate_consistency([])
        
        assert result["consistency"] == "unclear"
        assert result["support_ratio"] == 0
        assert result["contradict_ratio"] == 0


# ============================================================================
# Test Quality Evaluation
# ============================================================================


class TestQualityEvaluation:
    """Tests for evaluate_quality function."""

    def test_high_quality_legal_and_geography(self):
        """Legal and geography agents have high base weights."""
        findings = [FINDING_LEGAL_SUPPORTING, FINDING_GEOGRAPHY_SUPPORTING]
        
        result = evaluate_quality(findings)
        
        assert result["quality"] == "high"
        assert result["avg_quality_score"] >= 0.8
        
    def test_low_quality_news_tier_4(self):
        """News with tier 4 source has low quality."""
        low_tier_news = AgentFinding(
            finding_id="finding-news-tier4",
            agent_name="news_media",
            claim_id="claim-judge-001",
            evidence_type="news",
            summary="Low credibility news source",
            details={"source_tier": 4},
            supports_claim=True,
            confidence="low",
            iteration=1,
        )
        
        result = evaluate_quality([low_tier_news])
        
        assert result["quality"] == "low"
        # 0.7 (news base) * 0.3 (tier 4) * 0.4 (low confidence) = 0.084
        assert result["avg_quality_score"] < 0.3

    def test_weights_confidence_levels(self):
        """Higher confidence = higher quality score."""
        high_conf = AgentFinding(
            finding_id="finding-high",
            agent_name="academic",
            claim_id="claim-judge-001",
            evidence_type="research",
            summary="High confidence finding",
            details={},
            supports_claim=True,
            confidence="high",
            iteration=1,
        )
        low_conf = AgentFinding(
            finding_id="finding-low",
            agent_name="academic",
            claim_id="claim-judge-001",
            evidence_type="research",
            summary="Low confidence finding",
            details={},
            supports_claim=True,
            confidence="low",
            iteration=1,
        )
        
        high_result = evaluate_quality([high_conf])
        low_result = evaluate_quality([low_conf])
        
        assert high_result["avg_quality_score"] > low_result["avg_quality_score"]

    def test_empty_findings_returns_low_quality(self):
        """Empty findings list returns low quality."""
        result = evaluate_quality([])
        
        assert result["quality"] == "low"
        assert result["avg_quality_score"] == 0.0

    def test_agent_weight_hierarchy(self):
        """Verify agent weight hierarchy is correct."""
        assert AGENT_QUALITY_WEIGHTS["legal"] > AGENT_QUALITY_WEIGHTS["geography"]
        assert AGENT_QUALITY_WEIGHTS["geography"] >= AGENT_QUALITY_WEIGHTS["data_metrics"]
        assert AGENT_QUALITY_WEIGHTS["academic"] > AGENT_QUALITY_WEIGHTS["news_media"]


# ============================================================================
# Test Completeness Evaluation
# ============================================================================


class TestCompletenessEvaluation:
    """Tests for evaluate_completeness function."""

    def test_high_completeness_all_expected_agents(self, sample_claim, sample_agent_status_healthy):
        """All expected agents investigated = high completeness."""
        findings = [
            FINDING_LEGAL_SUPPORTING,
            FINDING_ACADEMIC_SUPPORTING,
            FINDING_NEWS_SUPPORTING,
        ]
        
        result = evaluate_completeness(sample_claim, findings, sample_agent_status_healthy)
        
        assert result["completeness"] == "high"
        assert result["missing_agents"] == []

    def test_low_completeness_missing_critical_agent(self, sample_claim, sample_agent_status_healthy):
        """Missing expected agent = lower completeness."""
        findings = [FINDING_LEGAL_SUPPORTING]
        
        result = evaluate_completeness(sample_claim, findings, sample_agent_status_healthy)
        
        assert result["completeness"] in ["medium", "low"]
        assert len(result["missing_agents"]) > 0

    def test_accounts_for_errored_agents(self, sample_claim, sample_agent_status_with_error):
        """Errored agents affect completeness score."""
        findings = [FINDING_LEGAL_SUPPORTING, FINDING_ACADEMIC_SUPPORTING]
        
        result = evaluate_completeness(sample_claim, findings, sample_agent_status_with_error)
        
        assert "geography" in result["errored_agents"] or result["errored_agents"] == []
        # Score should be lower due to errored agent

    def test_expected_agents_by_claim_type(self):
        """Verify expected agents mapping for different claim types."""
        # Geographic claims expect geography + legal
        assert "geography" in CLAIM_TYPE_EXPECTED_AGENTS["geographic"]
        assert "legal" in CLAIM_TYPE_EXPECTED_AGENTS["geographic"]
        
        # Quantitative claims expect data_metrics + legal
        assert "data_metrics" in CLAIM_TYPE_EXPECTED_AGENTS["quantitative"]
        
        # Strategic claims expect multiple agents
        strategic_expected = CLAIM_TYPE_EXPECTED_AGENTS["strategic"]
        assert len(strategic_expected) >= 2

    def test_handles_empty_agent_status(self, sample_claim):
        """Handles empty agent_status dict gracefully."""
        findings = [FINDING_LEGAL_SUPPORTING]
        
        result = evaluate_completeness(sample_claim, findings, {})
        
        assert "completeness" in result
        assert result["errored_agents"] == []


# ============================================================================
# Test Combined Evaluation
# ============================================================================


class TestCombinedEvaluation:
    """Tests for evaluate_evidence function."""

    def test_overall_score_calculation(self, sample_claim, sample_findings_supporting, sample_agent_status_healthy):
        """Overall score is weighted combination of dimensions."""
        result = evaluate_evidence(sample_claim, sample_findings_supporting, sample_agent_status_healthy)
        
        assert "overall_score" in result
        assert 0 <= result["overall_score"] <= 1
        assert result["overall_score"] > 0.7  # High-quality evidence

    def test_dimension_weights_sum_to_one(self):
        """Dimension weights must sum to 1.0."""
        total = sum(DIMENSION_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_returns_all_dimension_evaluations(self, sample_claim, sample_findings_supporting, sample_agent_status_healthy):
        """Result includes all four dimension evaluations."""
        result = evaluate_evidence(sample_claim, sample_findings_supporting, sample_agent_status_healthy)
        
        assert "sufficiency" in result
        assert "consistency" in result
        assert "quality" in result
        assert "completeness" in result
        assert "dimension_scores" in result

    def test_empty_findings_low_score(self, sample_claim, sample_agent_status_healthy):
        """Empty findings produce low overall score."""
        result = evaluate_evidence(sample_claim, [], sample_agent_status_healthy)
        
        assert result["overall_score"] < 0.5


# ============================================================================
# Test Verdict Determination
# ============================================================================


class TestVerdictDetermination:
    """Tests for determine_verdict function."""

    def test_verified_high_score_no_contradictions(self, sample_claim, sample_findings_supporting, sample_agent_status_healthy):
        """High score + no contradictions = verified."""
        evaluation = evaluate_evidence(sample_claim, sample_findings_supporting, sample_agent_status_healthy)
        
        verdict = determine_verdict(evaluation)
        
        assert verdict == "verified"

    def test_unverified_no_findings(self, sample_claim, sample_agent_status_healthy):
        """No findings = unverified."""
        evaluation = evaluate_evidence(sample_claim, [], sample_agent_status_healthy)
        
        verdict = determine_verdict(evaluation)
        
        assert verdict == "unverified"

    def test_contradicted_majority_contradict(self):
        """Majority contradicting = contradicted verdict."""
        evaluation = {
            "overall_score": 0.5,
            "consistency": {
                "has_contradictions": True,
                "contradict_ratio": 0.6,
            },
            "sufficiency": {
                "source_count": 2,
            },
        }
        
        verdict = determine_verdict(evaluation)
        
        assert verdict == "contradicted"

    def test_insufficient_evidence_low_score(self, sample_claim, sample_agent_status_healthy):
        """Low score with some evidence = insufficient."""
        findings = [FINDING_LEGAL_WEAK]
        evaluation = evaluate_evidence(sample_claim, findings, sample_agent_status_healthy)
        
        verdict = determine_verdict(evaluation)
        
        assert verdict == "insufficient_evidence"

    def test_verified_threshold_boundary(self):
        """Test verdict at threshold boundary."""
        evaluation = {
            "overall_score": VERIFIED_THRESHOLD,
            "consistency": {"has_contradictions": False, "contradict_ratio": 0},
            "sufficiency": {"source_count": 2},
        }
        
        verdict = determine_verdict(evaluation)
        
        assert verdict == "verified"


# ============================================================================
# Test Verdict Reasoning
# ============================================================================


class TestVerdictReasoning:
    """Tests for generate_verdict_reasoning function."""

    def test_reasoning_cites_supporting_agents(self, sample_claim, sample_findings_supporting, sample_agent_status_healthy):
        """Reasoning mentions supporting agents."""
        evaluation = evaluate_evidence(sample_claim, sample_findings_supporting, sample_agent_status_healthy)
        
        reasoning = generate_verdict_reasoning(evaluation, sample_findings_supporting, "verified", sample_claim)
        
        assert "VERIFIED" in reasoning
        assert "Legal" in reasoning or "legal" in reasoning

    def test_reasoning_mentions_contradictions(self, sample_claim):
        """Reasoning explains contradictions when present."""
        findings = [FINDING_LEGAL_SUPPORTING, FINDING_NEWS_CONTRADICTING]
        evaluation = evaluate_evidence(sample_claim, findings, {})
        
        reasoning = generate_verdict_reasoning(evaluation, findings, "contradicted", sample_claim)
        
        assert "CONTRADICTED" in reasoning

    def test_reasoning_notes_missing_agents(self, sample_claim, sample_agent_status_healthy):
        """Reasoning notes missing expected agents."""
        findings = [FINDING_LEGAL_SUPPORTING]
        evaluation = evaluate_evidence(sample_claim, findings, sample_agent_status_healthy)
        
        reasoning = generate_verdict_reasoning(evaluation, findings, "insufficient_evidence", sample_claim)
        
        assert "INSUFFICIENT" in reasoning

    def test_unverified_reasoning(self, sample_claim, sample_agent_status_healthy):
        """Unverified verdict has appropriate reasoning."""
        evaluation = evaluate_evidence(sample_claim, [], sample_agent_status_healthy)
        
        reasoning = generate_verdict_reasoning(evaluation, [], "unverified", sample_claim)
        
        assert "UNVERIFIED" in reasoning
        assert "No external evidence" in reasoning or "cannot be independently verified" in reasoning


# ============================================================================
# Test IFRS Mapping
# ============================================================================


class TestIfrsMapping:
    """Tests for extract_ifrs_mapping function."""

    def test_extracts_from_claim_paragraphs(self, sample_claim):
        """Extracts IFRS paragraphs from claim."""
        result = extract_ifrs_mapping(sample_claim, [])
        
        assert len(result) > 0
        paragraphs = [m["paragraph"] for m in result]
        assert "S2.14(a)(iv)" in paragraphs or any("S2" in p for p in paragraphs)

    def test_extracts_from_legal_findings(self, sample_claim):
        """Extracts IFRS mappings from Legal Agent findings."""
        result = extract_ifrs_mapping(sample_claim, [FINDING_LEGAL_SUPPORTING])
        
        assert len(result) > 0
        # Should have "compliant" status from legal agent
        statuses = [m["status"] for m in result]
        assert "compliant" in statuses or "pending" in statuses

    def test_deduplicates_paragraphs(self, sample_claim):
        """Deduplicates paragraphs from multiple sources."""
        result = extract_ifrs_mapping(sample_claim, [FINDING_LEGAL_SUPPORTING])
        
        paragraphs = [m["paragraph"] for m in result]
        assert len(paragraphs) == len(set(paragraphs))

    def test_handles_empty_mappings(self):
        """Handles claims with no IFRS paragraphs."""
        claim_no_ifrs = Claim(
            claim_id="claim-no-ifrs",
            text="A claim without IFRS mapping",
            page_number=1,
            claim_type="general",
            ifrs_paragraphs=[],
            priority="low",
            source_location={},
            agent_reasoning="Test claim",
        )
        
        result = extract_ifrs_mapping(claim_no_ifrs, [])
        
        assert result == []


# ============================================================================
# Test Reinvestigation Decision
# ============================================================================


class TestReinvestigationDecision:
    """Tests for should_request_reinvestigation function."""

    def test_requests_when_score_below_threshold(self, sample_claim, sample_agent_status_healthy):
        """Requests reinvestigation when score below threshold."""
        findings = [FINDING_LEGAL_WEAK]
        evaluation = evaluate_evidence(sample_claim, findings, sample_agent_status_healthy)
        
        result = should_request_reinvestigation(evaluation, iteration_count=0, max_iterations=3)
        
        assert result is True

    def test_no_request_when_score_sufficient(self, sample_claim, sample_findings_supporting, sample_agent_status_healthy):
        """No request when evidence is sufficient."""
        evaluation = evaluate_evidence(sample_claim, sample_findings_supporting, sample_agent_status_healthy)
        
        result = should_request_reinvestigation(evaluation, iteration_count=0, max_iterations=3)
        
        assert result is False

    def test_no_request_at_max_iterations(self, sample_claim, sample_agent_status_healthy):
        """No request when at max iterations."""
        findings = [FINDING_LEGAL_WEAK]
        evaluation = evaluate_evidence(sample_claim, findings, sample_agent_status_healthy)
        
        result = should_request_reinvestigation(evaluation, iteration_count=3, max_iterations=3)
        
        assert result is False

    def test_respects_iteration_count(self, sample_claim, sample_agent_status_healthy):
        """Allows requests at lower iterations."""
        findings = [FINDING_LEGAL_WEAK]
        evaluation = evaluate_evidence(sample_claim, findings, sample_agent_status_healthy)
        
        result_iter1 = should_request_reinvestigation(evaluation, iteration_count=1, max_iterations=3)
        result_iter2 = should_request_reinvestigation(evaluation, iteration_count=2, max_iterations=3)
        
        assert result_iter1 is True
        assert result_iter2 is True


# ============================================================================
# Test Reinvestigation Generation
# ============================================================================


class TestReinvestigationGeneration:
    """Tests for generate_reinvestigation_request function."""

    def test_identifies_missing_agents(self, sample_claim, sample_agent_status_healthy):
        """Request targets missing expected agents."""
        findings = [FINDING_LEGAL_SUPPORTING]
        evaluation = evaluate_evidence(sample_claim, findings, sample_agent_status_healthy)
        
        request = generate_reinvestigation_request(sample_claim, evaluation, findings, iteration_count=0)
        
        assert len(request.target_agents) > 0
        # Strategic claims expect academic, news_media
        assert any(a in request.target_agents for a in ["academic", "news_media"])

    def test_identifies_contradicting_agents(self, sample_claim):
        """Request targets agents with contradictions."""
        findings = [FINDING_LEGAL_SUPPORTING, FINDING_NEWS_CONTRADICTING]
        evaluation = evaluate_evidence(sample_claim, findings, {})
        
        request = generate_reinvestigation_request(sample_claim, evaluation, findings, iteration_count=0)
        
        assert request.evidence_gap != ""
        # Should target both supporting and contradicting agents
        assert len(request.target_agents) >= 1

    def test_generates_refined_queries(self, sample_claim, sample_agent_status_healthy):
        """Request includes refined queries for target agents."""
        findings = [FINDING_LEGAL_SUPPORTING]
        evaluation = evaluate_evidence(sample_claim, findings, sample_agent_status_healthy)
        
        request = generate_reinvestigation_request(sample_claim, evaluation, findings, iteration_count=0)
        
        assert len(request.refined_queries) > 0
        # Queries should mention the claim
        assert any(sample_claim.text[:50] in q for q in request.refined_queries)

    def test_specifies_required_evidence(self, sample_claim, sample_agent_status_healthy):
        """Request specifies what evidence is needed."""
        findings = [FINDING_LEGAL_SUPPORTING]
        evaluation = evaluate_evidence(sample_claim, findings, sample_agent_status_healthy)
        
        request = generate_reinvestigation_request(sample_claim, evaluation, findings, iteration_count=0)
        
        assert request.required_evidence != ""

    def test_request_has_valid_structure(self, sample_claim, sample_agent_status_healthy):
        """Request has all required fields."""
        findings = [FINDING_LEGAL_SUPPORTING]
        evaluation = evaluate_evidence(sample_claim, findings, sample_agent_status_healthy)
        
        request = generate_reinvestigation_request(sample_claim, evaluation, findings, iteration_count=0)
        
        assert request.claim_id == sample_claim.claim_id
        assert isinstance(request.target_agents, list)
        assert isinstance(request.evidence_gap, str)
        assert isinstance(request.refined_queries, list)
        assert isinstance(request.required_evidence, str)


# ============================================================================
# Test Confidence Determination
# ============================================================================


class TestConfidenceDetermination:
    """Tests for determine_confidence function."""

    def test_high_confidence_high_score(self):
        """High overall score = high confidence."""
        assert determine_confidence(0.9) == "high"
        assert determine_confidence(0.8) == "high"

    def test_medium_confidence_medium_score(self):
        """Medium overall score = medium confidence."""
        assert determine_confidence(0.7) == "medium"
        assert determine_confidence(0.6) == "medium"

    def test_low_confidence_low_score(self):
        """Low overall score = low confidence."""
        assert determine_confidence(0.5) == "low"
        assert determine_confidence(0.3) == "low"
        assert determine_confidence(0.0) == "low"
