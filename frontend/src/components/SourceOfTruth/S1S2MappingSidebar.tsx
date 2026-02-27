/**
 * S1S2MappingSidebar - Slide-out panel showing S1↔S2 cross-mapping.
 * Implements FRD 13 Section 8.
 *
 * Redesigned: clearer intro, flow-arrow visuals, expandable mapping cards
 * with claim excerpts, and IFRS paragraph hover tooltips.
 */

import { useState } from "react";
import { X, ChevronDown, ChevronRight, ArrowRight } from "lucide-react";
import type { SourceOfTruthReportResponse } from "@/types/sourceOfTruth";
import { IFRSParagraphTag } from "./IFRSParagraphTag";

interface S1S2MappingSidebarProps {
  report: SourceOfTruthReportResponse;
}

const S1_S2_MAPPINGS: { s1: string; s2: string; description: string; why: string }[] = [
  { s1: "S1.26",    s2: "S2.5",     description: "Governance objective",       why: "Both standards require entities to disclose the governance objective for sustainability (S1) and climate (S2) oversight." },
  { s1: "S1.27(a)", s2: "S2.6",     description: "Governance body oversight",  why: "S1 requires disclosing the general governance body; S2 narrows this to climate-specific oversight." },
  { s1: "S1.27(b)", s2: "S2.7",     description: "Management role",            why: "Both standards require disclosing management's role — S1 generally, S2 specifically for climate." },
  { s1: "S1.33",    s2: "S2.14",    description: "Strategy and decision-making", why: "Climate strategy (S2.14) is the climate-specific implementation of S1's general strategy disclosure objective." },
  { s1: "S1.38",    s2: "S2.24",    description: "Risk management objective",  why: "Climate risk management (S2.24) fulfills the same disclosure objective as S1.38's general risk management requirement." },
  { s1: "S1.41(a)", s2: "S2.25(a)", description: "Risk identification",        why: "Both require disclosing inputs and parameters for risk identification — S2.25(a) specifically covers climate scenario analysis." },
  { s1: "S1.41(d)", s2: "S2.26",    description: "Integration with ERM",       why: "S2.26 requires the same ERM integration disclosure as S1.41(d) but scoped to climate-related risks." },
  { s1: "S1.46",    s2: "S2.29",    description: "Metrics disclosure",         why: "S2.29 is the climate-specific version of S1.46's general metrics and targets disclosure requirement." },
];

