/**
 * ClaimsPanel - Right panel wrapper for claims list with scroll-to functionality.
 * Implements FRD 4 Section 7 (Cross-Panel Interactions).
 */

import { useEffect, useRef, useCallback } from "react";
import type { Claim, ClaimType, ClaimPriority } from "@/types/claim";
import { ClaimCard } from "./ClaimCard";
import { ClaimsFilter } from "./ClaimsFilter";

interface ClaimsPanelProps {
  claims: Claim[];
  activeClaim: Claim | null;
  onClaimClick: (claim: Claim) => void;
  onGoToPage: (claim: Claim) => void;
  typeFilter: ClaimType | null;
  priorityFilter: ClaimPriority | null;
  onTypeFilterChange: (type: ClaimType | null) => void;
  onPriorityFilterChange: (priority: ClaimPriority | null) => void;
  claimsByType: Record<string, number>;
  claimsByPriority: Record<string, number>;
  isLoading?: boolean;
}

export function ClaimsPanel({
  claims,
  activeClaim,
  onClaimClick,
  onGoToPage,
  typeFilter,
  priorityFilter,
  onTypeFilterChange,
  onPriorityFilterChange,
  claimsByType,
  claimsByPriority,
  isLoading = false,
}: ClaimsPanelProps) {
  const claimRefsMap = useRef<Map<string, HTMLDivElement>>(new Map());
  const containerRef = useRef<HTMLDivElement>(null);

  // Scroll to active claim when it changes
  useEffect(() => {
    if (activeClaim) {
      const claimElement = claimRefsMap.current.get(activeClaim.id);
      if (claimElement && containerRef.current) {
        // Calculate if the element is in view
        const containerRect = containerRef.current.getBoundingClientRect();
        const elementRect = claimElement.getBoundingClientRect();

        const isInView =
          elementRect.top >= containerRect.top &&
          elementRect.bottom <= containerRect.bottom;

        if (!isInView) {
          claimElement.scrollIntoView({
            behavior: "smooth",
            block: "center",
          });
        }

        // Add flash animation
        claimElement.classList.add("claim-card--flash");
        const timer = setTimeout(() => {
          claimElement.classList.remove("claim-card--flash");
        }, 600);

        return () => clearTimeout(timer);
      }
    }
  }, [activeClaim]);

  const setClaimRef = useCallback(
    (claimId: string) => (el: HTMLDivElement | null) => {
      if (el) {
        claimRefsMap.current.set(claimId, el);
      } else {
        claimRefsMap.current.delete(claimId);
      }
    },
    []
  );

  const handleClaimClick = useCallback(
    (claim: Claim) => {
      onClaimClick(claim);
    },
    [onClaimClick]
  );

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-32 gap-2 text-[#8b7355]">
        <div className="w-5 h-5 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin" />
        <p className="text-xs">Loading claims…</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden bg-[#fff6e9]" ref={containerRef}>
      <ClaimsFilter
        typeFilter={typeFilter}
        priorityFilter={priorityFilter}
        onTypeChange={onTypeFilterChange}
        onPriorityChange={onPriorityFilterChange}
        claimsByType={claimsByType}
        claimsByPriority={claimsByPriority}
      />

      <div className="px-3 py-2 text-xs text-[#8b7355] font-medium border-b border-slate-100">
        {claims.length} claim{claims.length !== 1 ? "s" : ""}
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
        {claims.length === 0 ? (
          <div className="flex items-center justify-center py-8 text-xs text-[#8b7355]">
            No claims match the current filters.
          </div>
        ) : (
          claims.map((claim) => (
            <ClaimCard
              key={claim.id}
              ref={setClaimRef(claim.id)}
              claim={claim}
              onClick={() => handleClaimClick(claim)}
              onGoToPage={onGoToPage}
              isActive={activeClaim?.id === claim.id}
            />
          ))
        )}
      </div>
    </div>
  );
}
