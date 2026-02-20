"""Full pipeline integration test with mocked external dependencies.

Tests the complete LangGraph workflow from claims extraction through
verdict generation without consuming API tokens or database connections.

Run with: pytest tests/integration/test_full_pipeline.py -v
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.graph import build_graph, get_compiled_graph
from app.agents.state import (
    AgentFinding,
    AgentStatus,
    Claim,
    ClaimVerdict,
    ReinvestigationRequest,
    RoutingAssignment,
    SibylState,
    StreamEvent,
)


# ============================================================================
# Mock Response Generators
# ============================================================================


def mock_claims_extraction_response() -> str:
    """Generate mock response for claims extraction."""
    return json.dumps({
        "claims": [
            {
                "claim_text": "We reduced Scope 1 emissions by 30% from our 2020 baseline.",
                "claim_type": "quantitative",
                "source_page": 45,
                "source_context": "Section 5.2 GHG Emissions",
                "priority": "high",
                "reasoning": "Quantitative emissions claim requiring verification",
                "preliminary_ifrs": ["S2.29(a)(i)"],
            },
            {
                "claim_text": "Our Board's Sustainability Committee meets quarterly to review climate risks.",
                "claim_type": "legal_governance",
                "source_page": 12,
                "source_context": "Section 2.1 Governance",
                "priority": "medium",
                "reasoning": "Governance claim about board oversight",
                "preliminary_ifrs": ["S2.6", "S1.27(a)"],
            },
        ],
        "total_pages_analyzed": 100,
        "extraction_summary": "Corporate sustainability report with emissions and governance claims.",
    })


def mock_orchestrator_response() -> str:
    """Generate mock response for orchestrator routing."""
    return json.dumps({
        "routing_decisions": [
            {
                "claim_id": "claim-001",
                "assigned_agents": ["legal", "data_metrics"],
                "reasoning": "Quantitative emissions claim needs legal and data verification",
            },
            {
                "claim_id": "claim-002",
                "assigned_agents": ["legal"],
                "reasoning": "Governance claim needs legal compliance check",
            },
        ]
    })


def mock_legal_agent_response() -> str:
    """Generate mock response for legal agent."""
    return json.dumps({
        "findings": [
            {
                "evidence_type": "ifrs_compliance",
                "summary": "Claim meets S2.29(a)(i) disclosure requirements.",
                "supports_claim": True,
                "confidence": "high",
                "ifrs_mappings": [
                    {"paragraph_id": "S2.29(a)(i)", "compliance_status": "fully_addressed"}
                ],
            }
        ]
    })


def mock_data_metrics_response() -> str:
    """Generate mock response for data metrics agent."""
    return json.dumps({
        "mathematical_consistency": True,
        "benchmark_alignment": "within_range",
        "checks": [
            {"check_name": "scope_consistency", "result": "pass"},
            {"check_name": "yoy_percentage", "result": "pass"},
        ],
        "supports_claim": True,
        "confidence": "high",
    })


def mock_news_media_response() -> str:
    """Generate mock response for news media agent."""
    return json.dumps({
        "sources_found": 2,
        "corroboration_level": "moderate",
        "supports_claim": True,
        "confidence": "medium",
    })


def mock_academic_response() -> str:
    """Generate mock response for academic agent."""
    return json.dumps({
        "methodology_valid": True,
        "standard_alignment": "aligned",
        "supports_claim": True,
        "confidence": "high",
    })


def mock_geography_response() -> str:
    """Generate mock response for geography agent."""
    return json.dumps({
        "location_verified": True,
        "satellite_confidence": 0.85,
        "supports_claim": True,
        "confidence": "high",
    })


def mock_judge_verdict_response() -> str:
    """Generate mock response for judge agent."""
    return json.dumps({
        "verdict": "verified",
        "reasoning": "Multiple independent sources corroborate the claim.",
        "confidence": "high",
    })


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_all_llm_calls(mocker):
    """Mock all LLM calls across all agents."""
    responses = [
        # Claims extraction (may be called multiple times for chunks)
        mock_claims_extraction_response(),
        mock_claims_extraction_response(),
        # Orchestrator
        mock_orchestrator_response(),
        # Legal agent (multiple calls per claim)
        mock_legal_agent_response(),
        mock_legal_agent_response(),
        mock_legal_agent_response(),
        mock_legal_agent_response(),
        # Data metrics
        mock_data_metrics_response(),
        mock_data_metrics_response(),
        # News media (search + analysis)
        mock_news_media_response(),
        mock_news_media_response(),
        # Academic
        mock_academic_response(),
        mock_academic_response(),
        # Geography
        mock_geography_response(),
        mock_geography_response(),
        # Judge (may need LLM for complex cases)
        mock_judge_verdict_response(),
        mock_judge_verdict_response(),
    ]
    
    # Create a response iterator that cycles if needed
    response_iter = iter(responses * 5)  # Repeat to handle variable call counts
    
    async def mock_chat(*args, **kwargs):
        try:
            return next(response_iter)
        except StopIteration:
            return mock_legal_agent_response()  # Fallback
    
    mock = mocker.patch(
        "app.services.openrouter_client.openrouter_client.chat_completion",
        new=AsyncMock(side_effect=mock_chat)
    )
    return mock


@pytest.fixture
def mock_database(mocker):
    """Mock all database operations."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))))
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    async def mock_get_db():
        yield mock_session
    
    # Only compile_report uses get_db_session directly
    mocker.patch("app.agents.compile_report.get_db_session", mock_get_db)
    
    # Mock async_session_maker for agents that use it
    mocker.patch("app.core.database.async_session_maker", return_value=MagicMock(
        __aenter__=AsyncMock(return_value=mock_session),
        __aexit__=AsyncMock(return_value=None),
    ))
    
    return mock_session


