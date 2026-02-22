"""Tests for stream_utils module.

Tests the emit_* helper functions that use LangGraph's get_stream_writer()
for real-time event streaming.
"""

from unittest.mock import MagicMock, patch

from app.agents.stream_utils import (
    emit_event,
    emit_agent_started,
    emit_agent_thinking,
    emit_agent_completed,
    emit_evidence_found,
    emit_verdict_issued,
    emit_claim_routed,
    emit_reinvestigation_batch,
    emit_pipeline_completed,
    emit_error,
    emit_consistency_check,
    emit_search_executed,
)
from app.agents.state import StreamEvent


class TestEmitEventBasics:
    """Test basic emit_event functionality."""

    def test_emit_event_outside_streaming_context_does_not_raise(self):
        """Verify that emit_event gracefully handles being called outside streaming context."""
        # Should not raise - just logs a debug message
        emit_event("agent_started", "test_agent", {"key": "value"})

    def test_emit_agent_started_outside_context(self):
        """Verify emit_agent_started doesn't raise outside streaming context."""
        emit_agent_started("test_agent")

    def test_emit_agent_thinking_outside_context(self):
        """Verify emit_agent_thinking doesn't raise outside streaming context."""
        emit_agent_thinking("test_agent", "Processing claims...")

    def test_emit_agent_completed_outside_context(self):
        """Verify emit_agent_completed doesn't raise outside streaming context."""
        emit_agent_completed("test_agent", claims_processed=5, findings_count=3)

    def test_emit_evidence_found_outside_context(self):
        """Verify emit_evidence_found doesn't raise outside streaming context."""
        emit_evidence_found(
            agent_name="legal",
            claim_id="claim-001",
            evidence_type="ifrs_compliance",
            summary="Found compliance evidence",
            supports_claim=True,
            confidence="high",
        )

    def test_emit_verdict_issued_outside_context(self):
        """Verify emit_verdict_issued doesn't raise outside streaming context."""
        emit_verdict_issued(
            agent_name="judge",
            claim_id="claim-001",
            verdict="verified",
            confidence="high",
            reasoning="Strong evidence supports the claim",
            ifrs_mapping=["S1.1", "S2.2"],
            cycle_count=1,
        )

    def test_emit_error_outside_context(self):
        """Verify emit_error doesn't raise outside streaming context."""
        emit_error("test_agent", "Something went wrong")

    def test_emit_pipeline_completed_outside_context(self):
        """Verify emit_pipeline_completed doesn't raise outside streaming context."""
        emit_pipeline_completed(
            total_claims=10,
            total_verdicts=10,
            iterations=1,
            total_findings=15,
            verdict_breakdown={"verified": 5, "unverified": 3, "contradicted": 2},
            findings_by_agent={"legal": 5, "geography": 10},
        )


