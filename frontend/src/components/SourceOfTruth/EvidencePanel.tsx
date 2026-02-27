/**
 * EvidencePanel - Expandable panel showing evidence chain from agents.
 * Implements FRD 13 Section 7.
 */

import { useState } from "react";
import { CheckCircle2, XCircle } from "lucide-react";
import type { EvidenceChainEntry, VerdictResponse, AgentName } from "@/types/sourceOfTruth";

interface EvidencePanelProps {
  evidenceChain: EvidenceChainEntry[];
  verdict: VerdictResponse | null;
}

const AGENT_DISPLAY_NAMES: Record<AgentName, string> = {
  claims: "Claims",
  orchestrator: "Orchestrator",
  geography: "Geography",
  legal: "Legal",
  news_media: "News & Media",
  academic: "Academic",
  data_metrics: "Data Metrics",
  judge: "Judge",
};

const EVIDENCE_TYPE_LABELS: Record<string, string> = {
  ifrs_compliance: "IFRS Compliance",
  satellite_analysis: "Satellite Imagery",
  news_corroboration: "News Corroboration",
  news_contradiction: "News Contradiction",
  methodology_validation: "Methodology Validation",
  mathematical_consistency: "Math Consistency",
  mathematical_inconsistency: "Math Inconsistency",
  research_support: "Research Support",
  disclosure_gap: "Disclosure Gap",
};

export function EvidencePanel({ evidenceChain, verdict }: EvidencePanelProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (evidenceChain.length === 0) return null;

  return (
    <div className="px-5 py-4 space-y-3">
      {evidenceChain.map((entry) => {
        const isOpen = expanded === entry.finding_id;
        const label = EVIDENCE_TYPE_LABELS[entry.evidence_type] ?? entry.evidence_type;
        const agentName = AGENT_DISPLAY_NAMES[entry.agent_name] ?? entry.agent_name;

        return (
          <div key={entry.finding_id} className="flex gap-3">
            {/* Timeline dot */}
            <div className="flex flex-col items-center">
              <div
                className={`mt-1 w-1.5 h-1.5 rounded-full shrink-0 ${
                  entry.supports_claim === true
                    ? "bg-emerald-500"
                    : entry.supports_claim === false
                    ? "bg-rose-500"
                    : "bg-[#c8a97a]"
                }`}
              />
              <div className="flex-1 w-px bg-[#eddfc8] mt-1" />
            </div>

            {/* Content */}
            <div className="pb-3 flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className="text-xs font-semibold text-[#4a3c2e]">{agentName}</span>
                <span className="text-xs text-[#8b7355]">{label}</span>
                {entry.iteration > 1 && (
                  <span className="text-xs text-[#8b7355] bg-[#eddfc8] px-1.5 py-0.5 rounded">
                    iter {entry.iteration}
                  </span>
                )}
                {entry.supports_claim !== null && (
                  <span className={`flex items-center gap-0.5 text-xs ${
                    entry.supports_claim ? "text-emerald-600" : "text-rose-600"
                  }`}>
                    {entry.supports_claim
                      ? <CheckCircle2 size={11} />
                      : <XCircle size={11} />}
                    {entry.supports_claim ? "Supports" : "Contradicts"}
                  </span>
                )}
              </div>

              <p className="text-xs text-[#4a3c2e] leading-relaxed">{entry.summary}</p>

              {entry.reasoning && (
                <button
                  onClick={() => setExpanded(isOpen ? null : entry.finding_id)}
                  className="text-xs text-[#8b7355] hover:text-[#4a3c2e] mt-1 transition-colors"
                >
                  {isOpen ? "Hide reasoning" : "Show reasoning"}
                </button>
              )}
              {isOpen && entry.reasoning && (
                <p className="text-xs text-[#8b7355] italic mt-1 leading-relaxed">
                  {entry.reasoning}
                </p>
              )}
            </div>
          </div>
        );
      })}

      {/* Judge verdict */}
      {verdict && (
        <div className="pt-3 border-t border-[#e0d4bf]">
          <p className="text-xs font-semibold text-[#4a3c2e] mb-1">Judge Verdict</p>
          <p className="text-xs text-[#4a3c2e] leading-relaxed">{verdict.reasoning}</p>
          <p className="text-xs text-[#8b7355] mt-1">
            After {verdict.iteration_count} iteration{verdict.iteration_count !== 1 ? "s" : ""}
          </p>
        </div>
      )}
    </div>
  );
}
