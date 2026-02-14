/**
 * DashboardPlaceholder - Placeholder for the Investigation Dashboard.
 * Implements FRD 4 - center panel placeholder.
 *
 * This will be replaced with the actual React Flow network graph
 * in FRD 5 (Orchestrator Agent / LangGraph Pipeline).
 */

export function DashboardPlaceholder() {
  return (
    <div className="dashboard-placeholder">
      <div className="dashboard-placeholder__content">
        <svg
          className="dashboard-placeholder__icon"
          width="64"
          height="64"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        >
          {/* Network/graph icon */}
          <circle cx="12" cy="5" r="2" />
          <circle cx="5" cy="19" r="2" />
          <circle cx="19" cy="19" r="2" />
          <line x1="12" y1="7" x2="12" y2="12" />
          <line x1="12" y1="12" x2="5" y2="17" />
          <line x1="12" y1="12" x2="19" y2="17" />
        </svg>
        <h3 className="dashboard-placeholder__title">Investigation Dashboard</h3>
        <p className="dashboard-placeholder__description">
          The multi-agent investigation network will appear here, showing
          the Claims Agent's findings and subsequent specialist agent analyses.
        </p>
        <div className="dashboard-placeholder__coming-soon">
          Coming in FRD 5
        </div>
      </div>
    </div>
  );
}
