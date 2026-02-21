/**
 * ComplianceSummary - Overview statistics for the report.
 * Implements FRD 13 Section 11.
 */

import type { ReportSummaryResponse } from "@/types/sourceOfTruth";

interface ComplianceSummaryProps {
  summary: ReportSummaryResponse;
}

export function ComplianceSummary({ summary }: ComplianceSummaryProps) {
  const totalVerdicts =
    summary.verdicts_by_type.verified +
    summary.verdicts_by_type.unverified +
    summary.verdicts_by_type.contradicted +
    summary.verdicts_by_type.insufficient_evidence;

  const verifiedPercentage =
    totalVerdicts > 0
      ? Math.round((summary.verdicts_by_type.verified / totalVerdicts) * 100)
      : 0;

  const totalGaps =
    (summary.gaps_by_status.fully_unaddressed || 0) +
    (summary.gaps_by_status.partially_addressed || 0);

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h2 className="text-lg font-semibold text-foreground mb-4">
        Compliance Summary
      </h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {/* Total Claims */}
        <div className="space-y-1">
          <div className="text-3xl font-bold text-foreground">
            {summary.total_claims}
          </div>
          <div className="text-sm text-muted-foreground">Total Claims</div>
        </div>

        {/* Verified Rate */}
        <div className="space-y-1">
          <div className="text-3xl font-bold text-green-400">
            {verifiedPercentage}%
          </div>
          <div className="text-sm text-muted-foreground">Verified</div>
        </div>

        {/* Contradicted */}
        <div className="space-y-1">
          <div className="text-3xl font-bold text-red-400">
            {summary.verdicts_by_type.contradicted}
          </div>
          <div className="text-sm text-muted-foreground">Contradicted</div>
        </div>

        {/* Disclosure Gaps */}
        <div className="space-y-1">
          <div className="text-3xl font-bold text-orange-400">{totalGaps}</div>
          <div className="text-sm text-muted-foreground">Disclosure Gaps</div>
        </div>
      </div>

      {/* Verdict Breakdown Bar */}
      <div className="mt-6">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="text-muted-foreground">Verdict Distribution</span>
          <span className="text-muted-foreground">
            {summary.pipeline_iterations} iteration
            {summary.pipeline_iterations > 1 ? "s" : ""}
          </span>
        </div>
        <div className="h-3 rounded-full bg-muted overflow-hidden flex">
          {summary.verdicts_by_type.verified > 0 && (
            <div
              className="bg-green-500 h-full"
              style={{
                width: `${
                  (summary.verdicts_by_type.verified / totalVerdicts) * 100
                }%`,
              }}
              title={`Verified: ${summary.verdicts_by_type.verified}`}
            />
          )}
          {(summary.verdicts_by_type.unverified > 0 ||
            summary.verdicts_by_type.insufficient_evidence > 0) && (
            <div
              className="bg-yellow-500 h-full"
              style={{
                width: `${
                  ((summary.verdicts_by_type.unverified +
                    summary.verdicts_by_type.insufficient_evidence) /
                    totalVerdicts) *
                  100
                }%`,
              }}
              title={`Unverified/Insufficient: ${
                summary.verdicts_by_type.unverified +
                summary.verdicts_by_type.insufficient_evidence
              }`}
            />
          )}
          {summary.verdicts_by_type.contradicted > 0 && (
            <div
              className="bg-red-500 h-full"
              style={{
                width: `${
                  (summary.verdicts_by_type.contradicted / totalVerdicts) * 100
                }%`,
              }}
              title={`Contradicted: ${summary.verdicts_by_type.contradicted}`}
            />
          )}
        </div>
        <div className="flex items-center gap-4 mt-2 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-muted-foreground">
              Verified ({summary.verdicts_by_type.verified})
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-yellow-500" />
            <span className="text-muted-foreground">
              Unverified/Insufficient (
              {summary.verdicts_by_type.unverified +
                summary.verdicts_by_type.insufficient_evidence}
              )
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-muted-foreground">
              Contradicted ({summary.verdicts_by_type.contradicted})
            </span>
          </div>
        </div>
      </div>

      {/* Coverage by Pillar */}
      <div className="mt-6">
        <div className="text-sm text-muted-foreground mb-3">
          Coverage by Pillar
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(summary.coverage_by_pillar).map(
            ([pillar, coverage]) => (
              <div key={pillar} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground capitalize">
                    {pillar.replace(/_/g, " ")}
                  </span>
                  <span className="text-xs font-medium text-foreground">
                    {Math.round(coverage)}%
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                  <div
                    className="bg-green-500 h-full transition-all"
                    style={{ width: `${coverage}%` }}
                  />
                </div>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
