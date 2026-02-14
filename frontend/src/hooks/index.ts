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

// TODO: Implement hooks in subsequent FRDs:
// - useSSE (FRD 5) - SSE connection for agent streaming
// - useChat (FRD 14) - Chatbot conversation state
