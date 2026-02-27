/**
 * GapCard - Displays a disclosure gap with severity and materiality context.
 * Implements FRD 13 Section 9.3.
 */

import type { DisclosureGapResponse } from "@/types/sourceOfTruth";
import { IFRSParagraphTag } from "./IFRSParagraphTag";

interface GapCardProps {
  gap: DisclosureGapResponse;
}

const SEVERITY_CONFIG: Record<string, { label: string; className: string }> = {
  high: { label: "High", className: "bg-rose-50 text-rose-700 border-rose-100" },
  medium: { label: "Medium", className: "bg-amber-50 text-amber-700 border-amber-100" },
  low: { label: "Low", className: "bg-[#f5ecdb] text-[#6b5344] border-[#e0d4bf]" },
};

const GAP_TYPE_LABELS: Record<string, string> = {
  fully_unaddressed: "Unaddressed",
  partially_addressed: "Partial",
};

export function GapCard({ gap }: GapCardProps) {
  const severity = SEVERITY_CONFIG[gap.severity] ?? SEVERITY_CONFIG.medium;

  return (
    <div className="bg-[#fff6e9] p-4 space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <IFRSParagraphTag paragraphId={gap.paragraph_id} />
          <span className="text-xs text-[#6b5344]">
            {GAP_TYPE_LABELS[gap.gap_type] ?? gap.gap_type}
          </span>
          <span
            title={severity.label}
            className={`w-2 h-2 rounded-full shrink-0 ${
              gap.severity === "high"
                ? "bg-rose-500"
                : gap.severity === "medium"
                ? "bg-amber-400"
                : "bg-[#c8a97a]"
            }`}
          />
        </div>
        {gap.s1_counterpart && (
          <span className="text-xs text-[#8b7355] font-mono">
            S1: {gap.s1_counterpart}
          </span>
        )}
      </div>

      {/* Requirement text */}
      <p className="text-sm text-[#4a3c2e] leading-relaxed">{gap.requirement_text}</p>

      {/* Missing requirements */}
      {gap.missing_requirements.length > 0 && (
        <div className="space-y-1">
          <span className="text-xs font-medium text-[#8b7355] uppercase tracking-wide">
            Missing
          </span>
          <ul className="space-y-0.5">
            {gap.missing_requirements.map((req, i) => (
              <li key={i} className="text-xs text-[#4a3c2e] flex gap-2">
                <span className="text-[#c8a97a] shrink-0">–</span>
                {req.replace(/_/g, " ")}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Materiality context */}
      {gap.materiality_context && (
        <div className="pt-2 border-t border-[#e0d4bf]">
          <p className="text-xs text-[#8b7355] italic">{gap.materiality_context}</p>
        </div>
      )}
    </div>
  );
}