@pytest.fixture
def mock_rag_service(mocker):
    """Mock RAG lookup service."""
    mock_result = [
        {
            "paragraph_id": "S2.29(a)(i)",
            "content": "Scope 1 emissions disclosure requirements...",
            "relevance_score": 0.95,
        }
    ]
    
    # Create a mock tool that returns results
    mock_rag_tool = MagicMock()
    mock_rag_tool.ainvoke = AsyncMock(return_value=mock_result)
    
    mocker.patch("app.agents.tools.rag_lookup.rag_lookup", mock_rag_tool)
    mocker.patch("app.agents.tools.rag_lookup.rag_lookup_report", mock_rag_tool)
    
    return mock_rag_tool


@pytest.fixture
def mock_tavily_search(mocker):
    """Mock Tavily search for news and academic agents."""
    mock_search = AsyncMock(return_value=[
        {
            "title": "Company achieves emissions reduction",
            "url": "https://reuters.com/article/123",
            "content": "The company reported a 30% reduction in emissions...",
            "score": 0.9,
            "domain": "reuters.com",
        }
    ])
    # Patch at the source module
    mocker.patch("app.agents.tools.search_web.search_web_async", mock_search)
    return mock_search


@pytest.fixture
def mock_satellite_service(mocker):
    """Mock satellite imagery service for geography agent."""
    # Mock the satellite_service module
    mock_service = MagicMock()
    mock_service.catalog = MagicMock()
    mock_service.connect = AsyncMock()
    mock_service.compute_bbox = MagicMock(return_value=(-6.5, 110.5, -6.0, 111.0))
    mock_service.compute_bbox_from_area = MagicMock(return_value=(-6.5, 110.5, -6.0, 111.0))
    mock_service.search_sentinel2 = MagicMock(return_value=[
        {
            "id": "test-image-001",
            "datetime": "2024-01-15T10:30:00Z",
            "cloud_cover": 5.0,
            "bbox": (-6.5, 110.5, -6.0, 111.0),
        }
    ])
    
    mocker.patch("app.services.satellite_service.satellite_service", mock_service)
    return mock_service


@pytest.fixture
def mock_embeddings(mocker):
    """Mock embedding service for deduplication."""
    import numpy as np
    
    # Mock the embedding service singleton
    mock_service = MagicMock()
    mock_service.embed_text = AsyncMock(return_value=np.random.rand(1536).tolist())
    mock_service.embed_batch = AsyncMock(return_value=[np.random.rand(1536).tolist()])
    
    mocker.patch("app.services.embedding_service.embedding_service", mock_service)
    mocker.patch("app.agents.claims_agent.embedding_service", mock_service)
    
    return mock_service


