/**
 * DisclosureGapsSection - Collapsible section displaying disclosure gaps.
 * Implements FRD 13 Section 9.2.
 */

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import type { DisclosureGapResponse } from "@/types/sourceOfTruth";
import { GapCard } from "./GapCard";

interface DisclosureGapsSectionProps {
  gaps: DisclosureGapResponse[];
  pillar?: string;
}

export function DisclosureGapsSection({ gaps }: DisclosureGapsSectionProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (gaps.length === 0) return null;

  const fullyUnaddressed = gaps.filter((g) => g.gap_type === "fully_unaddressed").length;
  const partiallyAddressed = gaps.filter((g) => g.gap_type === "partially_addressed").length;

  return (
    <div>
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between py-3 hover:bg-[#f5ecdb] transition-colors text-left px-1 -mx-1"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-[#4a3c2e]">Disclosure Gaps</span>
          <span className="text-xs text-[#8b7355]">
            {gaps.length} gap{gaps.length !== 1 ? "s" : ""}
          </span>
          {fullyUnaddressed > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-rose-50 text-rose-600 font-medium">
              {fullyUnaddressed} unaddressed
            </span>
          )}
          {partiallyAddressed > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-600">
              {partiallyAddressed} partial
            </span>
          )}
        </div>
        <ChevronDown
          size={14}
          className={`text-[#8b7355] transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`}
        />
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="divide-y divide-[#e0d4bf] border-y border-[#e0d4bf]">
          {gaps.map((gap) => (
            <GapCard key={gap.gap_id} gap={gap} />
          ))}
        </div>
      )}
    </div>
  );
}
