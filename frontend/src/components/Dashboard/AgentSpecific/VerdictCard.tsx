/**
 * VerdictCard - Judge Agent verdict display.
 * Shows color-coded verdict badges with claim text and reasoning.
 */

import type { Verdict } from "@/types/dashboard";

interface VerdictCardProps {
  verdicts: Verdict[];
}

const VERDICT_CONFIG: Record<
  Verdict["verdict"],
  { label: string; className: string }
> = {
  verified: { label: "Verified", className: "verdict-card__badge--verified" },
  unverified: {
    label: "Unverified",
    className: "verdict-card__badge--unverified",
  },
  contradicted: {
    label: "Contradicted",
    className: "verdict-card__badge--contradicted",
  },
  insufficient_evidence: {
    label: "Insufficient Evidence",
    className: "verdict-card__badge--insufficient",
  },
};

function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + "...";
}

export function VerdictCard({ verdicts }: VerdictCardProps) {
  if (verdicts.length === 0) {
    return (
      <div className="verdict-card verdict-card--empty">
        <div className="verdict-card__header">Verdicts</div>
        <span className="verdict-card__placeholder">No verdicts issued yet</span>
      </div>
    );
  }

  const verdictCounts = verdicts.reduce(
    (acc, v) => {
      acc[v.verdict] = (acc[v.verdict] || 0) + 1;
      return acc;
    },
    {} as Record<Verdict["verdict"], number>
  );

  return (
    <div className="verdict-card">
      <div className="verdict-card__header">
        Verdicts ({verdicts.length})
        <div className="verdict-card__summary">
          {verdictCounts.verified && (
            <span className="verdict-card__count verdict-card__count--verified">
              {verdictCounts.verified} verified
            </span>
          )}
          {verdictCounts.contradicted && (
            <span className="verdict-card__count verdict-card__count--contradicted">
              {verdictCounts.contradicted} contradicted
            </span>
          )}
        </div>
      </div>
      <div className="verdict-card__list">
        {verdicts.map((verdict) => {
          const config = VERDICT_CONFIG[verdict.verdict];
          return (
            <div key={verdict.claimId} className="verdict-card__item">
              <div className="verdict-card__item-header">
                <span className={`verdict-card__badge ${config.className}`}>
                  {config.label}
                </span>
                {verdict.cycleCount > 1 && (
                  <span className="verdict-card__cycle">
                    Cycle {verdict.cycleCount}
                  </span>
                )}
              </div>
              <div className="verdict-card__claim">
                {truncateText(verdict.claimText, 100)}
              </div>
              <div className="verdict-card__reasoning">
                {truncateText(verdict.reasoning, 150)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
