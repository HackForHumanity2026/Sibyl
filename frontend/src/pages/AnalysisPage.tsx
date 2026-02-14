/**
 * AnalysisPage - Main page for viewing claims extraction results.
 * Implements FRD 3 Section 7.2.
 */

import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAnalysis } from "@/hooks";
import { getReportStatus } from "@/services/api";
import {
  ClaimCard,
  ClaimsFilter,
  AnalysisProgress,
} from "@/components/Analysis";
import type { ReportStatusResponse } from "@/types/report";

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

  const handleRetry = () => {
    if (reportId) {
      retry(reportId);
    }
  };

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

  return (
    <div className="analysis-page">
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
      </header>

      {/* Main content */}
      <main className="analysis-page__main">
        {/* Show progress indicator while analyzing */}
        {(analysisState === "starting" ||
          analysisState === "analyzing" ||
          analysisState === "error") && (
          <AnalysisProgress
            state={analysisState}
            claimsCount={claimsCount}
            error={error}
            onRetry={handleRetry}
          />
        )}

        {/* Show claims when complete */}
        {analysisState === "complete" && (
          <div className="analysis-page__claims-section">
            {/* Filters */}
            <ClaimsFilter
              typeFilter={typeFilter}
              priorityFilter={priorityFilter}
              onTypeChange={setTypeFilter}
              onPriorityChange={setPriorityFilter}
              claimsByType={claimsByType}
              claimsByPriority={claimsByPriority}
            />

            {/* Claims count */}
            <div className="analysis-page__claims-count">
              Showing {filteredClaims.length} of {claims.length} claims
            </div>

            {/* Claims list */}
            <div className="analysis-page__claims-list">
              {filteredClaims.length > 0 ? (
                filteredClaims.map((claim) => (
                  <ClaimCard key={claim.id} claim={claim} />
                ))
              ) : (
                <div className="analysis-page__no-claims">
                  <p>No claims match the current filters.</p>
                  <button
                    onClick={() => {
                      setTypeFilter(null);
                      setPriorityFilter(null);
                    }}
                  >
                    Clear Filters
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Idle state (shouldn't normally show) */}
        {analysisState === "idle" && (
          <div className="analysis-page__idle">
            <p>Ready to analyze</p>
            <button onClick={() => startAnalysis(reportId)}>
              Start Analysis
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
