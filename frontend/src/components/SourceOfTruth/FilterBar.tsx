/**
 * FilterBar - Filter controls for the Source of Truth report.
 * Implements FRD 13 Section 10.
 */

import { Search, X } from "lucide-react";
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
  { value: "insufficient_evidence", label: "Insufficient" },
];

const CLAIM_TYPE_OPTIONS: { value: ClaimType; label: string }[] = [
  { value: "geographic", label: "Geographic" },
  { value: "quantitative", label: "Quantitative" },
  { value: "legal_governance", label: "Legal / Gov" },
  { value: "strategic", label: "Strategic" },
  { value: "environmental", label: "Environmental" },
];

const AGENT_OPTIONS: { value: AgentName; label: string }[] = [
  { value: "geography", label: "Geography" },
  { value: "legal", label: "Legal" },
  { value: "news_media", label: "News" },
  { value: "academic", label: "Academic" },
  { value: "data_metrics", label: "Data" },
];

const GAP_STATUS_OPTIONS: { value: GapType; label: string }[] = [
  { value: "fully_unaddressed", label: "Unaddressed" },
  { value: "partially_addressed", label: "Partial" },
];

function FilterSelect<T extends string>({
  value,
  onChange,
  options,
  placeholder,
}: {
  value: T | undefined;
  onChange: (v: T | undefined) => void;
  options: { value: T; label: string }[];
  placeholder: string;
}) {
  return (
    <select
      value={value ?? ""}
      onChange={(e) => onChange((e.target.value as T) || undefined)}
      className="h-8 px-2.5 rounded-lg border border-[#e0d4bf] bg-[#fff6e9] text-sm text-[#4a3c2e] focus:outline-none focus:ring-2 focus:ring-[#e0d4bf] transition-all appearance-none pr-7 cursor-pointer"
      style={{ backgroundImage: "url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%239ca3af' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e\")", backgroundRepeat: "no-repeat", backgroundPosition: "right 0.4rem center", backgroundSize: "1.2em 1.2em" }}
    >
      <option value="">{placeholder}</option>
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  );
}

export function FilterBar({ filters, onFiltersChange, onClearFilters }: FilterBarProps) {
  const hasActiveFilters = Object.values(filters).some((v) => v !== undefined && v !== "");

  const handleChange = <K extends keyof ReportFilters>(key: K, value: ReportFilters[K]) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  return (
    <div className="sticky top-0 z-10 bg-[#fff6e9]/90 backdrop-blur-sm border-b border-[#e0d4bf]">
      <div className="max-w-5xl mx-auto px-6 py-3 flex flex-wrap items-center gap-2">
        {/* Filters */}
        <FilterSelect
          value={filters.pillar}
          onChange={(v) => handleChange("pillar", v)}
          options={PILLAR_OPTIONS}
          placeholder="All Pillars"
        />
        <FilterSelect
          value={filters.claimType}
          onChange={(v) => handleChange("claimType", v)}
          options={CLAIM_TYPE_OPTIONS}
          placeholder="All Types"
        />
        <FilterSelect
          value={filters.verdict}
          onChange={(v) => handleChange("verdict", v)}
          options={VERDICT_OPTIONS}
          placeholder="All Verdicts"
        />
        <FilterSelect
          value={filters.agent}
          onChange={(v) => handleChange("agent", v)}
          options={AGENT_OPTIONS}
          placeholder="All Agents"
        />
        <FilterSelect
          value={filters.gapStatus}
          onChange={(v) => handleChange("gapStatus", v)}
          options={GAP_STATUS_OPTIONS}
          placeholder="All Gaps"
        />

        {/* Search */}
        <div className="relative ml-auto">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#8b7355]" />
          <input
            type="text"
            placeholder="Search IFRS paragraph…"
            value={filters.ifrsSearch ?? ""}
            onChange={(e) => handleChange("ifrsSearch", e.target.value || undefined)}
            className="h-8 pl-8 pr-3 rounded-lg border border-[#e0d4bf] bg-[#fff6e9] text-sm placeholder:text-[#8b7355] focus:outline-none focus:ring-2 focus:ring-[#e0d4bf] transition-all w-44"
          />
        </div>

        {/* Clear */}
        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="flex items-center gap-1.5 h-8 px-3 rounded-lg text-sm text-[#6b5344] hover:text-[#4a3c2e] hover:bg-[#eddfc8] transition-colors"
          >
            <X size={14} />
            Clear
          </button>
        )}
      </div>
    </div>
  );
}
