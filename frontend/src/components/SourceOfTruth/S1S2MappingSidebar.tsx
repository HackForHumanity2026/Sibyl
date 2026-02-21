/**
 * S1S2MappingSidebar - Slide-out sidebar showing S1↔S2 cross-mapping.
 * Implements FRD 13 Section 8.
 */

import { useState } from "react";
import type { SourceOfTruthReportResponse } from "@/types/sourceOfTruth";

interface S1S2MappingSidebarProps {
  report: SourceOfTruthReportResponse;
}

// S1 to S2 mapping based on IFRS standards
const S1_S2_MAPPINGS: { s1: string; s2: string; description: string }[] = [
  {
    s1: "S1.26",
    s2: "S2.5",
    description: "Governance objective",
  },
  {
    s1: "S1.27(a)",
    s2: "S2.6",
    description: "Governance body oversight",
  },
  {
    s1: "S1.27(b)",
    s2: "S2.7",
    description: "Management role",
  },
  {
    s1: "S1.33",
    s2: "S2.14",
    description: "Strategy and decision-making",
  },
  {
    s1: "S1.38",
    s2: "S2.24",
    description: "Risk management objective",
  },
  {
    s1: "S1.41(a)",
    s2: "S2.25(a)",
    description: "Risk identification",
  },
  {
    s1: "S1.41(d)",
    s2: "S2.26",
    description: "Integration with ERM",
  },
  {
    s1: "S1.46",
    s2: "S2.29",
    description: "Metrics disclosure",
  },
];

export function S1S2MappingSidebar({ report }: S1S2MappingSidebarProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Collect all paragraph IDs from claims
  const coveredParagraphs = new Set<string>();
  Object.values(report.pillars).forEach((pillar) => {
    pillar.claims.forEach((claim) => {
      claim.claim.ifrs_paragraphs.forEach((p) => {
        coveredParagraphs.add(p.paragraph_id);
      });
    });
  });

  // Check coverage status for each mapping
  const getMappingStatus = (
    s1: string,
    s2: string
  ): "covered" | "partial" | "gap" => {
    const s1Covered = [...coveredParagraphs].some((p) => p.startsWith(s1));
    const s2Covered = [...coveredParagraphs].some((p) => p.startsWith(s2));

    if (s1Covered && s2Covered) return "covered";
    if (s1Covered || s2Covered) return "partial";
    return "gap";
  };

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed right-4 top-1/2 -translate-y-1/2 z-40 bg-primary text-primary-foreground px-3 py-2 rounded-l-lg shadow-lg hover:bg-primary/90 transition-colors text-sm font-medium"
        style={{ writingMode: "vertical-rl", textOrientation: "mixed" }}
      >
        S1/S2 Mapping
      </button>

      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed right-0 top-0 h-full w-96 max-w-full bg-background border-l border-border shadow-xl z-50 transform transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">
            S1/S2 Cross-Mapping
          </h2>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-muted rounded transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto h-[calc(100%-60px)]">
          <p className="text-sm text-muted-foreground mb-4">
            IFRS S2 climate-specific requirements fulfill corresponding S1
            general sustainability requirements. Coverage status is based on
            claims in this report.
          </p>

          {/* Legend */}
          <div className="flex items-center gap-4 mb-4 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-muted-foreground">Covered</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-yellow-500" />
              <span className="text-muted-foreground">Partial</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-gray-500" />
              <span className="text-muted-foreground">Gap</span>
            </div>
          </div>

          {/* Mappings */}
          <div className="space-y-3">
            {S1_S2_MAPPINGS.map((mapping) => {
              const status = getMappingStatus(mapping.s1, mapping.s2);
              const statusColor =
                status === "covered"
                  ? "bg-green-500"
                  : status === "partial"
                  ? "bg-yellow-500"
                  : "bg-gray-500";

              return (
                <div
                  key={`${mapping.s1}-${mapping.s2}`}
                  className="p-3 rounded-lg border border-border bg-muted/30 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${statusColor}`} />
                      <span className="text-sm font-medium text-foreground">
                        {mapping.description}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="px-1.5 py-0.5 rounded bg-muted text-foreground font-mono">
                      {mapping.s1}
                    </span>
                    <span className="text-muted-foreground">↔</span>
                    <span className="px-1.5 py-0.5 rounded bg-muted text-foreground font-mono">
                      {mapping.s2}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Summary */}
          <div className="mt-6 p-3 rounded-lg bg-muted/50 border border-border">
            <div className="text-sm font-medium text-foreground mb-2">
              Coverage Summary
            </div>
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div>
                <div className="text-lg font-bold text-green-400">
                  {
                    S1_S2_MAPPINGS.filter(
                      (m) => getMappingStatus(m.s1, m.s2) === "covered"
                    ).length
                  }
                </div>
                <div className="text-muted-foreground">Covered</div>
              </div>
              <div>
                <div className="text-lg font-bold text-yellow-400">
                  {
                    S1_S2_MAPPINGS.filter(
                      (m) => getMappingStatus(m.s1, m.s2) === "partial"
                    ).length
                  }
                </div>
                <div className="text-muted-foreground">Partial</div>
              </div>
              <div>
                <div className="text-lg font-bold text-gray-400">
                  {
                    S1_S2_MAPPINGS.filter(
                      (m) => getMappingStatus(m.s1, m.s2) === "gap"
                    ).length
                  }
                </div>
                <div className="text-muted-foreground">Gaps</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
