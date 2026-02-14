/**
 * Hook for managing analysis state and polling.
 * Implements FRD 3 Section 7.4.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  getClaims,
  getAnalysisStatus,
  startAnalysis as startAnalysisApi,
} from "@/services/api";
import type {
  AnalysisStatusResponse,
  Claim,
  ClaimPriority,
  ClaimType,
} from "@/types/claim";

export type AnalysisState =
  | "idle"
  | "starting"
  | "analyzing"
  | "complete"
  | "error";

export interface UseAnalysisReturn {
  // State
  analysisState: AnalysisState;
  claims: Claim[];
  claimsCount: number;
  claimsByType: Record<string, number>;
  claimsByPriority: Record<string, number>;
  error: string | null;

  // Actions
  startAnalysis: (reportId: string) => Promise<void>;
  retry: (reportId: string) => Promise<void>;

  // Filters
  typeFilter: ClaimType | null;
  priorityFilter: ClaimPriority | null;
  setTypeFilter: (type: ClaimType | null) => void;
  setPriorityFilter: (priority: ClaimPriority | null) => void;
  filteredClaims: Claim[];
}

const POLLING_INTERVAL_MS = 3000;
const MAX_POLLS = 100;

export function useAnalysis(): UseAnalysisReturn {
  // Core state
  const [analysisState, setAnalysisState] = useState<AnalysisState>("idle");
  const [claims, setClaims] = useState<Claim[]>([]);
  const [claimsCount, setClaimsCount] = useState(0);
  const [claimsByType, setClaimsByType] = useState<Record<string, number>>({});
  const [claimsByPriority, setClaimsByPriority] = useState<
    Record<string, number>
  >({});
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [typeFilter, setTypeFilter] = useState<ClaimType | null>(null);
  const [priorityFilter, setPriorityFilter] = useState<ClaimPriority | null>(
    null
  );

  // Polling refs — use refs for all mutable state the interval touches
  // so callback identities stay stable and don't trigger re-renders.
  const pollCountRef = useRef(0);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingRef = useRef(false);

  // Stop polling — clear interval and reset refs
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    isPollingRef.current = false;
    pollCountRef.current = 0;
  }, []);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  // Fetch claims after analysis completes
  const fetchClaims = useCallback(async (reportId: string) => {
    try {
      const response = await getClaims(reportId, { size: 100 });
      setClaims(response.claims);
    } catch (err) {
      console.error("Failed to fetch claims:", err);
    }
  }, []);

  // Start polling — always clears any existing interval first
  const startPolling = useCallback(
    (reportId: string) => {
      // Guard: clear any existing interval before creating a new one
      stopPolling();

      isPollingRef.current = true;
      pollCountRef.current = 0;

      const poll = async () => {
        // Bail out if polling was stopped between ticks
        if (!isPollingRef.current) return;

        try {
          const status: AnalysisStatusResponse =
            await getAnalysisStatus(reportId);

          setClaimsCount(status.claims_count);
          setClaimsByType(status.claims_by_type || {});
          setClaimsByPriority(status.claims_by_priority || {});

          if (status.status === "completed") {
            setAnalysisState("complete");
            stopPolling();
            await fetchClaims(reportId);
            return;
          }

          if (status.status === "error") {
            setAnalysisState("error");
            setError(status.error_message || "Analysis failed");
            stopPolling();
            return;
          }
        } catch (err) {
          console.error("Failed to poll status:", err);
          // Don't stop polling on transient errors
        }

        pollCountRef.current += 1;
        if (pollCountRef.current >= MAX_POLLS) {
          setAnalysisState("error");
          setError("Analysis timed out after 5 minutes");
          stopPolling();
        }
      };

      // Initial poll immediately
      poll();

      // Set up interval for subsequent polls
      pollIntervalRef.current = setInterval(poll, POLLING_INTERVAL_MS);
    },
    [stopPolling, fetchClaims]
  );

  // Start analysis — stable ref-based wrapper so the identity never changes
  const startAnalysisRef = useRef<(reportId: string) => Promise<void>>();

  startAnalysisRef.current = async (reportId: string) => {
    setError(null);
    setClaims([]);
    setClaimsCount(0);
    setClaimsByType({});
    setClaimsByPriority({});
    setAnalysisState("starting");

    try {
      const response = await startAnalysisApi(reportId);

      if (response.status === "analyzing") {
        setAnalysisState("analyzing");
        startPolling(reportId);
      } else {
        setAnalysisState("error");
        setError("Unexpected response status");
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to start analysis";

      // Already completed (409)
      if (errorMessage.includes("already been completed")) {
        setAnalysisState("complete");
        try {
          const status = await getAnalysisStatus(reportId);
          setClaimsCount(status.claims_count);
          setClaimsByType(status.claims_by_type || {});
          setClaimsByPriority(status.claims_by_priority || {});
        } catch {
          // Ignore status fetch errors
        }
        await fetchClaims(reportId);
        return;
      }

      // Already analyzing (409)
      if (errorMessage.includes("already in progress")) {
        setAnalysisState("analyzing");
        startPolling(reportId);
        return;
      }

      setAnalysisState("error");
      setError(errorMessage);
    }
  };

  // Stable function identity — never changes across renders
  const startAnalysis = useCallback(
    (reportId: string) => startAnalysisRef.current!(reportId),
    []
  );

  // Retry analysis
  const retry = useCallback(
    async (reportId: string) => {
      stopPolling();
      await startAnalysis(reportId);
    },
    [stopPolling, startAnalysis]
  );

  // Filtered claims
  const filteredClaims = useMemo(
    () =>
      claims.filter((claim) => {
        if (typeFilter && claim.claim_type !== typeFilter) return false;
        if (priorityFilter && claim.priority !== priorityFilter) return false;
        return true;
      }),
    [claims, typeFilter, priorityFilter]
  );

  return {
    analysisState,
    claims,
    claimsCount,
    claimsByType,
    claimsByPriority,
    error,

    startAnalysis,
    retry,

    typeFilter,
    priorityFilter,
    setTypeFilter,
    setPriorityFilter,
    filteredClaims,
  };
}
