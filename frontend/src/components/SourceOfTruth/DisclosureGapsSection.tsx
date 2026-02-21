/**
 * DisclosureGapsSection - Collapsible section displaying disclosure gaps.
 * Implements FRD 13 Section 9.2.
 */

import { useState } from "react";
import type { DisclosureGapResponse } from "@/types/sourceOfTruth";
import { GapCard } from "./GapCard";

interface DisclosureGapsSectionProps {
  gaps: DisclosureGapResponse[];
  pillar?: string;
}

export function DisclosureGapsSection({
  gaps,
}: DisclosureGapsSectionProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (gaps.length === 0) {
    return null;
  }

  const fullyUnaddressed = gaps.filter(
    (g) => g.gap_type === "fully_unaddressed"
  ).length;
  const partiallyAddressed = gaps.filter(
    (g) => g.gap_type === "partially_addressed"
  ).length;

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-muted/30 hover:bg-muted/50 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-foreground">
            Disclosure Gaps
          </span>
          <span className="text-xs text-muted-foreground">
            ({gaps.length} gap{gaps.length !== 1 ? "s" : ""})
          </span>
        </div>
        <div className="flex items-center gap-3">
          {fullyUnaddressed > 0 && (
            <span className="text-xs px-2 py-0.5 rounded bg-gray-500/20 text-gray-400">
              {fullyUnaddressed} unaddressed
            </span>
          )}
          {partiallyAddressed > 0 && (
            <span className="text-xs px-2 py-0.5 rounded bg-orange-500/20 text-orange-400">
              {partiallyAddressed} partial
            </span>
          )}
          <span
            className={`text-muted-foreground transition-transform ${
              isExpanded ? "rotate-180" : ""
            }`}
          >
            ▼
          </span>
        </div>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="p-4 space-y-3">
          {gaps.map((gap) => (
            <GapCard key={gap.gap_id} gap={gap} />
          ))}
        </div>
      )}
    </div>
  );
}
