/**
 * ClaimCard - Displays a single claim with type-colored border and collapsible reasoning.
 * Implements FRD 3 Section 7.3, enhanced in FRD 4 for cross-panel interactions.
 */

import { useState, forwardRef, useCallback } from "react";
import type { Claim, ClaimType, ClaimPriority } from "@/types/claim";

interface ClaimCardProps {
  claim: Claim;
  onClick?: () => void;
  /** Callback when page link is clicked (navigates to claim in PDF) */
  onGoToPage?: (claim: Claim) => void;
  /** Whether this claim is currently active/selected */
  isActive?: boolean;
}

const CLAIM_TYPE_LABELS: Record<ClaimType, string> = {
  geographic: "Geographic",
  quantitative: "Quantitative",
  legal_governance: "Legal/Governance",
  strategic: "Strategic",
  environmental: "Environmental",
};

const PRIORITY_LABELS: Record<ClaimPriority, string> = {
  high: "High",
  medium: "Medium",
  low: "Low",
};

export const ClaimCard = forwardRef<HTMLDivElement, ClaimCardProps>(
  function ClaimCard({ claim, onClick, onGoToPage, isActive = false }, ref) {
  const [isExpanded, setIsExpanded] = useState(false);

  const toggleExpanded = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded((prev) => !prev);
  }, []);

  const handlePageClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (onGoToPage) {
        onGoToPage(claim);
      }
    },
    [onGoToPage, claim]
  );

  const cardClasses = [
    "claim-card",
    `claim-card--${claim.claim_type}`,
    isActive ? "claim-card--active" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      ref={ref}
      className={cardClasses}
      onClick={onClick}
    >
      <div className="claim-card__header">
        <span className={`claim-card__type-badge claim-card__type-badge--${claim.claim_type}`}>
          {CLAIM_TYPE_LABELS[claim.claim_type]}
        </span>
        <span className={`claim-card__priority-badge claim-card__priority-badge--${claim.priority}`}>
          {PRIORITY_LABELS[claim.priority]}
        </span>
        {onGoToPage ? (
          <button
            className="claim-card__page claim-card__page--link"
            onClick={handlePageClick}
            title="Go to page in PDF viewer"
          >
            Page {claim.source_page} →
          </button>
        ) : (
          <span className="claim-card__page">Page {claim.source_page}</span>
        )}
      </div>

      <div className="claim-card__content">
        <p className="claim-card__text">{claim.claim_text}</p>
      </div>

      {claim.ifrs_paragraphs.length > 0 && (
        <div className="claim-card__ifrs">
          {claim.ifrs_paragraphs.map((mapping, index) => (
            <span key={index} className="claim-card__ifrs-tag" title={mapping.relevance}>
              {mapping.paragraph_id}
            </span>
          ))}
        </div>
      )}

      {claim.agent_reasoning && (
        <div className="claim-card__reasoning-section">
          <button
            className="claim-card__reasoning-toggle"
            onClick={toggleExpanded}
            aria-expanded={isExpanded}
          >
            {isExpanded ? "Hide Reasoning" : "Show Reasoning"}
            <span className={`claim-card__arrow ${isExpanded ? "claim-card__arrow--up" : ""}`}>
              ▼
            </span>
          </button>
          {isExpanded && (
            <div className="claim-card__reasoning">
              <p>{claim.agent_reasoning}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
});
