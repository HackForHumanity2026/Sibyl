/**
 * ComplianceSummary - Arc gauge with hierarchy.
 * Verified % is the hero metric in the gauge centre.
 * Contradicted and Gaps shown smaller underneath.
 * Implements FRD 13 Section 11.
 */

import type { ReportSummaryResponse } from "@/types/sourceOfTruth";

interface ComplianceSummaryProps {
  summary: ReportSummaryResponse;
}

// ============================================================================
// Arc Gauge SVG
// ============================================================================

interface ArcGaugeProps {
  verifiedPct: number;
  unverifiedPct: number;
  contradictedPct: number;
  verifiedCount: number;
  totalClaims: number;
}

function ArcGauge({
  verifiedPct,
  unverifiedPct,
  contradictedPct,
  verifiedCount,
  totalClaims,
}: ArcGaugeProps) {
  // Half-circle from left (180°) to right (0°), radius 80, centre (110, 100)
  const CX = 110;
  const CY = 100;
  const R = 80;
  const STROKE = 16;
  const circumference = Math.PI * R; // arc length of a semicircle

  const arcPath = `M ${CX - R} ${CY} A ${R} ${R} 0 0 1 ${CX + R} ${CY}`;

  const vLen  = verifiedPct     * circumference;
  const uLen  = unverifiedPct   * circumference;
  const cLen  = contradictedPct * circumference;

  const uOffset = -(vLen);
  const cOffset = -(vLen + uLen);

  const verifiedPercent = Math.round(verifiedPct * 100);

  return (
    <svg
      viewBox={`0 0 ${CX * 2} ${CY + 20}`}
      aria-label={`${verifiedPercent}% of claims verified`}
    >
      {/* Track (warm grey) */}
      <path
        d={arcPath}
        stroke="#e8ddd0"
        strokeWidth={STROKE}
        fill="none"
        strokeLinecap="round"
      />

      {/* Unverified / Insufficient — amber */}
      {uLen > 0 && (
        <path
          d={arcPath}
          stroke="#f59e0b"
          strokeWidth={STROKE}
          fill="none"
          strokeLinecap="butt"
          strokeDasharray={`${uLen} ${circumference}`}
          strokeDashoffset={uOffset}
        />
      )}

      {/* Contradicted — rose */}
      {cLen > 0 && (
        <path
          d={arcPath}
          stroke="#f43f5e"
          strokeWidth={STROKE}
          fill="none"
          strokeLinecap="butt"
          strokeDasharray={`${cLen} ${circumference}`}
          strokeDashoffset={cOffset}
        />
      )}

      {/* Verified — emerald (drawn last = on top) */}
      {vLen > 0 && (
        <path
          d={arcPath}
          stroke="#10b981"
          strokeWidth={STROKE}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={`${vLen} ${circumference}`}
        />
      )}

      {/* Centre: percentage */}
      <text
        x={CX}
        y={CY - 14}
        textAnchor="middle"
        fontSize="46"
        fontWeight="700"
        fill="#0f172a"
        fontFamily="ui-sans-serif, system-ui, -apple-system, sans-serif"
      >
        {verifiedPercent}%
      </text>

      {/* Centre: label */}
      <text
        x={CX}
        y={CY + 6}
        textAnchor="middle"
        fontSize="12"
        fill="#6b5344"
        fontFamily="ui-sans-serif, system-ui, -apple-system, sans-serif"
      >
        verified
      </text>

      {/* Left anchor: total claims */}
      <text
        x={CX - R - 4}
        y={CY + 18}
        textAnchor="end"
        fontSize="11"
        fill="#6b5344"
        fontFamily="ui-sans-serif, system-ui, -apple-system, sans-serif"
      >
        {verifiedCount}/{totalClaims}
      </text>

      {/* Right anchor: label */}
      <text
        x={CX + R + 4}
        y={CY + 18}
        textAnchor="start"
        fontSize="11"
        fill="#6b5344"
        fontFamily="ui-sans-serif, system-ui, -apple-system, sans-serif"
      >
        claims
      </text>
    </svg>
  );
}

// ============================================================================
// Stat pill — secondary metrics
// ============================================================================

interface StatPillProps {
  label: string;
  value: number;
  dotColor: string;
}

function StatPill({ label, value, dotColor }: StatPillProps) {
  return (
    <div className="flex items-center gap-2.5 px-4 py-2 rounded-xl bg-[#f5ecdb]">
      <div className={`w-2 h-2 rounded-full shrink-0 ${dotColor}`} />
      <span className="text-xl font-bold text-[#4a3c2e] tabular-nums">{value}</span>
      <span className="text-xs text-[#6b5344] leading-tight">{label}</span>
    </div>
  );
}

// ============================================================================
// Legend row
// ============================================================================

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className={`w-2 h-2 rounded-full ${color}`} />
      <span className="text-xs text-[#6b5344]">{label}</span>
    </div>
  );
}

// ============================================================================
// ComplianceSummary
// ============================================================================

export function ComplianceSummary({ summary }: ComplianceSummaryProps) {
  const totalVerdicts =
    summary.verdicts_by_type.verified +
    summary.verdicts_by_type.unverified +
    summary.verdicts_by_type.contradicted +
    summary.verdicts_by_type.insufficient_evidence;

  const unverifiedCount =
    summary.verdicts_by_type.unverified +
    summary.verdicts_by_type.insufficient_evidence;

  const totalGaps =
    (summary.gaps_by_status.fully_unaddressed || 0) +
    (summary.gaps_by_status.partially_addressed || 0);

  const safe = totalVerdicts > 0 ? totalVerdicts : 1;
  const verifiedPct     = summary.verdicts_by_type.verified / safe;
  const unverifiedPct   = unverifiedCount / safe;
  const contradictedPct = summary.verdicts_by_type.contradicted / safe;

  return (
    <section className="glass-card px-8 py-7 mb-8">
      <h2 className="text-sm font-semibold uppercase tracking-widest text-[#6b5344] mb-6">
        Compliance Summary
      </h2>

      {/* Gauge + secondary stats side-by-side */}
      <div className="flex items-center gap-10">
        {/* Gauge */}
        <div className="w-56 shrink-0">
          <ArcGauge
            verifiedPct={verifiedPct}
            unverifiedPct={unverifiedPct}
            contradictedPct={contradictedPct}
            verifiedCount={summary.verdicts_by_type.verified}
            totalClaims={summary.total_claims}
          />
        </div>

        {/* Secondary metrics */}
        <div className="flex flex-col gap-3 flex-1">
          <StatPill
            label="Total Claims"
            value={summary.total_claims}
            dotColor="bg-[#c8a97a]"
          />
          <StatPill
            label="Contradicted"
            value={summary.verdicts_by_type.contradicted}
            dotColor="bg-rose-400"
          />
          <StatPill
            label="Disclosure Gaps"
            value={totalGaps}
            dotColor="bg-amber-400"
          />
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-5 mt-5 pt-5 border-t border-[#e8ddd0]">
        <LegendItem color="bg-emerald-500" label="Verified" />
        <LegendItem color="bg-amber-400"   label="Unverified / Insufficient" />
        <LegendItem color="bg-rose-400"    label="Contradicted" />
      </div>
    </section>
  );
}
