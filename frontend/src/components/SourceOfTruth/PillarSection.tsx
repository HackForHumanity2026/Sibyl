/**
 * PillarSection - Section for a single IFRS pillar with claims and gaps.
 * Implements FRD 13 Section 5.
 */

import type {
  ClaimWithVerdictResponse,
  DisclosureGapResponse,
  PillarSummaryResponse,
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

export function PillarSection({
  pillar,
  claims,
  gaps,
  summary,
  reportId,
}: PillarSectionProps) {
  const pillarInfo = PILLAR_INFO[pillar];

  // Don't render if no content
  if (claims.length === 0 && gaps.length === 0) {
    return null;
  }

  return (
    <section className="space-y-4">
      {/* Pillar Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 pb-2 border-b border-border">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{pillarInfo.icon}</span>
          <div>
            <h2 className="text-xl font-semibold text-foreground">
              {pillarInfo.displayName}
            </h2>
            <p className="text-sm text-muted-foreground">
              {pillarInfo.description}
            </p>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1.5">
            <span className="text-muted-foreground">Claims:</span>
            <span className="font-medium text-foreground">
              {summary.total_claims}
            </span>
          </div>
          {summary.verified_claims > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-green-400">{summary.verified_claims}</span>
            </div>
          )}
          {summary.contradicted_claims > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-red-400">{summary.contradicted_claims}</span>
            </div>
          )}
          {(summary.unverified_claims > 0 ||
            summary.insufficient_evidence_claims > 0) && (
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-yellow-500" />
              <span className="text-yellow-400">
                {summary.unverified_claims + summary.insufficient_evidence_claims}
              </span>
            </div>
          )}
          {summary.disclosure_gaps > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="text-muted-foreground">Gaps:</span>
              <span className="text-orange-400">{summary.disclosure_gaps}</span>
            </div>
          )}
        </div>
      </div>

      {/* Claims List */}
      {claims.length > 0 && (
        <div className="space-y-4">
          {claims.map((claim) => (
            <ClaimCard
              key={claim.claim.claim_id}
              claim={claim}
              reportId={reportId}
            />
          ))}
        </div>
      )}

      {/* Disclosure Gaps */}
      <DisclosureGapsSection gaps={gaps} pillar={pillar} />
    </section>
  );
}
