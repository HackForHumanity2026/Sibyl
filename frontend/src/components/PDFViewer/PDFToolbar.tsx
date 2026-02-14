/**
 * PDFToolbar - Navigation and zoom controls for the PDF viewer.
 * Implements FRD 4 Section 4.2.
 */

import { useState, useCallback, type ChangeEvent, type KeyboardEvent } from "react";
import type { PDFToolbarProps } from "./types";

export function PDFToolbar({
  currentPage,
  totalPages,
  zoomLevel,
  onPageChange,
  onZoomChange,
  onFitToWidth,
  onFitToPage,
}: PDFToolbarProps) {
  const [pageInput, setPageInput] = useState(String(currentPage));

  // Sync page input when currentPage changes externally
  if (pageInput !== String(currentPage) && document.activeElement?.tagName !== "INPUT") {
    setPageInput(String(currentPage));
  }

  const handlePageInputChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    setPageInput(e.target.value);
  }, []);

  const handlePageInputKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        const page = parseInt(pageInput, 10);
        if (!isNaN(page) && page >= 1 && page <= totalPages) {
          onPageChange(page);
        } else {
          setPageInput(String(currentPage));
        }
      }
    },
    [pageInput, totalPages, currentPage, onPageChange]
  );

  const handlePageInputBlur = useCallback(() => {
    const page = parseInt(pageInput, 10);
    if (!isNaN(page) && page >= 1 && page <= totalPages) {
      onPageChange(page);
    } else {
      setPageInput(String(currentPage));
    }
  }, [pageInput, totalPages, currentPage, onPageChange]);

  const handlePrevPage = useCallback(() => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  }, [currentPage, onPageChange]);

  const handleNextPage = useCallback(() => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  }, [currentPage, totalPages, onPageChange]);

  const handleZoomIn = useCallback(() => {
    onZoomChange(Math.min(zoomLevel + 25, 300));
  }, [zoomLevel, onZoomChange]);

  const handleZoomOut = useCallback(() => {
    onZoomChange(Math.max(zoomLevel - 25, 25));
  }, [zoomLevel, onZoomChange]);

  return (
    <div className="pdf-toolbar">
      {/* Page Navigation */}
      <div className="pdf-toolbar__nav">
        <button
          className="pdf-toolbar__button"
          onClick={handlePrevPage}
          disabled={currentPage <= 1}
          aria-label="Previous page"
          title="Previous page"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>

        <div className="pdf-toolbar__page-info">
          <input
            type="text"
            className="pdf-toolbar__page-input"
            value={pageInput}
            onChange={handlePageInputChange}
            onKeyDown={handlePageInputKeyDown}
            onBlur={handlePageInputBlur}
            aria-label="Current page"
          />
          <span className="pdf-toolbar__page-total">/ {totalPages}</span>
        </div>

        <button
          className="pdf-toolbar__button"
          onClick={handleNextPage}
          disabled={currentPage >= totalPages}
          aria-label="Next page"
          title="Next page"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>

      {/* Zoom Controls */}
      <div className="pdf-toolbar__zoom">
        <button
          className="pdf-toolbar__button"
          onClick={handleZoomOut}
          disabled={zoomLevel <= 25}
          aria-label="Zoom out"
          title="Zoom out"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="8" y1="11" x2="14" y2="11" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </button>

        <span className="pdf-toolbar__zoom-level">{Math.round(zoomLevel)}%</span>

        <button
          className="pdf-toolbar__button"
          onClick={handleZoomIn}
          disabled={zoomLevel >= 300}
          aria-label="Zoom in"
          title="Zoom in"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="11" y1="8" x2="11" y2="14" />
            <line x1="8" y1="11" x2="14" y2="11" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </button>

        <div className="pdf-toolbar__separator" />

        <button
          className="pdf-toolbar__button"
          onClick={onFitToWidth}
          aria-label="Fit to width"
          title="Fit to width"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 3H3v18h18V3z" />
            <path d="M9 3v18" />
            <path d="M15 3v18" />
          </svg>
        </button>

        <button
          className="pdf-toolbar__button"
          onClick={onFitToPage}
          aria-label="Fit to page"
          title="Fit to page"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <path d="M9 9h6v6H9z" />
          </svg>
        </button>
      </div>
    </div>
  );
}
