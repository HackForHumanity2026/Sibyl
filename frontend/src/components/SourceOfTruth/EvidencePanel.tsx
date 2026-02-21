/**
 * EvidencePanel - Expandable panel showing evidence chain from agents.
 * Implements FRD 13 Section 7.
 */

import { useState } from "react";
import type {
  EvidenceChainEntry,
  VerdictResponse,
  AgentName,
} from "@/types/sourceOfTruth";
import { AGENT_COLORS } from "@/types/sourceOfTruth";

interface EvidencePanelProps {
  evidenceChain: EvidenceChainEntry[];
  verdict: VerdictResponse | null;
}

const AGENT_DISPLAY_NAMES: Record<AgentName, string> = {
  claims: "Claims Agent",
  orchestrator: "Orchestrator",
  geography: "Geography Agent",
  legal: "Legal Agent",
  news_media: "News & Media Agent",
  academic: "Academic Agent",
  data_metrics: "Data Metrics Agent",
  judge: "Judge Agent",
};

const EVIDENCE_TYPE_LABELS: Record<string, string> = {
  ifrs_compliance: "IFRS Compliance Analysis",
  satellite_analysis: "Satellite Imagery Analysis",
  news_corroboration: "News Corroboration",
  news_contradiction: "News Contradiction",
  methodology_validation: "Methodology Validation",
  mathematical_consistency: "Mathematical Consistency Check",
  mathematical_inconsistency: "Mathematical Inconsistency",
  research_support: "Research Support",
  disclosure_gap: "Disclosure Gap",
};

export function EvidencePanel({ evidenceChain, verdict }: EvidencePanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (evidenceChain.length === 0) {
    return (
      <div className="text-sm text-muted-foreground italic">
        No evidence chain available.
      </div>
    );
  }

  return (
    <div className="border border-border rounded-md overflow-hidden">
      {/* Toggle Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-2 bg-muted/50 hover:bg-muted transition-colors text-left"
      >
        <span className="text-sm font-medium text-foreground">
          Evidence Chain ({evidenceChain.length} findings)
        </span>
        <span
          className={`text-muted-foreground transition-transform ${
            isExpanded ? "rotate-180" : ""
          }`}
        >
          ▼
        </span>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="p-4 space-y-4">
          {/* Evidence Timeline */}
          <div className="space-y-3">
            {evidenceChain.map((entry) => {
              const agentColor = AGENT_COLORS[entry.agent_name] || "#888888";
              const evidenceLabel =
                EVIDENCE_TYPE_LABELS[entry.evidence_type] || entry.evidence_type;

              return (
                <div
                  key={entry.finding_id}
                  className="relative pl-6 pb-3 border-l-2"
                  style={{ borderColor: agentColor }}
                >
                  {/* Timeline dot */}
                  <div
                    className="absolute -left-[5px] top-0 w-2 h-2 rounded-full"
                    style={{ backgroundColor: agentColor }}
                  />

                  {/* Finding content */}
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className="text-sm font-medium"
                        style={{ color: agentColor }}
                      >
                        {AGENT_DISPLAY_NAMES[entry.agent_name]}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        • {evidenceLabel}
                      </span>
                      {entry.iteration > 1 && (
                        <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                          Iteration {entry.iteration}
                        </span>
                      )}
                    </div>

                    <p className="text-sm text-foreground">{entry.summary}</p>

                    {/* Confidence and Support indicators */}
                    <div className="flex items-center gap-3 text-xs">
                      {entry.supports_claim !== null && (
                        <span
                          className={
                            entry.supports_claim
                              ? "text-green-400"
                              : "text-red-400"
                          }
                        >
                          {entry.supports_claim ? "✓ Supports" : "✗ Contradicts"}
                        </span>
                      )}
                      {entry.confidence && (
                        <span className="text-muted-foreground">
                          Confidence: {entry.confidence}
                        </span>
                      )}
                    </div>

                    {/* Reasoning if available */}
                    {entry.reasoning && (
                      <p className="text-xs text-muted-foreground mt-1 italic">
                        {entry.reasoning}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Final Verdict Section */}
          {verdict && (
            <div className="pt-3 border-t border-border">
              <div className="flex items-center gap-2 mb-2">
                <span
                  className="text-sm font-medium"
                  style={{ color: AGENT_COLORS.judge }}
                >
                  Judge Agent Verdict
                </span>
              </div>
              <p className="text-sm text-foreground">{verdict.reasoning}</p>
              <div className="text-xs text-muted-foreground mt-1">
                After {verdict.iteration_count} iteration
                {verdict.iteration_count > 1 ? "s" : ""}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
