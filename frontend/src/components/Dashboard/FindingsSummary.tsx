/**
 * FindingsSummary - Summary of agent findings with recent entries.
 */

import type { AgentFinding } from "@/types/agent";

interface FindingsSummaryProps {
  findings: AgentFinding[];
  maxDisplay?: number;
}

export function FindingsSummary({
  findings,
  maxDisplay = 5,
}: FindingsSummaryProps) {
  const recentFindings = findings.slice(-maxDisplay);

  if (findings.length === 0) {
    return (
      <div className="findings-summary findings-summary--empty">
        <span className="findings-summary__placeholder">No findings yet</span>
      </div>
    );
  }

  return (
    <div className="findings-summary">
      <div className="findings-summary__header">
        Findings ({findings.length})
      </div>
      <div className="findings-summary__list">
        {recentFindings.map((finding) => (
          <div key={finding.id} className="findings-summary__item">
            <div className="findings-summary__item-header">
              <span
                className={`findings-summary__support-badge findings-summary__support-badge--${
                  finding.supportsClaim === true
                    ? "supports"
                    : finding.supportsClaim === false
                    ? "contradicts"
                    : "neutral"
                }`}
              >
                {finding.supportsClaim === true
                  ? "✓"
                  : finding.supportsClaim === false
                  ? "✗"
                  : "?"}
              </span>
              <span className="findings-summary__type">{finding.evidenceType}</span>
              {finding.confidence && (
                <span className={`findings-summary__confidence findings-summary__confidence--${finding.confidence}`}>
                  {finding.confidence}
                </span>
              )}
            </div>
            <div className="findings-summary__summary">{finding.summary}</div>
          </div>
        ))}
      </div>
      {findings.length > maxDisplay && (
        <div className="findings-summary__more">
          +{findings.length - maxDisplay} more findings
        </div>
      )}
    </div>
  );
}
