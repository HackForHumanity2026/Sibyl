/**
 * ClaimCard - Displays a claim with verdict, IFRS tags, and evidence chain.
 * Implements FRD 13 Section 6.
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { ChevronDown } from "lucide-react";
import type { ClaimWithVerdictResponse } from "@/types/sourceOfTruth";
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
  legal_governance: "Legal / Governance",
  strategic: "Strategic",
  environmental: "Environmental",
};

const PRIORITY_LABELS: Record<string, string> = {
  high: "High",
  medium: "Medium",
  low: "Low",
};

export function ClaimCard({ claim, reportId }: ClaimCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const { claim: claimData, verdict, evidence_chain } = claim;

  return (
    <div className="bg-[#fff6e9] overflow-hidden">
      {/* Card body */}
      <div className="py-4 px-5">
        {/* Single compact row: priority dot · verdict · IFRS tags · page + link */}
        <div className="flex items-center gap-2 mb-2">
          {/* Priority dot */}
          <span
            title={PRIORITY_LABELS[claimData.priority] ?? claimData.priority}
            className={`w-2 h-2 rounded-full shrink-0 ${
              claimData.priority === "high"
                ? "bg-rose-500"
                : claimData.priority === "medium"
                ? "bg-amber-400"
                : "bg-[#c8a97a]"
            }`}
          />

          {/* Verdict */}
          {verdict && <VerdictBadge verdict={verdict.verdict} />}

          {/* IFRS tags */}
          <div className="flex flex-wrap gap-1 flex-1">
            {claimData.ifrs_paragraphs.map((mapping, i) => (
              <IFRSParagraphTag
                key={`${mapping.paragraph_id}-${i}`}
                paragraphId={mapping.paragraph_id}
                relevance={mapping.relevance}
              />
            ))}
          </div>

          {/* Page + document link */}
          <div className="flex items-center gap-2 text-xs text-[#8b7355] shrink-0">
            <span className="font-mono">p.{claimData.source_page}</span>
            <Link
              to={`/analysis/${reportId}?page=${claimData.source_page}&highlight=${claimData.claim_id}`}
              className="hover:text-[#4a3c2e] transition-colors"
            >
              View →
            </Link>
          </div>
        </div>

        {/* Claim text */}
        <p className="text-slate-800 text-sm leading-relaxed">
          {claimData.claim_text}
        </p>
      </div>

      {/* Evidence chain toggle — flush continuation of the card, no top border */}
      {evidence_chain.length > 0 && (
        <>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full flex items-center justify-between px-5 py-2 hover:bg-[#f5ecdb] transition-colors text-xs text-[#8b7355] hover:text-[#4a3c2e]"
          >
            <span>Evidence Chain ({evidence_chain.length} findings)</span>
            <ChevronDown
              size={14}
              className={`transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`}
            />
          </button>

          {isExpanded && (
            <div className="bg-[#fff6e9]">
              <EvidencePanel evidenceChain={evidence_chain} verdict={verdict} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
