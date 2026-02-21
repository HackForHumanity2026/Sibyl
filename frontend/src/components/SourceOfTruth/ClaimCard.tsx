/**
 * ClaimCard - Displays a claim with verdict, IFRS tags, and evidence chain.
 * Implements FRD 13 Section 6.
 */

import { Link } from "react-router-dom";
import type { ClaimWithVerdictResponse } from "@/types/sourceOfTruth";
import { VERDICT_COLORS } from "@/types/sourceOfTruth";
import { VerdictBadge } from "./VerdictBadge";
import { IFRSParagraphTag } from "./IFRSParagraphTag";
import { EvidencePanel } from "./EvidencePanel";

interface ClaimCardProps {
  claim: ClaimWithVerdictResponse;
  reportId: string;
}

const CLAIM_TYPE_LABELS: Record<string, string> = {
  geographic: "Geographic",
  quantitative: "Quantitative",
  legal_governance: "Legal/Governance",
  strategic: "Strategic",
  environmental: "Environmental",
};

const PRIORITY_LABELS: Record<string, string> = {
  high: "High",
  medium: "Medium",
  low: "Low",
};

export function ClaimCard({ claim, reportId }: ClaimCardProps) {
  const { claim: claimData, verdict, evidence_chain } = claim;

  // Get border color based on verdict
  const borderColor = verdict
    ? VERDICT_COLORS[verdict.verdict].border
    : "border-gray-500";

  return (
    <div
      className={`bg-card rounded-lg border-l-4 ${borderColor} shadow-sm overflow-hidden`}
    >
      {/* Header */}
      <div className="px-4 py-3 bg-muted/30 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Claim Type Badge */}
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary/20 text-primary">
            {CLAIM_TYPE_LABELS[claimData.claim_type] || claimData.claim_type}
          </span>

          {/* Priority Badge */}
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
              claimData.priority === "high"
                ? "bg-red-500/20 text-red-400"
                : claimData.priority === "medium"
                ? "bg-yellow-500/20 text-yellow-400"
                : "bg-gray-500/20 text-gray-400"
            }`}
          >
            {PRIORITY_LABELS[claimData.priority]}
          </span>

          {/* Verdict Badge */}
          {verdict && <VerdictBadge verdict={verdict.verdict} />}
        </div>

        {/* Page Link */}
        <Link
          to={`/analysis/${reportId}?page=${claimData.source_page}&highlight=${claimData.claim_id}`}
          className="text-xs text-muted-foreground hover:text-primary transition-colors"
        >
          Page {claimData.source_page} →
        </Link>
      </div>

      {/* Content */}
      <div className="px-4 py-4 space-y-4">
        {/* Claim Text */}
        <p className="text-sm text-foreground leading-relaxed">
          {claimData.claim_text}
        </p>

        {/* IFRS Paragraph Tags */}
        {claimData.ifrs_paragraphs.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {claimData.ifrs_paragraphs.map((mapping, index) => (
              <IFRSParagraphTag
                key={`${mapping.paragraph_id}-${index}`}
                paragraphId={mapping.paragraph_id}
                relevance={mapping.relevance}
              />
            ))}
          </div>
        )}

        {/* Agent Reasoning */}
        {claimData.agent_reasoning && (
          <div className="text-xs text-muted-foreground italic border-l-2 border-muted pl-3">
            {claimData.agent_reasoning}
          </div>
        )}

        {/* Evidence Panel */}
        <EvidencePanel evidenceChain={evidence_chain} verdict={verdict} />
      </div>
    </div>
  );
}
