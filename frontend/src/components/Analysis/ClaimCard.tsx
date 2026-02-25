/**
 * ClaimCard - Displays a single claim in the Analysis ClaimsPanel.
 * Implements FRD 3 Section 7.3, enhanced in FRD 4.
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

const TYPE_LABELS: Record<ClaimType, string> = {
  geographic: "Geographic",
  quantitative: "Quantitative",
  legal_governance: "Legal / Gov",
  strategic: "Strategic",
  environmental: "Environmental",
};

const PRIORITY_STYLES: Record<ClaimPriority, string> = {
  high: "bg-rose-50 text-rose-700 border-rose-100",
  medium: "bg-amber-50 text-amber-700 border-amber-100",
  low: "bg-[#f5ecdb] text-[#6b5344] border-slate-100",
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
          "relative bg-[#fff6e9] border rounded-xl overflow-hidden cursor-pointer transition-all duration-150",
          isActive
            ? "border-slate-400 shadow-md ring-1 ring-slate-300"
            : "border-slate-200 hover:border-slate-300 hover:shadow-sm"
        )}
      >
        {/* Type colour bar */}
        <div className={cn("absolute left-0 top-0 bottom-0 w-1", TYPE_BAR_COLORS[claim.claim_type])} />

        <div className="pl-4 pr-3 py-3">
          {/* Header row */}
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="text-xs font-semibold text-[#6b5344]">
              {TYPE_LABELS[claim.claim_type]}
            </span>
            <span className={cn(
              "inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border",
              PRIORITY_STYLES[claim.priority]
            )}>
              {claim.priority}
            </span>

            {onGoToPage ? (
              <button
                onClick={handlePageClick}
                className="ml-auto text-xs text-[#8b7355] hover:text-slate-700 transition-colors font-mono"
              >
                p.{claim.source_page} →
              </button>
            ) : (
              <span className="ml-auto text-xs text-[#8b7355] font-mono">p.{claim.source_page}</span>
            )}
          </div>

          {/* Claim text */}
          <p className="text-sm text-slate-700 leading-relaxed">{claim.claim_text}</p>

          {/* IFRS tags */}
          {claim.ifrs_paragraphs.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {claim.ifrs_paragraphs.map((mapping, i) => (
                <span
                  key={i}
                  title={mapping.relevance}
                  className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-mono bg-[#f5ecdb] text-[#8b7355] border border-slate-100"
                >
                  {mapping.paragraph_id}
                </span>
              ))}
            </div>
          )}

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
                  size={12}
                  className={cn("transition-transform duration-150", isExpanded && "rotate-180")}
                />
              </button>
              {isExpanded && (
                <p className="mt-2 text-xs text-[#6b5344] italic leading-relaxed border-l-2 border-slate-100 pl-2">
                  {claim.agent_reasoning}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }
);