class TestEmitEventWithMockedWriter:
    """Test emit_event with mocked get_stream_writer."""

    def test_emit_event_calls_writer(self):
        """Verify emit_event calls the stream writer with correct StreamEvent."""
        mock_writer = MagicMock()
        
        with patch("app.agents.stream_utils.get_stream_writer", return_value=mock_writer):
            emit_event("agent_started", "test_agent", {"test_key": "test_value"})
            
            # Verify writer was called
            mock_writer.assert_called_once()
            
            # Get the StreamEvent that was passed
            call_args = mock_writer.call_args[0]
            event = call_args[0]
            
            assert isinstance(event, StreamEvent)
            assert event.event_type == "agent_started"
            assert event.agent_name == "test_agent"
            assert event.data == {"test_key": "test_value"}
            assert event.timestamp is not None

    def test_emit_agent_started_creates_correct_event(self):
        """Verify emit_agent_started creates properly formatted event."""
        mock_writer = MagicMock()
        
        with patch("app.agents.stream_utils.get_stream_writer", return_value=mock_writer):
            emit_agent_started("geography")
            
            event = mock_writer.call_args[0][0]
            assert event.event_type == "agent_started"
            assert event.agent_name == "geography"
            assert event.data == {}

    def test_emit_agent_thinking_creates_correct_event(self):
        """Verify emit_agent_thinking creates properly formatted event."""
        mock_writer = MagicMock()
        
        with patch("app.agents.stream_utils.get_stream_writer", return_value=mock_writer):
            emit_agent_thinking("legal", "Analyzing IFRS compliance...")
            
            event = mock_writer.call_args[0][0]
            assert event.event_type == "agent_thinking"
            assert event.agent_name == "legal"
            assert event.data["message"] == "Analyzing IFRS compliance..."

    def test_emit_evidence_found_creates_correct_event(self):
        """Verify emit_evidence_found creates properly formatted event."""
        mock_writer = MagicMock()
        
        with patch("app.agents.stream_utils.get_stream_writer", return_value=mock_writer):
            emit_evidence_found(
                agent_name="academic",
                claim_id="claim-123",
                evidence_type="peer_reviewed",
                summary="Found supporting research",
                supports_claim=True,
                confidence="high",
            )
            
            event = mock_writer.call_args[0][0]
            assert event.event_type == "evidence_found"
            assert event.agent_name == "academic"
            assert event.data["claim_id"] == "claim-123"
            assert event.data["evidence_type"] == "peer_reviewed"
            assert event.data["summary"] == "Found supporting research"
            assert event.data["supports_claim"] is True
            assert event.data["confidence"] == "high"

    def test_emit_verdict_issued_creates_correct_event(self):
        """Verify emit_verdict_issued creates properly formatted event."""
        mock_writer = MagicMock()
        
        with patch("app.agents.stream_utils.get_stream_writer", return_value=mock_writer):
            emit_verdict_issued(
                agent_name="judge",
                claim_id="claim-456",
                verdict="contradicted",
                confidence="medium",
                reasoning="Evidence shows inconsistencies",
                ifrs_mapping=["S1.5"],
                cycle_count=2,
            )
            
            event = mock_writer.call_args[0][0]
            assert event.event_type == "verdict_issued"
            assert event.agent_name == "judge"
            assert event.data["claim_id"] == "claim-456"
            assert event.data["verdict"] == "contradicted"
            assert event.data["confidence"] == "medium"
            assert event.data["reasoning"] == "Evidence shows inconsistencies"
            assert event.data["ifrs_mapping"] == ["S1.5"]
            assert event.data["cycle_count"] == 2

    def test_emit_claim_routed_creates_correct_event(self):
        """Verify emit_claim_routed creates properly formatted event."""
        mock_writer = MagicMock()
        
        with patch("app.agents.stream_utils.get_stream_writer", return_value=mock_writer):
            emit_claim_routed(
                claim_id="claim-789",
                assigned_agents=["geography", "legal"],
            )
            
            event = mock_writer.call_args[0][0]
            assert event.event_type == "claim_routed"
            assert event.agent_name == "orchestrator"
            assert event.data["claim_id"] == "claim-789"
            assert event.data["assigned_agents"] == ["geography", "legal"]

    def test_emit_reinvestigation_batch_creates_correct_event(self):
        """Verify emit_reinvestigation_batch creates properly formatted event."""
        mock_writer = MagicMock()
        
        with patch("app.agents.stream_utils.get_stream_writer", return_value=mock_writer):
            emit_reinvestigation_batch(
                agent_name="judge",
                claim_ids=["claim-001", "claim-002"],
                target_agents=["geography", "academic"],
                cycle=2,
            )
            
            event = mock_writer.call_args[0][0]
            assert event.event_type == "reinvestigation"
            assert event.agent_name == "judge"
            assert event.data["claim_ids"] == ["claim-001", "claim-002"]
            assert event.data["target_agents"] == ["geography", "academic"]
            assert event.data["cycle"] == 2

    def test_emit_pipeline_completed_creates_correct_event(self):
        """Verify emit_pipeline_completed creates properly formatted event."""
        mock_writer = MagicMock()
        
        with patch("app.agents.stream_utils.get_stream_writer", return_value=mock_writer):
            emit_pipeline_completed(
                total_claims=10,
                total_verdicts=10,
                iterations=2,
            )
            
            event = mock_writer.call_args[0][0]
            assert event.event_type == "pipeline_completed"
            assert event.agent_name is None
            assert event.data["total_claims"] == 10
            assert event.data["total_verdicts"] == 10
            assert event.data["iterations"] == 2

    def test_emit_consistency_check_creates_correct_event(self):
        """Verify emit_consistency_check creates properly formatted event."""
        mock_writer = MagicMock()
        
        with patch("app.agents.stream_utils.get_stream_writer", return_value=mock_writer):
            emit_consistency_check(
                agent_name="data_metrics",
                check_name="scope_total_check",
                claim_id="claim-001",
                result="pass",
                severity="high",
                details="Totals match",
                message="Scope totals are consistent",
            )
            
            event = mock_writer.call_args[0][0]
            assert event.event_type == "consistency_check"
            assert event.agent_name == "data_metrics"
            assert event.data["check_name"] == "scope_total_check"
            assert event.data["claim_id"] == "claim-001"
            assert event.data["result"] == "pass"
            assert event.data["severity"] == "high"
            assert event.data["message"] == "Scope totals are consistent"

    def test_emit_search_executed_creates_correct_event(self):
        """Verify emit_search_executed creates properly formatted event."""
        mock_writer = MagicMock()
        
        with patch("app.agents.stream_utils.get_stream_writer", return_value=mock_writer):
            emit_search_executed(
                agent_name="news_media",
                query="Tesla sustainability controversy",
                results_count=15,
                source="tavily",
            )
            
            event = mock_writer.call_args[0][0]
            assert event.event_type == "search_executed"
            assert event.agent_name == "news_media"
            assert event.data["query"] == "Tesla sustainability controversy"
            assert event.data["results_count"] == 15
            assert event.data["source"] == "tavily"


class TestEmitEventEdgeCases:
    """Test edge cases and error handling."""

    def test_emit_event_with_none_data(self):
        """Verify emit_event handles None data correctly."""
        mock_writer = MagicMock()
        
        with patch("app.agents.stream_utils.get_stream_writer", return_value=mock_writer):
            emit_event("agent_started", "test_agent", None)
            
            event = mock_writer.call_args[0][0]
            assert event.data == {}

    def test_emit_event_with_empty_agent_name(self):
        """Verify emit_event handles None agent_name (for pipeline events)."""
        mock_writer = MagicMock()
        
        with patch("app.agents.stream_utils.get_stream_writer", return_value=mock_writer):
            emit_event("pipeline_completed", None, {"total_claims": 10})
            
            event = mock_writer.call_args[0][0]
            assert event.agent_name is None
            assert event.event_type == "pipeline_completed"

    def test_emit_event_handles_writer_exception_gracefully(self):
        """Verify emit_event catches and logs exceptions from writer."""
        mock_writer = MagicMock(side_effect=RuntimeError("Writer error"))
        
        with patch("app.agents.stream_utils.get_stream_writer", return_value=mock_writer):
            # Should not raise
            emit_event("agent_started", "test_agent", {})

    def test_emit_event_handles_get_stream_writer_exception_gracefully(self):
        """Verify emit_event catches exceptions from get_stream_writer itself."""
        with patch("app.agents.stream_utils.get_stream_writer", side_effect=RuntimeError("No context")):
            # Should not raise
            emit_event("agent_started", "test_agent", {})
