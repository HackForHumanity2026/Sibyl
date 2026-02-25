/**
 * ClaimCard - Displays a single claim in the Analysis ClaimsPanel.
 * Implements FRD 3 Section 7.3, enhanced in FRD 4.
 * Design: flat divider row, no card borders/backgrounds.
 */

import { useState, forwardRef, useCallback } from "react";
import { ChevronDown } from "lucide-react";
import type { Claim, ClaimType, ClaimPriority } from "@/types/claim";
import { cn } from "@/lib/utils";

interface ClaimCardProps {
  claim: Claim;
  onClick?: () => void;
  onGoToPage?: (claim: Claim) => void;
  isActive?: boolean;
}

const PRIORITY_DOT: Record<ClaimPriority, string> = {
  high: "bg-rose-500",
  medium: "bg-amber-400",
  low: "bg-[#c8a97a]",
};

const TYPE_BAR_COLORS: Record<ClaimType, string> = {
  geographic: "bg-blue-400",
  quantitative: "bg-violet-400",
  legal_governance: "bg-indigo-400",
  strategic: "bg-cyan-400",
  environmental: "bg-emerald-400",
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
        onGoToPage?.(claim);
      },
      [onGoToPage, claim]
    );

    return (
      <div
        ref={ref}
        onClick={onClick}
        className={cn(
          "relative cursor-pointer transition-colors duration-100 py-3 px-4",
          "hover:bg-[#f5ecdb]",
          isActive && "bg-[#f5ecdb]"
        )}
      >
        {/* Active indicator — thin left bar */}
        {isActive && (
          <div className={cn("absolute left-0 top-2 bottom-2 w-0.5 rounded-r", TYPE_BAR_COLORS[claim.claim_type])} />
        )}

        {/* Meta row: priority dot · page link · IFRS tags */}
        <div className="flex items-center gap-2 mb-1.5">
          <span
            title={`Priority: ${claim.priority}`}
            className={cn("w-2 h-2 rounded-full shrink-0", PRIORITY_DOT[claim.priority])}
          />

          <div className="flex flex-wrap gap-1 flex-1">
            {claim.ifrs_paragraphs.map((mapping, i) => (
              <span
                key={i}
                title={mapping.relevance}
                className="text-[10px] font-mono text-[#8b7355]"
              >
                {mapping.paragraph_id}
              </span>
            ))}
          </div>

          {onGoToPage ? (
            <button
              onClick={handlePageClick}
              className="text-xs text-[#8b7355] hover:text-[#4a3c2e] transition-colors font-mono shrink-0"
            >
              p.{claim.source_page} →
            </button>
          ) : (
            <span className="text-xs text-[#8b7355] font-mono shrink-0">
              p.{claim.source_page}
            </span>
          )}
        </div>

        {/* Claim text */}
        <p className="text-sm text-[#4a3c2e] leading-relaxed">{claim.claim_text}</p>

        {/* Reasoning toggle */}
        {claim.agent_reasoning && (
          <div className="mt-2">
            <button
              onClick={toggleExpanded}
              className="flex items-center gap-1 text-xs text-[#8b7355] hover:text-[#4a3c2e] transition-colors"
              aria-expanded={isExpanded}
            >
              <span>{isExpanded ? "Hide reasoning" : "Show reasoning"}</span>
              <ChevronDown
                size={11}
                className={cn("transition-transform duration-150", isExpanded && "rotate-180")}
              />
            </button>
            {isExpanded && (
              <p className="mt-1.5 text-xs text-[#6b5344] italic leading-relaxed border-l-2 border-[#e0d4bf] pl-2.5">
                {claim.agent_reasoning}
              </p>
            )}
          </div>
        )}
      </div>
    );
  }
);
