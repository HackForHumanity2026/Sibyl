/**
 * S1S2MappingSidebar - Slide-out panel showing S1↔S2 cross-mapping.
 * Implements FRD 13 Section 8.
 */

import { useState } from "react";
import { X } from "lucide-react";
import type { SourceOfTruthReportResponse } from "@/types/sourceOfTruth";

interface S1S2MappingSidebarProps {
  report: SourceOfTruthReportResponse;
}

const S1_S2_MAPPINGS: { s1: string; s2: string; description: string }[] = [
  { s1: "S1.26",    s2: "S2.5",     description: "Governance objective" },
  { s1: "S1.27(a)", s2: "S2.6",     description: "Governance body oversight" },
  { s1: "S1.27(b)", s2: "S2.7",     description: "Management role" },
  { s1: "S1.33",    s2: "S2.14",    description: "Strategy and decision-making" },
  { s1: "S1.38",    s2: "S2.24",    description: "Risk management objective" },
  { s1: "S1.41(a)", s2: "S2.25(a)", description: "Risk identification" },
  { s1: "S1.41(d)", s2: "S2.26",    description: "Integration with ERM" },
  { s1: "S1.46",    s2: "S2.29",    description: "Metrics disclosure" },
];

export function S1S2MappingSidebar({ report }: S1S2MappingSidebarProps) {
  const [isOpen, setIsOpen] = useState(false);

  const coveredParagraphs = new Set<string>();
  Object.values(report.pillars).forEach((pillar) => {
    pillar.claims.forEach((claim) => {
      claim.claim.ifrs_paragraphs.forEach((p) => coveredParagraphs.add(p.paragraph_id));
    });
  });

  const getStatus = (s1: string, s2: string): "covered" | "partial" | "gap" => {
    const s1c = [...coveredParagraphs].some((p) => p.startsWith(s1));
    const s2c = [...coveredParagraphs].some((p) => p.startsWith(s2));
    if (s1c && s2c) return "covered";
    if (s1c || s2c) return "partial";
    return "gap";
  };

  const statusDot = (s: "covered" | "partial" | "gap") =>
    s === "covered" ? "bg-emerald-500" : s === "partial" ? "bg-amber-400" : "bg-rose-300";

  const covered  = S1_S2_MAPPINGS.filter((m) => getStatus(m.s1, m.s2) === "covered").length;
  const partial  = S1_S2_MAPPINGS.filter((m) => getStatus(m.s1, m.s2) === "partial").length;
  const gaps     = S1_S2_MAPPINGS.filter((m) => getStatus(m.s1, m.s2) === "gap").length;

  return (
    <>
      {/* Toggle tab */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed right-0 top-1/2 -translate-y-1/2 z-40 bg-slate-900 text-white px-2.5 py-3 rounded-l-lg shadow-lg hover:bg-slate-700 transition-colors text-xs font-medium tracking-wide"
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
        className={`fixed right-0 top-0 h-full w-96 max-w-full bg-[#fff6e9] border-l border-slate-200 shadow-2xl z-50 transform transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <h2 className="text-base font-semibold text-slate-800">S1 / S2 Cross-Mapping</h2>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 hover:bg-[#eddfc8] rounded-lg transition-colors text-[#8b7355] hover:text-slate-700"
          >
            <X size={18} />
          </button>
        </div>

        <div className="overflow-y-auto h-[calc(100%-65px)] px-5 py-4 space-y-4">
          {/* Summary stats */}
          <div className="grid grid-cols-3 text-center divide-x divide-[#e0d4bf] bg-[#f5ecdb] rounded-xl py-3">
            <div>
              <div className="text-2xl font-bold text-emerald-600">{covered}</div>
              <div className="text-xs text-[#6b5344] font-medium">Covered</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-amber-500">{partial}</div>
              <div className="text-xs text-[#6b5344] font-medium">Partial</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-rose-500">{gaps}</div>
              <div className="text-xs text-[#6b5344] font-medium">Gaps</div>
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 text-xs text-[#4a3c2e] font-medium">
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />Covered</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />Partial</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-rose-300 inline-block" />Gap</span>
          </div>

          {/* Mappings */}
          <div className="space-y-2">
            {S1_S2_MAPPINGS.map((m) => {
              const status = getStatus(m.s1, m.s2);
              return (
                <div
                  key={`${m.s1}-${m.s2}`}
                  className="p-3 bg-[#f5ecdb] space-y-2"
                >
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${statusDot(status)} shrink-0`} />
                    <span className="text-sm font-medium text-slate-800">{m.description}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-[#4a3c2e] font-mono font-semibold">
                    <span className="px-1.5 py-0.5 bg-[#eddfc8] rounded">{m.s1}</span>
                    <span className="text-[#8b7355]">↔</span>
                    <span className="px-1.5 py-0.5 bg-[#eddfc8] rounded">{m.s2}</span>
                  </div>
                </div>
              );
            })}
          </div>

          <p className="text-xs text-[#8b7355] pb-4">
            IFRS S2 climate-specific requirements fulfill corresponding S1 general sustainability requirements. Coverage is based on claims in this report.
          </p>
        </div>
      </div>
    </>
  );
}