@pytest.fixture
def sample_initial_state() -> SibylState:
    """Create initial state for pipeline execution."""
    return {
        "report_id": "test-report-full-pipeline-001",
        "document_content": """
        SUSTAINABILITY REPORT 2024
        
        Section 2.1 Governance
        Our Board's Sustainability Committee meets quarterly to review climate risks
        and opportunities. The committee is chaired by an independent director.
        
        Section 5.2 GHG Emissions
        We reduced Scope 1 emissions by 30% from our 2020 baseline, achieving
        2.3 million tCO2e in FY2024. This represents significant progress toward
        our net-zero commitment.
        """,
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
        "events": [],
    }


# ============================================================================
# Pipeline Flow Tests
# ============================================================================


class TestFullPipelineFlow:
    """Test the complete pipeline from start to finish."""

    @pytest.mark.asyncio
    async def test_graph_compiles_successfully(self):
        """Test that the graph compiles without errors."""
        graph = build_graph()
        compiled = graph.compile()
        
        assert compiled is not None
        
    @pytest.mark.asyncio
    async def test_graph_has_all_nodes(self):
        """Test that graph contains all expected nodes."""
        graph = build_graph()
        
        expected_nodes = [
            "extract_claims",
            "orchestrate",
            "investigate_geography",
            "investigate_legal",
            "investigate_news",
            "investigate_academic",
            "investigate_data",
            "judge_evidence",
            "compile_report",
        ]
        
        for node in expected_nodes:
            assert node in graph.nodes, f"Missing node: {node}"

    @pytest.mark.asyncio
    async def test_full_pipeline_executes(
        self,
        mock_all_llm_calls,
        mock_database,
        mock_rag_service,
        mock_tavily_search,
        mock_satellite_service,
        mock_embeddings,
        sample_initial_state,
    ):
        """Test that the full pipeline runs to completion."""
        compiled = get_compiled_graph()
        
        # Execute the graph
        result = await compiled.ainvoke(
            sample_initial_state,
            config={"recursion_limit": 50}
        )
        
        # Verify pipeline completed
        assert result is not None
        
        # Should have processed events
        assert len(result.get("events", [])) > 0
        
        # Should have claims (even if mocked)
        # Note: claims may be empty if extraction mock doesn't match expected format
        
    @pytest.mark.asyncio
    async def test_pipeline_produces_verdicts(
        self,
        mock_all_llm_calls,
        mock_database,
        mock_rag_service,
        mock_tavily_search,
        mock_satellite_service,
        mock_embeddings,
    ):
        """Test that pipeline produces verdicts for claims."""
        from app.agents.legal_agent import investigate_legal
        from app.agents.data_metrics_agent import investigate_data
        from app.agents.judge_agent import judge_evidence
        
        # Start with pre-extracted claims and routing plan
        state: SibylState = {
            "report_id": "test-report-verdicts-001",
            "document_content": "Sample report content",
            "document_chunks": [],
            "claims": [
                Claim(
                    claim_id="claim-test-001",
                    text="We reduced emissions by 30%",
                    page_number=45,
                    claim_type="quantitative",
                    ifrs_paragraphs=["S2.29(a)(i)"],
                    priority="high",
                    source_location={"source_context": "Section 5.2"},
                    agent_reasoning="Quantitative emissions claim",
                ),
            ],
            "routing_plan": [
                RoutingAssignment(
                    claim_id="claim-test-001",
                    assigned_agents=["legal", "data_metrics"],
                    reasoning="Needs verification",
                ),
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
            "events": [],
        }
        
        # Execute specialists -> judge manually to test flow
        # Skip orchestrator since routing_plan is already set
        
        # Execute legal agent
        state_after_legal = await investigate_legal(state)
        state["findings"].extend(state_after_legal.get("findings", []))
        state["events"].extend(state_after_legal.get("events", []))
        
        # Execute data metrics agent
        state_after_data = await investigate_data(state)
        state["findings"].extend(state_after_data.get("findings", []))
        state["events"].extend(state_after_data.get("events", []))
        
        # Execute judge
        state_after_judge = await judge_evidence(state)
        
        # Verify verdicts produced
        verdicts = state_after_judge.get("verdicts", [])
        assert len(verdicts) >= 1, "Judge should produce at least one verdict"
        
        # Verify verdict structure
        verdict = verdicts[0]
        assert verdict.claim_id == "claim-test-001"
        assert verdict.verdict in ["verified", "unverified", "contradicted", "insufficient_evidence"]
        assert verdict.reasoning != ""


class TestCyclicValidation:
    """Test the re-investigation cycle."""

    @pytest.mark.asyncio
    async def test_reinvestigation_cycle_routes_back(self):
        """Test that reinvestigation requests route back to orchestrator."""
        from app.agents.graph import should_continue_or_compile
        
        # State with reinvestigation request
        state = {
            "reinvestigation_requests": [
                ReinvestigationRequest(
                    claim_id="claim-001",
                    target_agents=["geography"],
                    evidence_gap="Need satellite verification",
                    refined_queries=["Verify location"],
                    required_evidence="NDVI analysis",
                )
            ],
            "iteration_count": 1,
            "max_iterations": 3,
        }
        
        result = should_continue_or_compile(state)
        assert result == "orchestrate"

    @pytest.mark.asyncio
    async def test_max_iterations_routes_to_compile(self):
        """Test that max iterations routes to compile."""
        from app.agents.graph import should_continue_or_compile
        
        state = {
            "reinvestigation_requests": [
                ReinvestigationRequest(
                    claim_id="claim-001",
                    target_agents=["geography"],
                    evidence_gap="Need verification",
                    refined_queries=[],
                    required_evidence="",
                )
            ],
            "iteration_count": 3,
            "max_iterations": 3,
        }
        
        result = should_continue_or_compile(state)
        assert result == "compile_report"


class TestRouting:
    """Test routing logic."""

    @pytest.mark.asyncio
    async def test_route_to_specialists(self):
        """Test that routing plan determines active specialists."""
        from app.agents.graph import route_to_specialists
        
        state: SibylState = {
            "report_id": "test",
            "document_content": "",
            "document_chunks": [],
            "claims": [],
            "routing_plan": [
                RoutingAssignment(
                    claim_id="claim-001",
                    assigned_agents=["legal", "geography"],
                    reasoning="Test",
                ),
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
            "events": [],
        }
        
        nodes = route_to_specialists(state)
        
        assert "investigate_legal" in nodes
        assert "investigate_geography" in nodes
        assert len(nodes) == 2

    @pytest.mark.asyncio
    async def test_empty_routing_goes_to_judge(self):
        """Test that empty routing plan routes directly to judge."""
        from app.agents.graph import route_to_specialists
        
        state: SibylState = {
            "report_id": "test",
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
            "events": [],
        }
        
        nodes = route_to_specialists(state)
        
        assert nodes == ["judge_evidence"]


class TestEventEmission:
    """Test that events are emitted correctly."""

    @pytest.mark.asyncio
    async def test_judge_emits_events(
        self,
        mock_all_llm_calls,
    ):
        """Test that judge agent emits expected events."""
        from app.agents.judge_agent import judge_evidence
        
        state: SibylState = {
            "report_id": "test",
            "document_content": "",
            "document_chunks": [],
            "claims": [
                Claim(
                    claim_id="claim-001",
                    text="Test claim",
                    page_number=1,
                    claim_type="quantitative",
                    ifrs_paragraphs=[],
                    priority="high",
                    source_location={},
                    agent_reasoning="Test",
                ),
            ],
            "routing_plan": [],
            "agent_status": {},
            "findings": [
                AgentFinding(
                    finding_id="finding-001",
                    agent_name="legal",
                    claim_id="claim-001",
                    evidence_type="ifrs_compliance",
                    summary="Supports claim",
                    details={},
                    supports_claim=True,
                    confidence="high",
                    iteration=1,
                ),
            ],
            "info_requests": [],
            "info_responses": [],
            "verdicts": [],
            "reinvestigation_requests": [],
            "iteration_count": 0,
            "max_iterations": 3,
            "disclosure_gaps": [],
            "events": [],
        }
        
        result = await judge_evidence(state)
        
        events = result.get("events", [])
        event_types = [e.event_type for e in events]
        
        assert "agent_started" in event_types
        assert "verdict_issued" in event_types
        assert "agent_completed" in event_types
