/**
 * VerdictBadge - Color-coded badge displaying verdict status.
 * Implements FRD 13 Section 6.3.
 */

import type { VerdictStatus } from "@/types/sourceOfTruth";
import { VERDICT_COLORS } from "@/types/sourceOfTruth";

interface VerdictBadgeProps {
  verdict: VerdictStatus;
}

const VERDICT_LABELS: Record<VerdictStatus, string> = {
  verified: "Verified",
  unverified: "Unverified",
  contradicted: "Contradicted",
  insufficient_evidence: "Insufficient Evidence",
};

const VERDICT_ICONS: Record<VerdictStatus, string> = {
  verified: "✓",
  unverified: "?",
  contradicted: "✗",
  insufficient_evidence: "⚠",
};

export function VerdictBadge({ verdict }: VerdictBadgeProps) {
  const colors = VERDICT_COLORS[verdict];
  const label = VERDICT_LABELS[verdict];
  const icon = VERDICT_ICONS[verdict];

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${colors.bg} ${colors.text}`}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </span>
  );
}
