/**
 * PDFViewer - Embedded PDF renderer with claim highlight overlays.
 * Implements FRD 4 Section 4 (PDF Viewer Components).
 *
 * Uses react-pdf (wojtekmaj) - MIT license, no watermarks.
 *
 * Architecture:
 *   - All pages rendered in a scroll container
 *   - IntersectionObserver tracks which page is most visible (no feedback loops)
 *   - goToPage scrolls to the target page element via refs
 *   - Zoom is handled by scaling the react-pdf width prop
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/TextLayer.css";
import "react-pdf/dist/Page/AnnotationLayer.css";
import type { Claim } from "@/types/claim";
import type { PDFViewerProps, ClaimHighlightData } from "./types";
import { ClaimHighlight } from "./ClaimHighlight";
import { HighlightTooltip } from "./HighlightTooltip";
import { PDFToolbar } from "./PDFToolbar";
import { useClaimHighlights } from "@/hooks/useClaimHighlights";

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.mjs",
  import.meta.url,
).toString();

const BASE_PAGE_WIDTH = 700;
const ZOOM_STEP = 25;
const MIN_ZOOM = 50;
const MAX_ZOOM = 300;

export function PDFViewer({
  pdfUrl,
  claims,
  activeClaim,
  onClaimClick,
  onPageChange,
  currentPage,
}: PDFViewerProps) {
  // ── Core state ─────────────────────────────────────────────────────
  const [totalPages, setTotalPages] = useState(0);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // ── Tooltip state ──────────────────────────────────────────────────
  const [tooltipClaim, setTooltipClaim] = useState<Claim | null>(null);
  const [tooltipAnchor, setTooltipAnchor] = useState<ClaimHighlightData["rects"][0] | null>(null);
  const [pulsingClaimId, setPulsingClaimId] = useState<string | null>(null);

  // ── Refs ────────────────────────────────────────────────────────────
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  // Track whether a programmatic scroll is in progress so the
  // IntersectionObserver doesn't fight with goToPage calls.
  const isProgrammaticScrollRef = useRef(false);

  const { getHighlightsForPage, computeHighlights } = useClaimHighlights(claims);

  // ── Document load handlers ─────────────────────────────────────────
  const handleDocumentLoadSuccess = useCallback(
    ({ numPages }: { numPages: number }) => {
      setTotalPages(numPages);
      setIsLoading(false);
      setError(null);
    },
    [],
  );

  const handleDocumentLoadError = useCallback(() => {
    setIsLoading(false);
    setError("Unable to load PDF. The document may not be available.");
  }, []);

  // ── Page tracking via IntersectionObserver ─────────────────────────
  // Fires only when the user *scrolls*; programmatic scrolls are gated.
  useEffect(() => {
    if (totalPages === 0 || !scrollContainerRef.current) return;

    const visibilityMap = new Map<number, number>(); // pageNum → ratio

    const observer = new IntersectionObserver(
      (entries) => {
        if (isProgrammaticScrollRef.current) return; // skip during goToPage

        for (const entry of entries) {
          const pageNum = Number(entry.target.getAttribute("data-page-number"));
          if (!isNaN(pageNum)) {
            visibilityMap.set(pageNum, entry.intersectionRatio);
          }
        }

        // Find the page with the highest visibility
        let bestPage = currentPage;
        let bestRatio = 0;
        for (const [page, ratio] of visibilityMap) {
          if (ratio > bestRatio) {
            bestRatio = ratio;
            bestPage = page;
          }
        }

        if (bestPage !== currentPage && bestRatio > 0) {
          onPageChange(bestPage);
        }
      },
      {
        root: scrollContainerRef.current,
        threshold: [0, 0.25, 0.5, 0.75, 1],
      },
    );

    // Observe all page elements
    for (const [, el] of pageRefs.current) {
      observer.observe(el);
    }

    return () => observer.disconnect();
  }, [totalPages, currentPage, onPageChange]);

  // ── goToPage (scrolls to a page element) ───────────────────────────
  const goToPage = useCallback(
    (page: number) => {
      const el = pageRefs.current.get(page);
      if (!el || !scrollContainerRef.current) return;

      isProgrammaticScrollRef.current = true;
      el.scrollIntoView({ behavior: "smooth", block: "start" });

      // Allow the observer to resume after the scroll settles
      const timer = setTimeout(() => {
        isProgrammaticScrollRef.current = false;
      }, 600);

      onPageChange(page);

      return () => clearTimeout(timer);
    },
    [onPageChange],
  );

  // ── Navigate to active claim's page + pulse ────────────────────────
  useEffect(() => {
    if (!activeClaim?.source_page) return;

    goToPage(activeClaim.source_page);

    setPulsingClaimId(activeClaim.id);
    const timer = setTimeout(() => setPulsingClaimId(null), 600);
    return () => clearTimeout(timer);
    // Only react to activeClaim *identity* changes
  }, [activeClaim?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Zoom handlers ──────────────────────────────────────────────────
  const handleZoomChange = useCallback((zoom: number) => {
    setZoomLevel(Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoom)));
  }, []);

  const handleFitToWidth = useCallback(() => {
    if (!scrollContainerRef.current) return;
    const containerWidth = scrollContainerRef.current.clientWidth - 32; // padding
    const fitZoom = Math.round((containerWidth / BASE_PAGE_WIDTH) * 100);
    setZoomLevel(Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, fitZoom)));
  }, []);

  const handleFitToPage = useCallback(() => {
    setZoomLevel(100);
  }, []);

  // ── Highlight click handlers ───────────────────────────────────────
  const handleHighlightClick = useCallback(
    (claim: Claim, rect: ClaimHighlightData["rects"][0]) => {
      setTooltipClaim(claim);
      setTooltipAnchor(rect);
      onClaimClick(claim);
    },
    [onClaimClick],
  );

  const handleTooltipClose = useCallback(() => {
    setTooltipClaim(null);
    setTooltipAnchor(null);
  }, []);

  const handleGoToClaim = useCallback(
    (claim: Claim) => {
      onClaimClick(claim);
      handleTooltipClose();
    },
    [onClaimClick, handleTooltipClose],
  );

  // ── Page ref callback ──────────────────────────────────────────────
  const setPageRef = useCallback(
    (pageNum: number) => (el: HTMLDivElement | null) => {
      if (el) {
        pageRefs.current.set(pageNum, el);
      } else {
        pageRefs.current.delete(pageNum);
      }
    },
    [],
  );

  // ── Text layer render callback — triggers highlight computation ────
  const handleTextLayerRendered = useCallback(
    (pageNum: number) => () => {
      // Pass the page wrapper (stable ref) to computeHighlights.
      // The hook will re-query the text layer fresh to avoid stale
      // DOM references caused by React re-renders.
      const pageWrapper = pageRefs.current.get(pageNum);
      if (!pageWrapper) return;
      computeHighlights(pageNum, pageWrapper);
    },
    [computeHighlights],
  );

  // ── Computed values ────────────────────────────────────────────────
  const pageWidth = Math.round(BASE_PAGE_WIDTH * (zoomLevel / 100));

  // ── Error state ────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="pdf-viewer pdf-viewer--error">
        <div className="pdf-viewer__error-content">
          <svg
            className="pdf-viewer__error-icon"
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <p className="pdf-viewer__error-message">{error}</p>
          <button
            className="pdf-viewer__retry-button"
            onClick={() => {
              setError(null);
              setIsLoading(true);
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // ── Render ─────────────────────────────────────────────────────────
  return (
    <div className="pdf-viewer" ref={containerRef}>
      <PDFToolbar
        currentPage={currentPage}
        totalPages={totalPages}
        zoomLevel={zoomLevel}
        onPageChange={goToPage}
        onZoomChange={handleZoomChange}
        onFitToWidth={handleFitToWidth}
        onFitToPage={handleFitToPage}
      />

      <div className="pdf-viewer__scroll-container" ref={scrollContainerRef}>
        {isLoading && (
          <div className="pdf-viewer__loading">
            <div className="pdf-viewer__loading-spinner" />
            <p>Loading PDF...</p>
          </div>
        )}

        <Document
          file={pdfUrl}
          onLoadSuccess={handleDocumentLoadSuccess}
          onLoadError={handleDocumentLoadError}
          loading={null}
        >
          {Array.from({ length: totalPages }, (_, i) => {
            const pageNum = i + 1;
            const pageHighlights = getHighlightsForPage(pageNum);

            return (
              <div
                key={pageNum}
                ref={setPageRef(pageNum)}
                className="pdf-viewer__page-wrapper"
                data-page-number={pageNum}
              >
                <Page
                  pageNumber={pageNum}
                  width={pageWidth}
                  renderTextLayer={true}
                  renderAnnotationLayer={true}
                  onRenderTextLayerSuccess={handleTextLayerRendered(pageNum)}
                />

                {/* Highlights overlay for this page */}
                {pageHighlights.length > 0 && (
                  <div className="pdf-viewer__page-highlights">
                    {pageHighlights.map((highlight) => (
                      <ClaimHighlight
                        key={highlight.claim.id}
                        claimHighlight={highlight}
                        isActive={activeClaim?.id === highlight.claim.id}
                        isPulsing={pulsingClaimId === highlight.claim.id}
                        onClick={(claim) => {
                          const firstRect = highlight.rects[0];
                          if (firstRect) {
                            handleHighlightClick(claim, firstRect);
                          }
                        }}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </Document>
      </div>

      {/* Tooltip for clicked highlight */}
      {tooltipClaim && tooltipAnchor && (
        <HighlightTooltip
          claim={tooltipClaim}
          anchorRect={tooltipAnchor}
          onClose={handleTooltipClose}
          onGoToClaim={handleGoToClaim}
          containerRef={containerRef}
        />
      )}
    </div>
  );
}
