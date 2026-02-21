/**
 * FilterBar - Filter controls for the Source of Truth report.
 * Implements FRD 13 Section 10.
 */

import type { ReportFilters, VerdictStatus, ClaimType, AgentName, GapType } from "@/types/sourceOfTruth";
import type { IFRSPillar } from "@/types/ifrs";

interface FilterBarProps {
  filters: ReportFilters;
  onFiltersChange: (filters: ReportFilters) => void;
  onClearFilters: () => void;
}

const PILLAR_OPTIONS: { value: IFRSPillar; label: string }[] = [
  { value: "governance", label: "Governance" },
  { value: "strategy", label: "Strategy" },
  { value: "risk_management", label: "Risk Management" },
  { value: "metrics_targets", label: "Metrics & Targets" },
];

const VERDICT_OPTIONS: { value: VerdictStatus; label: string }[] = [
  { value: "verified", label: "Verified" },
  { value: "unverified", label: "Unverified" },
  { value: "contradicted", label: "Contradicted" },
  { value: "insufficient_evidence", label: "Insufficient Evidence" },
];

const CLAIM_TYPE_OPTIONS: { value: ClaimType; label: string }[] = [
  { value: "geographic", label: "Geographic" },
  { value: "quantitative", label: "Quantitative" },
  { value: "legal_governance", label: "Legal/Governance" },
  { value: "strategic", label: "Strategic" },
  { value: "environmental", label: "Environmental" },
];

const AGENT_OPTIONS: { value: AgentName; label: string }[] = [
  { value: "geography", label: "Geography" },
  { value: "legal", label: "Legal" },
  { value: "news_media", label: "News/Media" },
  { value: "academic", label: "Academic" },
  { value: "data_metrics", label: "Data/Metrics" },
];

const GAP_STATUS_OPTIONS: { value: GapType; label: string }[] = [
  { value: "fully_unaddressed", label: "Fully Unaddressed" },
  { value: "partially_addressed", label: "Partially Addressed" },
];

export function FilterBar({
  filters,
  onFiltersChange,
  onClearFilters,
}: FilterBarProps) {
  const hasActiveFilters = Object.values(filters).some(
    (v) => v !== undefined && v !== ""
  );

  const handleChange = (key: keyof ReportFilters, value: string) => {
    onFiltersChange({
      ...filters,
      [key]: value || undefined,
    });
  };

  return (
    <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-border py-3 px-4">
      <div className="flex flex-wrap items-center gap-3">
        {/* Pillar Filter */}
        <select
          value={filters.pillar || ""}
          onChange={(e) => handleChange("pillar", e.target.value)}
          className="h-9 px-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">All Pillars</option>
          {PILLAR_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* Claim Type Filter */}
        <select
          value={filters.claimType || ""}
          onChange={(e) => handleChange("claimType", e.target.value)}
          className="h-9 px-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">All Types</option>
          {CLAIM_TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* Verdict Filter */}
        <select
          value={filters.verdict || ""}
          onChange={(e) => handleChange("verdict", e.target.value)}
          className="h-9 px-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">All Verdicts</option>
          {VERDICT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* Agent Filter */}
        <select
          value={filters.agent || ""}
          onChange={(e) => handleChange("agent", e.target.value)}
          className="h-9 px-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">All Agents</option>
          {AGENT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* Gap Status Filter */}
        <select
          value={filters.gapStatus || ""}
          onChange={(e) => handleChange("gapStatus", e.target.value)}
          className="h-9 px-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">All Gap Status</option>
          {GAP_STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* IFRS Paragraph Search */}
        <input
          type="text"
          placeholder="Search IFRS paragraph..."
          value={filters.ifrsSearch || ""}
          onChange={(e) => handleChange("ifrsSearch", e.target.value)}
          className="h-9 px-3 rounded-md border border-input bg-background text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring w-48"
        />

        {/* Clear Filters Button */}
        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="h-9 px-3 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            Clear Filters
          </button>
        )}
      </div>
    </div>
  );
}
