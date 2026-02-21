/**
 * ConsistencyCheckList - Data/Metrics Agent consistency check results.
 * Shows pass/fail status for each validation check.
 */

import type { ConsistencyCheck } from "@/types/dashboard";

interface ConsistencyCheckListProps {
  checks: ConsistencyCheck[];
}

export function ConsistencyCheckList({ checks }: ConsistencyCheckListProps) {
  if (checks.length === 0) {
    return (
      <div className="consistency-check-list consistency-check-list--empty">
        <div className="consistency-check-list__header">Consistency Checks</div>
        <span className="consistency-check-list__placeholder">
          No checks performed yet
        </span>
      </div>
    );
  }

  const passCount = checks.filter((c) => c.status === "pass").length;
  const failCount = checks.filter((c) => c.status === "fail").length;
  const pendingCount = checks.filter((c) => c.status === "pending").length;

  return (
    <div className="consistency-check-list">
      <div className="consistency-check-list__header">
        Consistency Checks
        <span className="consistency-check-list__summary">
          <span className="consistency-check-list__count consistency-check-list__count--pass">
            {passCount} pass
          </span>
          {failCount > 0 && (
            <span className="consistency-check-list__count consistency-check-list__count--fail">
              {failCount} fail
            </span>
          )}
          {pendingCount > 0 && (
            <span className="consistency-check-list__count consistency-check-list__count--pending">
              {pendingCount} pending
            </span>
          )}
        </span>
      </div>
      <div className="consistency-check-list__items">
        {checks.map((check) => (
          <div
            key={check.id}
            className={`consistency-check-list__item consistency-check-list__item--${check.status}`}
          >
            <div className="consistency-check-list__icon">
              {check.status === "pass" && (
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              )}
              {check.status === "fail" && (
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              )}
              {check.status === "pending" && (
                <div className="consistency-check-list__spinner" />
              )}
            </div>
            <div className="consistency-check-list__content">
              <div className="consistency-check-list__name">{check.checkName}</div>
              <div className="consistency-check-list__description">
                {check.description}
              </div>
              {check.result && (
                <div className="consistency-check-list__result">
                  {check.result}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
