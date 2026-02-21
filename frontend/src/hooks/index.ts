/**
 * Custom React hooks.
 */

export { useUpload } from "./useUpload";
export type { UploadState, UseUploadReturn } from "./useUpload";

export { useAnalysis } from "./useAnalysis";
export type { AnalysisState, UseAnalysisReturn } from "./useAnalysis";

export { usePDFViewer } from "./usePDFViewer";
export type { UsePDFViewerState, UsePDFViewerReturn } from "./usePDFViewer";

export { useClaimHighlights } from "./useClaimHighlights";
export type { UseClaimHighlightsReturn } from "./useClaimHighlights";

export { useSSE } from "./useSSE";
export type { UseSSEReturn } from "./useSSE";

export { useDashboard } from "./useDashboard";
export type { UseDashboardReturn } from "./useDashboard";

// TODO: Implement hooks in subsequent FRDs:
// - useChat (FRD 14) - Chatbot conversation state
