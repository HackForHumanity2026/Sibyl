/**
 * AnalysisProgress - Loading indicator and progress display during claims extraction.
 * Implements FRD 3 Section 7.3.
 */

import type { AnalysisState } from "@/hooks/useAnalysis";

interface AnalysisProgressProps {
  state: AnalysisState;
  claimsCount: number;
  error: string | null;
  onRetry: () => void;
}

export function AnalysisProgress({
  state,
  claimsCount,
  error,
  onRetry,
}: AnalysisProgressProps) {
  if (state === "error") {
    return (
      <div className="analysis-progress analysis-progress--error">
        <div className="analysis-progress__icon">
          <svg
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
        </div>
        <h3 className="analysis-progress__title">Analysis Failed</h3>
        <p className="analysis-progress__message">{error}</p>
        <button className="analysis-progress__retry" onClick={onRetry}>
          Retry Analysis
        </button>
      </div>
    );
  }

  if (state === "starting" || state === "analyzing") {
    return (
      <div className="analysis-progress analysis-progress--loading">
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
        <h3 className="analysis-progress__title">
          {state === "starting" ? "Starting Analysis..." : "Extracting Claims..."}
        </h3>
        {claimsCount > 0 && (
          <p className="analysis-progress__count">
            Found {claimsCount} claim{claimsCount !== 1 ? "s" : ""} so far
          </p>
        )}
        <p className="analysis-progress__message">
          This may take a few minutes for large documents.
        </p>
      </div>
    );
  }

  return null;
}
