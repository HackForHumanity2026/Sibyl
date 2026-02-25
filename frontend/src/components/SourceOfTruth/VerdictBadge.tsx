/**
 * VerdictBadge - Color-coded badge displaying verdict status.
 * Implements FRD 13 Section 6.3.
 */

import { CheckCircle2, XCircle, HelpCircle, AlertTriangle } from "lucide-react";
import type { VerdictStatus } from "@/types/sourceOfTruth";

interface VerdictBadgeProps {
  verdict: VerdictStatus;
}

const VERDICT_CONFIG: Record<
  VerdictStatus,
  { label: string; className: string; Icon: React.ComponentType<{ size?: number }> }
> = {
  verified: {
    label: "Verified",
    className: "bg-emerald-50 text-emerald-700 border border-emerald-100",
    Icon: CheckCircle2,
  },
  unverified: {
    label: "Unverified",
    className: "bg-amber-50 text-amber-700 border border-amber-100",
    Icon: HelpCircle,
  },
  contradicted: {
    label: "Contradicted",
    className: "bg-rose-50 text-rose-700 border border-rose-100",
    Icon: XCircle,
  },
  insufficient_evidence: {
    label: "Insufficient",
    className: "bg-[#f5ecdb] text-[#4a3c2e] border border-slate-100",
    Icon: AlertTriangle,
  },
};

export function VerdictBadge({ verdict }: VerdictBadgeProps) {
  const config = VERDICT_CONFIG[verdict];

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${config.className}`}
    >
      <config.Icon size={12} />
      {config.label}
    </span>
  );
}
