/**
 * GapCard - Displays a disclosure gap with severity and materiality context.
 * Implements FRD 13 Section 9.3.
 */

import type { DisclosureGapResponse } from "@/types/sourceOfTruth";
import { GAP_COLORS } from "@/types/sourceOfTruth";
import { IFRSParagraphTag } from "./IFRSParagraphTag";

interface GapCardProps {
  gap: DisclosureGapResponse;
}

const SEVERITY_LABELS: Record<string, { label: string; color: string }> = {
  high: { label: "High Severity", color: "text-red-400" },
  medium: { label: "Medium Severity", color: "text-yellow-400" },
  low: { label: "Low Severity", color: "text-gray-400" },
};

const GAP_TYPE_LABELS: Record<string, string> = {
  fully_unaddressed: "Fully Unaddressed",
  partially_addressed: "Partially Addressed",
};

export function GapCard({ gap }: GapCardProps) {
  const colors = GAP_COLORS[gap.gap_type];
  const severity = SEVERITY_LABELS[gap.severity] || SEVERITY_LABELS.medium;

  return (
    <div
      className={`rounded-lg border-l-4 ${colors.border} ${colors.bg} p-4 space-y-3`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <IFRSParagraphTag paragraphId={gap.paragraph_id} />
          <span className="text-xs text-muted-foreground">
            {GAP_TYPE_LABELS[gap.gap_type]}
          </span>
          <span className={`text-xs ${severity.color}`}>{severity.label}</span>
        </div>
        {gap.s1_counterpart && (
          <span className="text-xs text-muted-foreground">
            S1 counterpart: {gap.s1_counterpart}
          </span>
        )}
      </div>

      {/* Requirement Text */}
      <p className="text-sm text-foreground">{gap.requirement_text}</p>

      {/* Missing Requirements */}
      {gap.missing_requirements.length > 0 && (
        <div className="space-y-1">
          <span className="text-xs font-medium text-muted-foreground">
            Missing Requirements:
          </span>
          <ul className="list-disc list-inside text-xs text-foreground space-y-0.5">
            {gap.missing_requirements.map((req, index) => (
              <li key={index}>{req.replace(/_/g, " ")}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Materiality Context */}
      {gap.materiality_context && (
        <div className="pt-2 border-t border-border/50">
          <span className="text-xs font-medium text-muted-foreground">
            Why this matters:
          </span>
          <p className="text-xs text-foreground mt-1">
            {gap.materiality_context}
          </p>
        </div>
      )}
    </div>
  );
}
