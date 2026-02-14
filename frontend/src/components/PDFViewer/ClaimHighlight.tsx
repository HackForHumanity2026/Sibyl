/**
 * ClaimHighlight - Renders highlight overlays on PDF pages.
 * Implements FRD 4 Section 4.3.
 */

import { useCallback } from "react";
import type { ClaimHighlightProps } from "./types";
import type { ClaimType } from "@/types/claim";

/**
 * Get CSS class for claim type color.
 */
function getTypeColorClass(claimType: ClaimType): string {
  switch (claimType) {
    case "geographic":
      return "claim-highlight--geographic";
    case "quantitative":
      return "claim-highlight--quantitative";
    case "legal_governance":
      return "claim-highlight--legal";
    case "strategic":
      return "claim-highlight--strategic";
    case "environmental":
      return "claim-highlight--environmental";
    default:
      return "";
  }
}

export function ClaimHighlight({
  claimHighlight,
  isActive,
  isPulsing = false,
  onClick,
}: ClaimHighlightProps) {
  const { claim, rects, matched } = claimHighlight;

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onClick(claim);
    },
    [onClick, claim]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onClick(claim);
      }
    },
    [onClick, claim]
  );

  // Don't render if no rects or not matched (unless it's a fallback highlight)
  if (rects.length === 0) {
    return null;
  }

  const typeClass = getTypeColorClass(claim.claim_type);
  const activeClass = isActive ? "claim-highlight--active" : "";
  const pulsingClass = isPulsing ? "claim-highlight--pulse" : "";
  const unmatchedClass = !matched ? "claim-highlight--unmatched" : "";

  return (
    <>
      {rects.map((rect, index) => (
        <div
          key={`${claim.id}-${index}`}
          className={`claim-highlight ${typeClass} ${activeClass} ${pulsingClass} ${unmatchedClass}`}
          style={{
            position: "absolute",
            top: `${rect.top}%`,
            left: `${rect.left}%`,
            width: `${rect.width}%`,
            height: `${rect.height}%`,
          }}
          onClick={handleClick}
          onKeyDown={handleKeyDown}
          role="button"
          tabIndex={0}
          aria-label={`Claim highlight: ${claim.claim_text.slice(0, 50)}...`}
          title={`${claim.claim_type} claim - Click to view details`}
        />
      ))}
    </>
  );
}
