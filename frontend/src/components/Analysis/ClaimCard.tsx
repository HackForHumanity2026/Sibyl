/**
 * ClaimCard - Displays a single claim with type-colored border and collapsible reasoning.
 * Implements FRD 3 Section 7.3.
 */

import { useState } from "react";
import type { Claim, ClaimType, ClaimPriority } from "@/types/claim";

interface ClaimCardProps {
  claim: Claim;
  onClick?: () => void;
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

export function ClaimCard({ claim, onClick }: ClaimCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const toggleExpanded = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  return (
    <div
      className={`claim-card claim-card--${claim.claim_type}`}
      onClick={onClick}
    >
      <div className="claim-card__header">
        <span className={`claim-card__type-badge claim-card__type-badge--${claim.claim_type}`}>
          {CLAIM_TYPE_LABELS[claim.claim_type]}
        </span>
        <span className={`claim-card__priority-badge claim-card__priority-badge--${claim.priority}`}>
          {PRIORITY_LABELS[claim.priority]}
        </span>
        <span className="claim-card__page">Page {claim.source_page}</span>
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
}
