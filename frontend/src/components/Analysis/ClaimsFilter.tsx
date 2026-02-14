/**
 * ClaimsFilter - Filter controls for claims by type and priority.
 * Implements FRD 3 Section 7.3.
 */

import type { ClaimType, ClaimPriority } from "@/types/claim";

interface ClaimsFilterProps {
  typeFilter: ClaimType | null;
  priorityFilter: ClaimPriority | null;
  onTypeChange: (type: ClaimType | null) => void;
  onPriorityChange: (priority: ClaimPriority | null) => void;
  claimsByType: Record<string, number>;
  claimsByPriority: Record<string, number>;
}

const CLAIM_TYPES: { value: ClaimType; label: string }[] = [
  { value: "geographic", label: "Geographic" },
  { value: "quantitative", label: "Quantitative" },
  { value: "legal_governance", label: "Legal/Governance" },
  { value: "strategic", label: "Strategic" },
  { value: "environmental", label: "Environmental" },
];

const PRIORITIES: { value: ClaimPriority; label: string }[] = [
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

export function ClaimsFilter({
  typeFilter,
  priorityFilter,
  onTypeChange,
  onPriorityChange,
  claimsByType,
  claimsByPriority,
}: ClaimsFilterProps) {
  return (
    <div className="claims-filter">
      <div className="claims-filter__group">
        <label className="claims-filter__label">Type</label>
        <div className="claims-filter__chips">
          <button
            className={`claims-filter__chip ${!typeFilter ? "claims-filter__chip--active" : ""}`}
            onClick={() => onTypeChange(null)}
          >
            All
          </button>
          {CLAIM_TYPES.map(({ value, label }) => {
            const count = claimsByType[value] || 0;
            return (
              <button
                key={value}
                className={`claims-filter__chip claims-filter__chip--${value} ${
                  typeFilter === value ? "claims-filter__chip--active" : ""
                }`}
                onClick={() => onTypeChange(value)}
                disabled={count === 0}
              >
                {label} ({count})
              </button>
            );
          })}
        </div>
      </div>

      <div className="claims-filter__group">
        <label className="claims-filter__label">Priority</label>
        <div className="claims-filter__chips">
          <button
            className={`claims-filter__chip ${!priorityFilter ? "claims-filter__chip--active" : ""}`}
            onClick={() => onPriorityChange(null)}
          >
            All
          </button>
          {PRIORITIES.map(({ value, label }) => {
            const count = claimsByPriority[value] || 0;
            return (
              <button
                key={value}
                className={`claims-filter__chip claims-filter__chip--priority-${value} ${
                  priorityFilter === value ? "claims-filter__chip--active" : ""
                }`}
                onClick={() => onPriorityChange(value)}
                disabled={count === 0}
              >
                {label} ({count})
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