export function S1S2MappingSidebar({ report }: S1S2MappingSidebarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedMappings, setExpandedMappings] = useState<Set<string>>(new Set());

  const coveredParagraphs = new Set<string>();
  const paragraphToClaims = new Map<string, Array<{ claimText: string; pillar: string }>>();

  Object.entries(report.pillars).forEach(([pillarKey, pillar]) => {
    pillar.claims.forEach((claimItem) => {
      claimItem.claim.ifrs_paragraphs.forEach((p) => {
        coveredParagraphs.add(p.paragraph_id);
        if (!paragraphToClaims.has(p.paragraph_id)) {
          paragraphToClaims.set(p.paragraph_id, []);
        }
        paragraphToClaims.get(p.paragraph_id)!.push({
          claimText: claimItem.claim.claim_text,
          pillar: pillarKey,
        });
      });
    });
  });

  const getStatus = (s1: string, s2: string): "covered" | "partial" | "gap" => {
    const s1c = [...coveredParagraphs].some((p) => p.startsWith(s1));
    const s2c = [...coveredParagraphs].some((p) => p.startsWith(s2));
    if (s1c && s2c) return "covered";
    if (s1c || s2c) return "partial";
    return "gap";
  };

  const getClaimsForParagraph = (paragraphPrefix: string): Array<{ claimText: string; pillar: string }> => {
    const results: Array<{ claimText: string; pillar: string }> = [];
    for (const [pid, claims] of paragraphToClaims.entries()) {
      if (pid.startsWith(paragraphPrefix)) {
        results.push(...claims);
      }
    }
    return results;
  };

  const toggleMapping = (key: string) => {
    setExpandedMappings((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const covered = S1_S2_MAPPINGS.filter((m) => getStatus(m.s1, m.s2) === "covered").length;
  const partial  = S1_S2_MAPPINGS.filter((m) => getStatus(m.s1, m.s2) === "partial").length;
  const gaps     = S1_S2_MAPPINGS.filter((m) => getStatus(m.s1, m.s2) === "gap").length;

  const statusConfig = {
    covered: { dot: "bg-emerald-500", label: "Covered", textColor: "text-emerald-700", bg: "bg-emerald-50" },
    partial:  { dot: "bg-amber-400",  label: "Partial",  textColor: "text-amber-700",   bg: "bg-amber-50" },
    gap:      { dot: "bg-rose-400",   label: "Gap",      textColor: "text-rose-700",    bg: "bg-rose-50" },
  };

  return (
    <>
      {/* Toggle tab */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed right-0 top-1/2 -translate-y-1/2 z-40 bg-[#4a3c2e] text-[#fff6e9] px-2.5 py-3 rounded-l-lg shadow-lg hover:bg-[#6b5344] transition-colors text-xs font-medium tracking-wide"
        style={{ writingMode: "vertical-rl", textOrientation: "mixed" }}
      >
        S1 / S2
      </button>

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Panel */}
      <div
        className={`fixed right-0 top-0 h-full w-[420px] max-w-full bg-[#fff6e9] border-l border-[#e0d4bf] shadow-2xl z-50 transform transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="px-5 py-4 border-b border-[#e0d4bf]">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-base font-semibold text-[#4a3c2e]">S1 / S2 Cross-Mapping</h2>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 transition-colors text-[#8b7355] hover:text-[#4a3c2e]"
            >
              <X size={16} />
            </button>
          </div>
          <p className="text-xs text-[#8b7355] leading-relaxed">
            IFRS S2 (climate-specific) requirements fulfill corresponding S1 (general sustainability) requirements.
            Each row below shows a paired disclosure — hover the pills to see the full requirement text.
          </p>
        </div>

        <div className="overflow-y-auto h-[calc(100%-105px)] px-5 py-4 space-y-3">
          {/* Summary stats */}
          <div className="grid grid-cols-3 text-center bg-[#f5ecdb] py-3 gap-0">
            <div>
              <div className="text-xl font-bold text-emerald-600">{covered}</div>
              <div className="text-xs text-[#6b5344] font-medium">Both covered</div>
            </div>
            <div className="border-x border-[#e0d4bf]">
              <div className="text-xl font-bold text-amber-500">{partial}</div>
              <div className="text-xs text-[#6b5344] font-medium">One covered</div>
            </div>
            <div>
              <div className="text-xl font-bold text-rose-500">{gaps}</div>
              <div className="text-xs text-[#6b5344] font-medium">Neither</div>
            </div>
          </div>

          {/* Mappings */}
          <div className="space-y-2">
            {S1_S2_MAPPINGS.map((m) => {
              const status = getStatus(m.s1, m.s2);
              const { dot, label, textColor } = statusConfig[status];
              const key = `${m.s1}-${m.s2}`;
              const isExpanded = expandedMappings.has(key);
              const s1Claims = getClaimsForParagraph(m.s1);
              const s2Claims = getClaimsForParagraph(m.s2);
              const allClaims = [...s1Claims, ...s2Claims].slice(0, 3);

              return (
                <div key={key} className="bg-[#f5ecdb] overflow-hidden">
                  {/* Card header — always visible */}
                  <button
                    className="w-full text-left px-3 py-3"
                    onClick={() => toggleMapping(key)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        {/* Status + description */}
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`w-2 h-2 rounded-full ${dot} shrink-0`} />
                          <span className="text-xs font-semibold text-[#4a3c2e] truncate">{m.description}</span>
                          <span className={`text-xs font-medium ${textColor} ml-auto shrink-0`}>{label}</span>
                        </div>

                        {/* Flow visual: S1 ──→ S2 */}
                        <div className="flex items-center gap-2">
                          <IFRSParagraphTag paragraphId={m.s1} />
                          <ArrowRight size={12} className="text-[#8b7355] shrink-0" />
                          <IFRSParagraphTag paragraphId={m.s2} />
                        </div>
                      </div>

                      <span className="text-[#8b7355] shrink-0 mt-0.5">
                        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      </span>
                    </div>
                  </button>

                  {/* Expanded: Why + claims */}
                  {isExpanded && (
                    <div className="border-t border-[#e0d4bf] px-3 py-3 space-y-3 bg-[#fff6e9]">
                      {/* Why it's mapped */}
                      <div>
                        <p className="text-xs font-medium text-[#6b5344] mb-1 uppercase tracking-wide">Why mapped</p>
                        <p className="text-xs text-[#8b7355] leading-relaxed">{m.why}</p>
                      </div>

                      {/* Claims referencing these paragraphs */}
                      {allClaims.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-[#6b5344] mb-1.5 uppercase tracking-wide">Referenced claims</p>
                          <div className="space-y-1.5">
                            {allClaims.map((claim, i) => (
                              <div key={i} className="text-xs text-[#4a3c2e] bg-[#f5ecdb] px-2.5 py-2 rounded leading-relaxed">
                                {claim.claimText.length > 120
                                  ? claim.claimText.slice(0, 120) + "…"
                                  : claim.claimText}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {allClaims.length === 0 && (
                        <p className="text-xs text-[#c8a97a] italic">No claims reference these paragraphs yet.</p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <p className="text-xs text-[#8b7355] pb-4 leading-relaxed">
            Coverage is determined by claims extracted from this report that reference each paragraph.
          </p>
        </div>
      </div>
    </>
  );
}
