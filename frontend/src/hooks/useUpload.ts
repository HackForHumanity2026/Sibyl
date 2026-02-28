/**
 * Custom hook for managing the PDF upload lifecycle.
 *
 * Implements FRD 2 Section 8 - Frontend Polling and State Management.
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { uploadReport, getReportStatus, retryReport } from "@/services/api";
import type { ReportStatusResponse } from "@/types/report";

export type UploadState = "idle" | "uploading" | "processing" | "complete" | "error";

export interface UseUploadReturn {
  /** Current state of the upload lifecycle */
  uploadState: UploadState;
  /** Report data from the backend (null until upload completes) */
  report: ReportStatusResponse | null;
  /** Error message if upload/processing failed */
  error: string | null;
  /** File being uploaded */
  file: File | null;
  /** Time when upload started */
  startedAt: Date | null;

  /** Start uploading a file */
  uploadFile: (file: File) => Promise<void>;
  /** Retry a failed upload */
  retry: () => Promise<void>;
  /** Reset to idle state */
  reset: () => void;
}

const POLL_INTERVAL_MS = 2000;
const MAX_POLL_COUNT = Infinity; // No timeout - large PDFs can take a while

export function useUpload(): UseUploadReturn {
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [report, setReport] = useState<ReportStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [startedAt, setStartedAt] = useState<Date | null>(null);

  const pollIntervalRef = useRef<number | null>(null);
  const pollCountRef = useRef(0);
  const reportIdRef = useRef<string | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    pollCountRef.current = 0;
  }, []);

  const pollStatus = useCallback(async () => {
    if (!reportIdRef.current) return;

    pollCountRef.current += 1;

    // Check for timeout
    if (pollCountRef.current > MAX_POLL_COUNT) {
      stopPolling();
      setError("Processing timed out. Please try again.");
      setUploadState("error");
      return;
    }

    try {
      const status = await getReportStatus(reportIdRef.current);
      setReport(status);

      if (status.status === "parsed") {
        stopPolling();
        setUploadState("complete");
      } else if (status.status === "error") {
        stopPolling();
        setError(status.error_message || "Processing failed. Please try again.");
        setUploadState("error");
      }
      // Otherwise, continue polling (status is "uploaded", "parsing", or "embedding")
    } catch (err) {
      // Network errors during polling - continue polling
      // Transient network issues shouldn't abort the flow
      console.error("Poll error:", err);
    }
  }, [stopPolling]);

  const startPolling = useCallback(() => {
    pollCountRef.current = 0;
    pollIntervalRef.current = window.setInterval(pollStatus, POLL_INTERVAL_MS);
    // Also poll immediately
    pollStatus();
  }, [pollStatus]);

  const uploadFile = useCallback(async (selectedFile: File) => {
    // Reset state
    setError(null);
    setReport(null);
    setFile(selectedFile);
    setStartedAt(new Date());
    setUploadState("uploading");

    try {
      const response = await uploadReport(selectedFile);
      reportIdRef.current = response.report_id;

      // Transition to processing and start polling
      setUploadState("processing");
      setReport({
        report_id: response.report_id,
        filename: response.filename,
        file_size_bytes: response.file_size_bytes,
        status: response.status,
        page_count: null,
        content_structure: null,
        error_message: null,
        created_at: response.created_at,
        updated_at: response.created_at,
      });

      startPolling();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed";
      setError(message);
      setUploadState("error");
    }
  }, [startPolling]);

  const retry = useCallback(async () => {
    if (!reportIdRef.current) {
      // No report to retry, reset and start fresh
      setError(null);
      setUploadState("idle");
      return;
    }

    setError(null);
    setUploadState("processing");
    setStartedAt(new Date());

    try {
      await retryReport(reportIdRef.current);
      startPolling();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Retry failed";
      setError(message);
      setUploadState("error");
    }
  }, [startPolling]);

  const reset = useCallback(() => {
    stopPolling();
    setUploadState("idle");
    setReport(null);
    setError(null);
    setFile(null);
    setStartedAt(null);
    reportIdRef.current = null;
  }, [stopPolling]);

  return {
    uploadState,
    report,
    error,
    file,
    startedAt,
    uploadFile,
    retry,
    reset,
  };
}
