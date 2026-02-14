/**
 * Types for PDF Viewer components.
 * Implements FRD 4 Section 5 (Highlight Position Computation).
 */

import type { Claim } from "@/types/claim";

/**
 * Represents a highlight rectangle positioned as percentages of page dimensions.
 * Using percentages ensures highlights scale correctly at any zoom level.
 */
export interface HighlightRect {
  /** Top position as percentage of page height (0-100) */
  top: number;
  /** Left position as percentage of page width (0-100) */
  left: number;
  /** Width as percentage of page width (0-100) */
  width: number;
  /** Height as percentage of page height (0-100) */
  height: number;
  /** 1-indexed page number */
  pageNumber: number;
}

/**
 * Data structure for a claim highlight, including computed positions.
 */
export interface ClaimHighlightData {
  /** The claim this highlight represents */
  claim: Claim;
  /** One rect per line of highlighted text */
  rects: HighlightRect[];
  /** Whether the claim text was successfully matched in the PDF */
  matched: boolean;
}

/**
 * State for highlight computation, keyed by page number.
 */
export interface HighlightCache {
  [pageNumber: number]: ClaimHighlightData[];
}

/**
 * Props for the PDFViewer component.
 */
export interface PDFViewerProps {
  /** URL to fetch the PDF from */
  pdfUrl: string;
  /** List of claims to highlight */
  claims: Claim[];
  /** Currently active/selected claim */
  activeClaim: Claim | null;
  /** Callback when a claim highlight is clicked */
  onClaimClick: (claim: Claim) => void;
  /** Callback when the current page changes */
  onPageChange: (pageNumber: number) => void;
  /** Current page number (1-indexed) */
  currentPage: number;
  /** Callback to navigate to a specific page */
  goToPage?: (page: number) => void;
}

/**
 * Props for the PDFToolbar component.
 */
export interface PDFToolbarProps {
  currentPage: number;
  totalPages: number;
  zoomLevel: number;
  onPageChange: (page: number) => void;
  onZoomChange: (zoom: number) => void;
  onFitToWidth: () => void;
  onFitToPage: () => void;
}

/**
 * Props for the ClaimHighlight component.
 */
export interface ClaimHighlightProps {
  /** Highlight data including claim and positions */
  claimHighlight: ClaimHighlightData;
  /** Whether this highlight is currently active/selected */
  isActive: boolean;
  /** Whether this highlight should show pulse animation */
  isPulsing?: boolean;
  /** Callback when the highlight is clicked */
  onClick: (claim: Claim) => void;
}

/**
 * Props for the HighlightTooltip component.
 */
export interface HighlightTooltipProps {
  /** The claim to display in the tooltip */
  claim: Claim;
  /** The anchor rect for positioning the tooltip */
  anchorRect: HighlightRect;
  /** Callback to close the tooltip */
  onClose: () => void;
  /** Callback to navigate to the claim in the claims list */
  onGoToClaim: (claim: Claim) => void;
  /** Bounding container for positioning constraints */
  containerRef?: React.RefObject<HTMLDivElement | null>;
}
