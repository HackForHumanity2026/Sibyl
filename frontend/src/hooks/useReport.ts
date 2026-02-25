/**
 * Hook for managing Source of Truth report state.
 * Implements FRD 13 Section 12.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getSourceOfTruthReport,
  seedMockReport,
} from "@/services/api";
import type {
  SourceOfTruthReportResponse,
  ClaimWithVerdictResponse,
  DisclosureGapResponse,
  ReportFilters,
} from "@/types/sourceOfTruth";
import type { IFRSPillar } from "@/types/ifrs";

export interface UseReportReturn {
  // Data
  report: SourceOfTruthReportResponse | null;
  loading: boolean;
  error: string | null;

  // Filtered data
  filteredClaims: Record<IFRSPillar, ClaimWithVerdictResponse[]>;
  filteredGaps: Record<IFRSPillar, DisclosureGapResponse[]>;

  // Filters
  filters: ReportFilters;
  setFilters: (filters: ReportFilters) => void;
  clearFilters: () => void;

  // Actions
  refetch: () => Promise<void>;

  // Dev-only mock data actions
  seedMock: () => Promise<void>;
  seedingMock: boolean;
}

const PILLARS: IFRSPillar[] = [
  "governance",
  "strategy",
  "risk_management",
  "metrics_targets",
];

export function useReport(reportId: string | undefined): UseReportReturn {
  // Core state
  const [report, setReport] = useState<SourceOfTruthReportResponse | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [filters, setFilters] = useState<ReportFilters>({});

  // Mock seeding state (dev only)
  const [seedingMock, setSeedingMock] = useState(false);

  // Fetch report
  const fetchReport = useCallback(async () => {
    if (!reportId) return;

    setLoading(true);
    setError(null);

    try {
      const data = await getSourceOfTruthReport(reportId);
      setReport(data);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load report";
      setError(message);
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, [reportId]);

  // Initial fetch and refetch when reportId changes
  useEffect(() => {
    if (reportId) {
      fetchReport();
    }
  }, [reportId, fetchReport]);

  // Apply filters to claims
  const applyFiltersToClaimsGroup = useCallback(
    (claims: ClaimWithVerdictResponse[]): ClaimWithVerdictResponse[] => {
      return claims.filter((item) => {
        // Pillar filter (handled at grouping level, but double-check)
        if (filters.pillar) {
          const claimPillars = item.claim.ifrs_paragraphs.map((p) => p.pillar);
          if (!claimPillars.includes(filters.pillar)) {
            return false;
          }
        }

        // Verdict filter
        if (filters.verdict) {
          if (!item.verdict || item.verdict.verdict !== filters.verdict) {
            return false;
          }
        }

        // Claim type filter
        if (filters.claimType) {
          if (item.claim.claim_type !== filters.claimType) {
            return false;
          }
        }

        // Agent filter
        if (filters.agent) {
          const agentFound = item.evidence_chain.some(
            (e) => e.agent_name === filters.agent
          );
          if (!agentFound) {
            return false;
          }
        }

        // IFRS paragraph search
        if (filters.ifrsSearch) {
          const searchTerm = filters.ifrsSearch.toLowerCase();
          const paragraphMatch = item.claim.ifrs_paragraphs.some((p) =>
            p.paragraph_id.toLowerCase().includes(searchTerm)
          );
          if (!paragraphMatch) {
            return false;
          }
        }

        return true;
      });
    },
    [filters]
  );

  // Apply filters to gaps
  const applyFiltersToGapsGroup = useCallback(
    (gaps: DisclosureGapResponse[]): DisclosureGapResponse[] => {
      return gaps.filter((gap) => {
        // Gap status filter
        if (filters.gapStatus) {
          if (gap.gap_type !== filters.gapStatus) {
            return false;
          }
        }

        // IFRS paragraph search
        if (filters.ifrsSearch) {
          const searchTerm = filters.ifrsSearch.toLowerCase();
          if (!gap.paragraph_id.toLowerCase().includes(searchTerm)) {
            return false;
          }
        }

        return true;
      });
    },
    [filters]
  );

  // Compute filtered claims by pillar
  const filteredClaims = useMemo((): Record<
    IFRSPillar,
    ClaimWithVerdictResponse[]
  > => {
    if (!report) {
      return {
        governance: [],
        strategy: [],
        risk_management: [],
        metrics_targets: [],
      };
    }

    const result: Record<IFRSPillar, ClaimWithVerdictResponse[]> = {
      governance: [],
      strategy: [],
      risk_management: [],
      metrics_targets: [],
    };

    for (const pillar of PILLARS) {
      // If pillar filter is set and doesn't match, skip
      if (filters.pillar && filters.pillar !== pillar) {
        continue;
      }

      const pillarSection = report.pillars[pillar];
      if (pillarSection) {
        result[pillar] = applyFiltersToClaimsGroup(pillarSection.claims);
      }
    }

    return result;
  }, [report, filters, applyFiltersToClaimsGroup]);

  // Compute filtered gaps by pillar
  const filteredGaps = useMemo((): Record<
    IFRSPillar,
    DisclosureGapResponse[]
  > => {
    if (!report) {
      return {
        governance: [],
        strategy: [],
        risk_management: [],
        metrics_targets: [],
      };
    }

    const result: Record<IFRSPillar, DisclosureGapResponse[]> = {
      governance: [],
      strategy: [],
      risk_management: [],
      metrics_targets: [],
    };

    for (const pillar of PILLARS) {
      // If pillar filter is set and doesn't match, skip
      if (filters.pillar && filters.pillar !== pillar) {
        continue;
      }

      const pillarSection = report.pillars[pillar];
      if (pillarSection) {
        result[pillar] = applyFiltersToGapsGroup(pillarSection.gaps);
      }
    }

    return result;
  }, [report, filters, applyFiltersToGapsGroup]);

  // Clear all filters
  const clearFilters = useCallback(() => {
    setFilters({});
  }, []);

  // Seed mock data (dev only)
  const seedMock = useCallback(async () => {
    if (!reportId) return;
    setSeedingMock(true);
    setError(null);
    try {
      await seedMockReport(reportId);
      await fetchReport();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to seed mock data");
    } finally {
      setSeedingMock(false);
    }
  }, [reportId, fetchReport]);

  return {
    report,
    loading,
    error,
    filteredClaims,
    filteredGaps,
    filters,
    setFilters,
    clearFilters,
    refetch: fetchReport,
    seedMock,
    seedingMock,
  };
}
