/**
 * AnalysisPage — two-tab layout with resizable splits.
 *   Document tab      → PDF viewer (left) + Claims (right)
 *   Investigation tab → Graph (left, wider) + Agent activity (right, narrower sidebar)
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAnalysis, useSSE } from "@/hooks";
import { getReportStatus, getPDFUrl } from "@/services/api";
import { ClaimsPanel, AgentReasoningPanel } from "@/components/Analysis";
import { PDFViewer } from "@/components/PDFViewer";
import { DashboardGraph } from "@/components/Dashboard";
import type { ReportStatusResponse } from "@/types/report";
import type { Claim } from "@/types/claim";
import { ArrowLeft } from "lucide-react";
import "./AnalysisPage.css";

type MainTab = "document" | "investigation";

// ─── Resizable split ────────────────────────────────────────────────────────

interface ResizableSplitProps {
  left: React.ReactNode;
  right: React.ReactNode;
  /** Initial left width as a percentage (0–100). Defaults to 62. */
  defaultLeftPct?: number;
  minLeftPct?: number;
  maxLeftPct?: number;
}

function ResizableSplit({
  left,
  right,
  defaultLeftPct = 62,
  minLeftPct = 20,
  maxLeftPct = 80,
}: ResizableSplitProps) {
  const [leftPct, setLeftPct] = useState(defaultLeftPct);
  const containerRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    dragging.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }, []);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!dragging.current || !containerRef.current) return;
      const { left: cLeft, width } = containerRef.current.getBoundingClientRect();
      const pct = ((e.clientX - cLeft) / width) * 100;
      setLeftPct(Math.max(minLeftPct, Math.min(maxLeftPct, pct)));
    };
    const onUp = () => {
      if (dragging.current) {
        dragging.current = false;
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
      }
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [minLeftPct, maxLeftPct]);

  return (
    <div ref={containerRef} className="analysis-split">
      <div className="analysis-split__pane" style={{ width: `${leftPct}%` }}>
        {left}
      </div>
      {/* Draggable handle */}
      <div
        className="analysis-split__handle"
        onMouseDown={onMouseDown}
        role="separator"
        aria-orientation="vertical"
      />
      <div className="analysis-split__pane" style={{ width: `${100 - leftPct}%` }}>
        {right}
      </div>
    </div>
  );
}

// ─── Main page ───────────────────────────────────────────────────────────────

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

  const [reportInfo, setReportInfo] = useState<ReportStatusResponse | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const initializedRef = useRef(false);

  const [activeClaim, setActiveClaim] = useState<Claim | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [mainTab, setMainTab] = useState<MainTab>("document");

  const isAnalyzing = analysisState === "starting" || analysisState === "analyzing";

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

  useEffect(() => {
    if (!reportId) {
      navigate("/analysis");
      return;
    }
    if (initializedRef.current) return;
    initializedRef.current = true;

    const initialize = async () => {
      try {
        const info = await getReportStatus(reportId);
        setReportInfo(info);
        await startAnalysis(reportId);
      } catch (err) {
        console.error("Failed to initialize analysis:", err);
      } finally {
        setInitialLoading(false);
      }
    };
    initialize();
  }, [reportId, navigate, startAnalysis]);

  const handleRetry = useCallback(() => { if (reportId) retry(reportId); }, [reportId, retry]);
  const handleClaimClick = useCallback((claim: Claim) => setActiveClaim(claim), []);
  const handleGoToPage = useCallback((claim: Claim) => {
    if (claim.source_page) setCurrentPage(claim.source_page);
    setActiveClaim(claim);
  }, []);
  const handlePageChange = useCallback((page: number) => setCurrentPage(page), []);

  if (!reportId) return null;

  if (initialLoading) {
    return (
      <div className="analysis-page">
        <div className="analysis-page__loading">
          <div className="analysis-progress__spinner">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" opacity="0.25" />
              <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round">
                <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite" />
              </path>
            </svg>
          </div>
          <p>Loading report...</p>
        </div>
      </div>
    );
  }

  const pdfUrl = getPDFUrl(reportId);

  return (
    <div className="analysis-page">
      {/* ── Header ── */}
      <header className="analysis-page__header">
        <div className="analysis-page__header-content">
          <button className="analysis-page__back" onClick={() => navigate("/analysis")} aria-label="Back">
            <ArrowLeft size={14} />
            <span>Analyses</span>
          </button>

          <div className="analysis-page__title-section">
            <h1 className="analysis-page__title">{reportInfo?.filename || "Report Analysis"}</h1>
            {reportInfo && <span className="analysis-page__meta">{reportInfo.page_count} pages</span>}
          </div>

          <div className="analysis-page__status">
            <span className={`analysis-page__status-badge analysis-page__status-badge--${analysisState}`}>
              {analysisState === "complete" ? `${claimsCount} Claims Found`
                : analysisState === "analyzing" ? "Analyzing…"
                : analysisState === "error" ? "Error"
                : "Starting…"}
            </span>
          </div>
        </div>

        {analysisState === "error" && error && (
          <div className="analysis-page__error-banner">
            <span className="analysis-page__error-message">{error}</span>
            <button className="analysis-page__retry-button" onClick={handleRetry}>Retry Analysis</button>
          </div>
        )}

        {/* ── Centred tab bar ── */}
        <div className="analysis-page__main-tabs">
          <button
            className={`analysis-page__main-tab ${mainTab === "document" ? "analysis-page__main-tab--active" : ""}`}
            onClick={() => setMainTab("document")}
          >
            Document
          </button>
          <button
            className={`analysis-page__main-tab ${mainTab === "investigation" ? "analysis-page__main-tab--active" : ""}`}
            onClick={() => setMainTab("investigation")}
          >
            Investigation
            {isAnalyzing && <span className="analysis-page__tab-indicator" />}
          </button>
        </div>
      </header>

      {/* ── Tab content ── */}
      <main className="analysis-page__main">

        {/* Document: PDF (left ~62%) | Claims (right ~38%) */}
        {mainTab === "document" && (
          <ResizableSplit
            defaultLeftPct={62}
            minLeftPct={25}
            maxLeftPct={80}
            left={
              <PDFViewer
                pdfUrl={pdfUrl}
                claims={claims}
                activeClaim={activeClaim}
                onClaimClick={handleClaimClick}
                onPageChange={handlePageChange}
                currentPage={currentPage}
              />
            }
            right={
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
            }
          />
        )}

        {/* Investigation: Graph (left ~70%) | Agent activity sidebar (right ~30%) */}
        {mainTab === "investigation" && (
          <ResizableSplit
            defaultLeftPct={70}
            minLeftPct={30}
            maxLeftPct={85}
            left={
              <DashboardGraph
                isAnalyzing={isAnalyzing}
                events={events}
                isConnected={isConnected}
                error={sseError}
              />
            }
            right={
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
            }
          />
        )}
      </main>
    </div>
  );
}
