/**
 * HighlightTooltip - Tooltip showing claim details on highlight click.
 * Implements FRD 4 Section 4.4.
 */

import { useState, useCallback, useEffect, useRef } from "react";
import type { HighlightTooltipProps } from "./types";
import type { ClaimType, ClaimPriority } from "@/types/claim";

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

const MAX_TEXT_LENGTH = 200;
const TOOLTIP_WIDTH = 320;
const TOOLTIP_MAX_HEIGHT = 400;

export function HighlightTooltip({
  claim,
  anchorRect,
  onClose,
  onGoToClaim,
  containerRef,
}: HighlightTooltipProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showFullText, setShowFullText] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Handle clicking outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (tooltipRef.current && !tooltipRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [onClose]);

  // Calculate position
  const getPosition = useCallback(() => {
    if (!containerRef?.current) {
      // Default position relative to anchor
      return {
        top: `${anchorRect.top}%`,
        left: `${Math.min(anchorRect.left + anchorRect.width + 2, 70)}%`,
      };
    }

    const containerRect = containerRef.current.getBoundingClientRect();
    const anchorLeft = (anchorRect.left / 100) * containerRect.width;
    const anchorTop = (anchorRect.top / 100) * containerRect.height;
    const anchorWidth = (anchorRect.width / 100) * containerRect.width;

    let left = anchorLeft + anchorWidth + 10;
    let top = anchorTop;

    // Check if tooltip would overflow right edge
    if (left + TOOLTIP_WIDTH > containerRect.width) {
      // Try left side
      left = anchorLeft - TOOLTIP_WIDTH - 10;
      if (left < 0) {
        // Place below instead
        left = Math.max(10, anchorLeft);
        top = anchorTop + 30;
      }
    }

    // Convert back to percentage
    return {
      top: `${(top / containerRect.height) * 100}%`,
      left: `${(left / containerRect.width) * 100}%`,
    };
  }, [anchorRect, containerRef]);

  const position = getPosition();
  const displayText = showFullText
    ? claim.claim_text
    : claim.claim_text.slice(0, MAX_TEXT_LENGTH);
  const hasMoreText = claim.claim_text.length > MAX_TEXT_LENGTH;

  const handleViewInList = useCallback(() => {
    onGoToClaim(claim);
  }, [onGoToClaim, claim]);

  const toggleReasoning = useCallback(() => {
    setIsExpanded((prev) => !prev);
  }, []);

  const toggleShowMore = useCallback(() => {
    setShowFullText((prev) => !prev);
  }, []);

  return (
    <div
      ref={tooltipRef}
      className="highlight-tooltip"
      style={{
        position: "absolute",
        top: position.top,
        left: position.left,
        width: TOOLTIP_WIDTH,
        maxHeight: TOOLTIP_MAX_HEIGHT,
      }}
      role="dialog"
      aria-label="Claim details"
    >
      {/* Header */}
      <div className="highlight-tooltip__header">
        <div className="highlight-tooltip__badges">
          <span className={`highlight-tooltip__type-badge highlight-tooltip__type-badge--${claim.claim_type}`}>
            {CLAIM_TYPE_LABELS[claim.claim_type]}
          </span>
          <span className={`highlight-tooltip__priority-badge highlight-tooltip__priority-badge--${claim.priority}`}>
            {PRIORITY_LABELS[claim.priority]}
          </span>
        </div>
        <button
          className="highlight-tooltip__close"
          onClick={onClose}
          aria-label="Close tooltip"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      {/* Claim Text */}
      <div className="highlight-tooltip__content">
        <p className="highlight-tooltip__text">
          {displayText}
          {hasMoreText && !showFullText && "..."}
        </p>
        {hasMoreText && (
          <button className="highlight-tooltip__show-more" onClick={toggleShowMore}>
            {showFullText ? "Show less" : "Show more"}
          </button>
        )}
      </div>

      {/* IFRS Tags */}
      {claim.ifrs_paragraphs.length > 0 && (
        <div className="highlight-tooltip__ifrs">
          {claim.ifrs_paragraphs.map((mapping, index) => (
            <span
              key={index}
              className="highlight-tooltip__ifrs-tag"
              title={mapping.relevance}
            >
              {mapping.paragraph_id}
            </span>
          ))}
        </div>
      )}

      {/* Reasoning Section */}
      {claim.agent_reasoning && (
        <div className="highlight-tooltip__reasoning-section">
          <button
            className="highlight-tooltip__reasoning-toggle"
            onClick={toggleReasoning}
            aria-expanded={isExpanded}
          >
            Claims Agent Reasoning
            <span className={`highlight-tooltip__arrow ${isExpanded ? "highlight-tooltip__arrow--up" : ""}`}>
              ▼
            </span>
          </button>
          {isExpanded && (
            <div className="highlight-tooltip__reasoning">
              <p>{claim.agent_reasoning}</p>
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="highlight-tooltip__footer">
        <span className="highlight-tooltip__page">Page {claim.source_page}</span>
        <button className="highlight-tooltip__link" onClick={handleViewInList}>
          View in Claims List →
        </button>
      </div>
    </div>
  );
}
