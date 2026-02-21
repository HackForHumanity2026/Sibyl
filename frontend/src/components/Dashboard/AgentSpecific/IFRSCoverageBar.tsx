/**
 * IFRSCoverageBar - Legal Agent IFRS coverage progress bars.
 * Shows coverage per pillar: Governance, Strategy, Risk Management, Metrics & Targets.
 */

import type { IFRSCoverage } from "@/types/dashboard";

interface IFRSCoverageBarProps {
  coverage: IFRSCoverage[];
}

const PILLAR_LABELS: Record<IFRSCoverage["pillar"], string> = {
  governance: "Governance",
  strategy: "Strategy",
  risk_management: "Risk Management",
  metrics_targets: "Metrics & Targets",
};

export function IFRSCoverageBar({ coverage }: IFRSCoverageBarProps) {
  if (coverage.length === 0) {
    return (
      <div className="ifrs-coverage-bar ifrs-coverage-bar--empty">
        <div className="ifrs-coverage-bar__header">IFRS Coverage</div>
        <span className="ifrs-coverage-bar__placeholder">
          No coverage data available
        </span>
      </div>
    );
  }

  return (
    <div className="ifrs-coverage-bar">
      <div className="ifrs-coverage-bar__header">IFRS Coverage</div>
      <div className="ifrs-coverage-bar__pillars">
        {coverage.map((pillar) => {
          const total = pillar.paragraphsTotal || 1;
          const coveredPercent = (pillar.paragraphsCovered / total) * 100;
          const partialPercent = (pillar.paragraphsPartial / total) * 100;
          const gapPercent = (pillar.paragraphsGaps / total) * 100;

          return (
            <div key={pillar.pillar} className="ifrs-coverage-bar__pillar">
              <div className="ifrs-coverage-bar__pillar-label">
                {PILLAR_LABELS[pillar.pillar]}
              </div>
              <div className="ifrs-coverage-bar__progress">
                <div
                  className="ifrs-coverage-bar__segment ifrs-coverage-bar__segment--covered"
                  style={{ width: `${coveredPercent}%` }}
                  title={`Covered: ${pillar.paragraphsCovered}`}
                />
                <div
                  className="ifrs-coverage-bar__segment ifrs-coverage-bar__segment--partial"
                  style={{ width: `${partialPercent}%` }}
                  title={`Partial: ${pillar.paragraphsPartial}`}
                />
                <div
                  className="ifrs-coverage-bar__segment ifrs-coverage-bar__segment--gap"
                  style={{ width: `${gapPercent}%` }}
                  title={`Gaps: ${pillar.paragraphsGaps}`}
                />
              </div>
              <div className="ifrs-coverage-bar__pillar-stats">
                {pillar.paragraphsCovered}/{total} covered
                {pillar.paragraphsPartial > 0 &&
                  `, ${pillar.paragraphsPartial} partial`}
                {pillar.paragraphsGaps > 0 &&
                  `, ${pillar.paragraphsGaps} gaps`}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
