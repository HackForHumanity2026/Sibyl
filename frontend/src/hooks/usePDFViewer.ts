/**
 * usePDFViewer - Hook for managing PDF viewer state.
 * Implements FRD 4 Section 5.2.
 *
 * This hook manages the external state for the PDF viewer,
 * including the current page and zoom level.
 */

import { useState, useCallback, useMemo } from "react";
import { getPDFUrl } from "@/services/api";

export interface UsePDFViewerState {
  currentPage: number;
  zoomLevel: number;
  isLoading: boolean;
  error: string | null;
}

export interface UsePDFViewerReturn extends UsePDFViewerState {
  pdfUrl: string | null;
  goToPage: (page: number) => void;
  nextPage: () => void;
  prevPage: () => void;
  setZoomLevel: (zoom: number) => void;
  fitToWidth: () => void;
  fitToPage: () => void;
  setCurrentPage: (page: number) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

/**
 * Hook for managing PDF viewer state.
 *
 * @param reportId - The report ID to fetch the PDF for
 * @param totalPages - Total number of pages (used for bounds checking)
 */
export function usePDFViewer(
  reportId: string | undefined,
  totalPages: number = 1
): UsePDFViewerReturn {
  const [currentPage, setCurrentPage] = useState(1);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Generate PDF URL
  const pdfUrl = useMemo(() => {
    if (!reportId) return null;
    return getPDFUrl(reportId);
  }, [reportId]);

  // Navigation functions
  const goToPage = useCallback(
    (page: number) => {
      if (page >= 1 && page <= totalPages) {
        setCurrentPage(page);
      }
    },
    [totalPages]
  );

  const nextPage = useCallback(() => {
    if (currentPage < totalPages) {
      setCurrentPage((prev) => prev + 1);
    }
  }, [currentPage, totalPages]);

  const prevPage = useCallback(() => {
    if (currentPage > 1) {
      setCurrentPage((prev) => prev - 1);
    }
  }, [currentPage]);

  // Zoom functions
  const fitToWidth = useCallback(() => {
    // FIT_WIDTH is typically represented as a special zoom value
    // The actual implementation depends on the PDF viewer library
    setZoomLevel(100); // Reset to 100% as approximation
  }, []);

  const fitToPage = useCallback(() => {
    // FIT_PAGE is typically represented as a special zoom value
    setZoomLevel(100); // Reset to 100% as approximation
  }, []);

  return {
    pdfUrl,
    currentPage,
    zoomLevel,
    isLoading,
    error,
    goToPage,
    nextPage,
    prevPage,
    setZoomLevel,
    fitToWidth,
    fitToPage,
    setCurrentPage,
    setIsLoading,
    setError,
  };
}
