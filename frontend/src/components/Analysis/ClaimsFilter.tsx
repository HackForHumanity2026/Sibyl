/**
 * ClaimsFilter - Filter controls for claims by type and priority.
 * Implements FRD 3 Section 7.3.
 */

import type { ClaimType, ClaimPriority } from "@/types/claim";
import { cn } from "@/lib/utils";

interface ClaimsFilterProps {
  typeFilter: ClaimType | null;
  priorityFilter: ClaimPriority | null;
  onTypeChange: (type: ClaimType | null) => void;
  onPriorityChange: (priority: ClaimPriority | null) => void;
  claimsByType: Record<string, number>;
  claimsByPriority: Record<string, number>;
}

const CLAIM_TYPES: { value: ClaimType; label: string }[] = [
  { value: "geographic",      label: "Geographic" },
  { value: "quantitative",    label: "Quantitative" },
  { value: "legal_governance", label: "Legal" },
  { value: "strategic",       label: "Strategic" },
  { value: "environmental",   label: "Environmental" },
];

const PRIORITIES: { value: ClaimPriority; label: string }[] = [
  { value: "high",   label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low",    label: "Low" },
];

function Chip({
  active,
  disabled,
  onClick,
  children,
}: {
  active: boolean;
  disabled?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border transition-all",
        active
          ? "bg-slate-900 text-white border-slate-900"
          : "bg-[#fff6e9] text-[#6b5344] border-slate-200 hover:border-slate-400 hover:text-slate-700",
        disabled && "opacity-40 cursor-not-allowed"
      )}
    >
      {children}
    </button>
  );
}

export function ClaimsFilter({
  typeFilter,
  priorityFilter,
  onTypeChange,
  onPriorityChange,
  claimsByType,
  claimsByPriority,
}: ClaimsFilterProps) {
  return (
    <div className="px-3 py-2.5 border-b border-slate-100 space-y-2">
      {/* Type filter */}
      <div>
        <p className="text-xs font-semibold text-[#8b7355] uppercase tracking-wide mb-1.5">Type</p>
        <div className="flex flex-wrap gap-1.5">
          <Chip active={!typeFilter} onClick={() => onTypeChange(null)}>All</Chip>
          {CLAIM_TYPES.map(({ value, label }) => (
            <Chip
              key={value}
              active={typeFilter === value}
              disabled={(claimsByType[value] || 0) === 0}
              onClick={() => onTypeChange(value)}
            >
              {label}
              <span className="ml-1 opacity-60">{claimsByType[value] || 0}</span>
            </Chip>
          ))}
        </div>
      </div>

      {/* Priority filter */}
      <div>
        <p className="text-xs font-semibold text-[#8b7355] uppercase tracking-wide mb-1.5">Priority</p>
        <div className="flex flex-wrap gap-1.5">
          <Chip active={!priorityFilter} onClick={() => onPriorityChange(null)}>All</Chip>
          {PRIORITIES.map(({ value, label }) => (
            <Chip
              key={value}
              active={priorityFilter === value}
              disabled={(claimsByPriority[value] || 0) === 0}
              onClick={() => onPriorityChange(value)}
            >
              {label}
              <span className="ml-1 opacity-60">{claimsByPriority[value] || 0}</span>
            </Chip>
          ))}
        </div>
      </div>
    </div>
  );
}
