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
      <div className="p-5">
        {/* Header row */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 flex-wrap">
            {/* Claim type */}
            <span className="px-2 py-0.5 rounded bg-[#eddfc8] text-[#4a3c2e] text-xs font-semibold">
              {CLAIM_TYPE_LABELS[claimData.claim_type] ?? claimData.claim_type}
            </span>
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
          </div>

          {/* Verdict */}
          {verdict && <VerdictBadge verdict={verdict.verdict} />}
        </div>

        {/* Claim text */}
        <p className="text-slate-800 text-sm font-medium leading-relaxed mb-3">
          {claimData.claim_text}
        </p>

        {/* IFRS tags (left) + page/link (right) */}
        <div className="mt-3 flex items-center justify-between gap-3">
          {/* IFRS tags */}
          <div className="flex flex-wrap gap-1.5">
            {claimData.ifrs_paragraphs.map((mapping, i) => (
              <IFRSParagraphTag
                key={`${mapping.paragraph_id}-${i}`}
                paragraphId={mapping.paragraph_id}
                relevance={mapping.relevance}
              />
            ))}
          </div>

          {/* Page + document link */}
          <div className="flex items-center gap-2 text-xs text-[#6b5344] shrink-0">
            <span className="font-mono">p.{claimData.source_page}</span>
            <Link
              to={`/analysis/${reportId}?page=${claimData.source_page}&highlight=${claimData.claim_id}`}
              className="hover:text-slate-900 transition-colors"
            >
              View →
            </Link>
          </div>
        </div>
      </div>

      {/* Evidence chain toggle */}
      {evidence_chain.length > 0 && (
        <>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full flex items-center justify-between px-5 py-2.5 border-t border-[#e0d4bf] hover:bg-[#f5ecdb] transition-colors text-xs text-[#6b5344] hover:text-[#4a3c2e]"
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
