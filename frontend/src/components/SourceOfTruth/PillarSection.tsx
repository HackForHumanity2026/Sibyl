/**
 * PillarSection - Section for a single IFRS pillar with claims and gaps.
 * Implements FRD 13 Section 5.
 */

import { Building2, Target, AlertTriangle, BarChart3 } from "lucide-react";
import type { LucideProps } from "lucide-react";
import type {
  ClaimWithVerdictResponse,
  DisclosureGapResponse,
  PillarSummaryResponse,
  PillarIconName,
} from "@/types/sourceOfTruth";
import type { IFRSPillar } from "@/types/ifrs";
import { PILLAR_INFO } from "@/types/sourceOfTruth";
import { ClaimCard } from "./ClaimCard";
import { DisclosureGapsSection } from "./DisclosureGapsSection";

interface PillarSectionProps {
  pillar: IFRSPillar;
  claims: ClaimWithVerdictResponse[];
  gaps: DisclosureGapResponse[];
  summary: PillarSummaryResponse;
  reportId: string;
}

const PILLAR_ICON_MAP: Record<PillarIconName, React.ComponentType<LucideProps>> = {
  Building2,
  Target,
  AlertTriangle,
  BarChart3,
};

export function PillarSection({
  pillar,
  claims,
  gaps,
  summary,
  reportId,
}: PillarSectionProps) {
  const pillarInfo = PILLAR_INFO[pillar];
  const PillarIcon = PILLAR_ICON_MAP[pillarInfo.icon];

  if (claims.length === 0 && gaps.length === 0) return null;

  return (
    <section className="border-t border-[#e0d4bf] pt-8">
      {/* Pillar header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[#eddfc8] rounded-lg">
            <PillarIcon size={20} className="text-[#4a3c2e]" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-[#4a3c2e]">{pillarInfo.displayName}</h2>
            <p className="text-xs text-[#6b5344] mt-0.5">{pillarInfo.description}</p>
          </div>
        </div>

        {/* Summary badges */}
        <div className="flex gap-2">
          {summary.total_claims > 0 && (
            <span className="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-semibold border border-emerald-100">
              Claims: {summary.total_claims}
            </span>
          )}
          {summary.disclosure_gaps > 0 && (
            <span className="px-3 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-semibold border border-amber-100">
              Gaps: {summary.disclosure_gaps}
            </span>
          )}
          {summary.contradicted_claims > 0 && (
            <span className="px-3 py-1 rounded-full bg-rose-50 text-rose-700 text-xs font-semibold border border-rose-100">
              Contradicted: {summary.contradicted_claims}
            </span>
          )}
        </div>
      </div>

      {/* Claims */}
      {claims.length > 0 && (
        <div className="divide-y divide-[#e0d4bf] border-y border-[#e0d4bf] mb-6">
          {claims.map((claim) => (
            <ClaimCard key={claim.claim.claim_id} claim={claim} reportId={reportId} />
          ))}
        </div>
      )}

      {/* Gaps */}
      <DisclosureGapsSection gaps={gaps} pillar={pillar} />
    </section>
  );
}
