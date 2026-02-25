/**
 * AnalysisPage - Main page for viewing claims extraction results with PDF viewer.
 * Implements FRD 3 Section 7.2, enhanced in FRD 4 with three-panel layout,
 * and FRD 5 with SSE streaming and agent reasoning panel.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAnalysis, useSSE } from "@/hooks";
import { getReportStatus, getPDFUrl } from "@/services/api";
import {
  AnalysisLayout,
  ClaimsPanel,
  AgentReasoningPanel,
} from "@/components/Analysis";
import { PDFViewer } from "@/components/PDFViewer";
import { DashboardGraph } from "@/components/Dashboard";
import type { ReportStatusResponse } from "@/types/report";
import type { Claim } from "@/types/claim";
import "./AnalysisPage.css";

type RightPanelTab = "activity" | "claims";

export function AnalysisPage() {
  const { reportId } = useParams<{ reportId?: string }>();
  const navigate = useNavigate();
  const {
    analysisState,
    claims,
    claimsCount,
    claimsByType,
    claimsByPriority,
    error,
    startAnalysis,
    retry,
    typeFilter,
    priorityFilter,
    setTypeFilter,
    setPriorityFilter,
    filteredClaims,
  } = useAnalysis();

  const [reportInfo, setReportInfo] = useState<ReportStatusResponse | null>(
    null
  );
  const [initialLoading, setInitialLoading] = useState(true);
  const initializedRef = useRef(false);

  // Cross-panel state
  const [activeClaim, setActiveClaim] = useState<Claim | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  // FRD 5: Right panel tab state
  const [rightPanelTab, setRightPanelTab] = useState<RightPanelTab>("activity");

  // FRD 5: SSE connection for real-time agent events
  // Note: SSE should not be enabled during error state (bug 21 fix)
  const isAnalyzing =
    analysisState === "starting" ||
    analysisState === "analyzing";

  const {
    events,
    eventsByAgent,
    isConnected,
    activeAgents,
    completedAgents,
    erroredAgents,
    pipelineComplete,
    error: sseError,
  } = useSSE(reportId, isAnalyzing);

  // Switch to claims tab when analysis completes
  useEffect(() => {
    if (analysisState === "complete" || pipelineComplete) {
      setRightPanelTab("claims");
    }
  }, [analysisState, pipelineComplete]);

  // Fetch report info and start analysis on mount — runs once per reportId
  useEffect(() => {
    if (!reportId) {
      navigate("/");
      return;
    }

    // Guard against double-invocation (React StrictMode / dep changes)
    if (initializedRef.current) return;
    initializedRef.current = true;

    const initialize = async () => {
      try {
        // Get report info
        const info = await getReportStatus(reportId);
        setReportInfo(info);

        // Start analysis automatically
        await startAnalysis(reportId);
      } catch (err) {
        console.error("Failed to initialize analysis:", err);
      } finally {
        setInitialLoading(false);
      }
    };

    initialize();
    // startAnalysis has a stable identity so this only fires on reportId change
  }, [reportId, navigate, startAnalysis]);

  const handleRetry = useCallback(() => {
    if (reportId) {
      retry(reportId);
    }
  }, [reportId, retry]);

  // Handle claim click from PDF highlight or claims list
  const handleClaimClick = useCallback((claim: Claim) => {
    setActiveClaim(claim);
  }, []);

  // Handle page navigation from claims list
  const handleGoToPage = useCallback((claim: Claim) => {
    if (claim.source_page) {
      setCurrentPage(claim.source_page);
    }
    setActiveClaim(claim);
  }, []);

  // Handle page change from PDF viewer
  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  if (!reportId) {
    return null;
  }

  if (initialLoading) {
    return (
      <div className="analysis-page">
        <div className="analysis-page__loading">
          <div className="analysis-progress__spinner">
            <svg
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" opacity="0.25" />
              <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round">
                <animateTransform
                  attributeName="transform"
                  type="rotate"
                  from="0 12 12"
                  to="360 12 12"
                  dur="1s"
                  repeatCount="indefinite"
                />
              </path>
            </svg>
          </div>
          <p>Loading report...</p>
        </div>
      </div>
    );
  }

  const pdfUrl = getPDFUrl(reportId);

  // Right panel content with tabs
  const rightPanelContent = (
    <div className="analysis-page__right-panel">
      {/* Tab bar */}
      <div className="analysis-page__tab-bar">
        <button
          className={`analysis-page__tab ${
            rightPanelTab === "activity" ? "analysis-page__tab--active" : ""
          }`}
          onClick={() => setRightPanelTab("activity")}
        >
          Agent Activity
          {isAnalyzing && (
            <span className="analysis-page__tab-indicator" />
          )}
        </button>
        <button
          className={`analysis-page__tab ${
            rightPanelTab === "claims" ? "analysis-page__tab--active" : ""
          }`}
          onClick={() => setRightPanelTab("claims")}
        >
          Claims ({claimsCount})
        </button>
      </div>

      {/* Tab content */}
      <div className="analysis-page__tab-content">
        {rightPanelTab === "activity" ? (
          <AgentReasoningPanel
            events={events}
            eventsByAgent={eventsByAgent}
            activeAgents={activeAgents}
            completedAgents={completedAgents}
            erroredAgents={erroredAgents}
            pipelineComplete={pipelineComplete}
            isConnected={isConnected}
            reportId={reportId}
          />
        ) : (
          <ClaimsPanel
            claims={filteredClaims}
            activeClaim={activeClaim}
            onClaimClick={handleClaimClick}
            onGoToPage={handleGoToPage}
            typeFilter={typeFilter}
            priorityFilter={priorityFilter}
            onTypeFilterChange={setTypeFilter}
            onPriorityFilterChange={setPriorityFilter}
            claimsByType={claimsByType}
            claimsByPriority={claimsByPriority}
            isLoading={analysisState === "analyzing" && filteredClaims.length === 0}
          />
        )}
      </div>
    </div>
  );

  return (
    <div className="analysis-page analysis-page--three-panel">
      {/* Header */}
      <header className="analysis-page__header">
        <div className="analysis-page__header-content">
          <button
            className="analysis-page__back"
            onClick={() => navigate("/")}
          >
            ← Back
          </button>
          <div className="analysis-page__title-section">
            <h1 className="analysis-page__title">
              {reportInfo?.filename || "Report Analysis"}
            </h1>
            {reportInfo && (
              <span className="analysis-page__meta">
                {reportInfo.page_count} pages
              </span>
            )}
          </div>
          <div className="analysis-page__status">
            <span
              className={`analysis-page__status-badge analysis-page__status-badge--${analysisState}`}
            >
              {analysisState === "complete"
                ? `${claimsCount} Claims Found`
                : analysisState === "analyzing"
                ? "Analyzing..."
                : analysisState === "error"
                ? "Error"
                : "Starting..."}
            </span>
          </div>
        </div>
        {/* Error banner with retry */}
        {analysisState === "error" && error && (
          <div className="analysis-page__error-banner">
            <span className="analysis-page__error-message">
              {error}
            </span>
            <button
              className="analysis-page__retry-button"
              onClick={handleRetry}
            >
              Retry Analysis
            </button>
          </div>
        )}
      </header>

      {/* Main content - Three Panel Layout */}
      <main className="analysis-page__main analysis-page__main--layout">
        <AnalysisLayout
          leftPanel={
            <PDFViewer
              pdfUrl={pdfUrl}
              claims={claims}
              activeClaim={activeClaim}
              onClaimClick={handleClaimClick}
              onPageChange={handlePageChange}
              currentPage={currentPage}
            />
          }
          centerPanel={
            <DashboardGraph
              isAnalyzing={isAnalyzing}
              events={events}
              isConnected={isConnected}
              error={sseError}
            />
          }
          rightPanel={rightPanelContent}
        />
      </main>
    </div>
  );
}
