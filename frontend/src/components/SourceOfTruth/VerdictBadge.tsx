/**
 * VerdictBadge - Plain text verdict label with a small icon. No pill background.
 * Implements FRD 13 Section 6.3.
 */

import { CheckCircle2, XCircle, HelpCircle, AlertTriangle } from "lucide-react";
import type { VerdictStatus } from "@/types/sourceOfTruth";

interface VerdictBadgeProps {
  verdict: VerdictStatus;
}

const VERDICT_CONFIG: Record<
  VerdictStatus,
  { label: string; textClass: string; Icon: React.ComponentType<{ size?: number; className?: string }> }
> = {
  verified: {
    label: "Verified",
    textClass: "text-emerald-700",
    Icon: CheckCircle2,
  },
  unverified: {
    label: "Unverified",
    textClass: "text-amber-600",
    Icon: HelpCircle,
  },
  contradicted: {
    label: "Contradicted",
    textClass: "text-rose-600",
    Icon: XCircle,
  },
  insufficient_evidence: {
    label: "Insufficient",
    textClass: "text-[#78695a]",
    Icon: AlertTriangle,
  },
};

export function VerdictBadge({ verdict }: VerdictBadgeProps) {
  const config = VERDICT_CONFIG[verdict];

  return (
    <span className={`inline-flex items-center gap-1 text-xs font-semibold ${config.textClass}`}>
      <config.Icon size={11} />
      {config.label}
    </span>
  );
}
