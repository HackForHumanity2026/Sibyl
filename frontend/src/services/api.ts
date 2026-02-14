/**
 * API client for the Sibyl backend.
 */

import type { ReportStatusResponse, UploadResponse } from "@/types/report";

const API_BASE = "http://localhost:8000/api/v1";

interface HealthResponse {
  status: "healthy" | "degraded";
  database: "connected" | "disconnected";
  redis: "connected" | "disconnected";
  version: string;
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

/**
 * Check the health of the backend services.
 */
export async function healthCheck(): Promise<HealthResponse> {
  return fetchAPI<HealthResponse>("/health");
}

/**
 * Upload a PDF report for analysis.
 */
export async function uploadReport(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
    // Note: Do NOT set Content-Type header; the browser sets it
    // automatically with the correct multipart boundary
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "Upload failed");
  }

  return response.json();
}

/**
 * Get the current status of an uploaded report.
 */
export async function getReportStatus(reportId: string): Promise<ReportStatusResponse> {
  return fetchAPI<ReportStatusResponse>(`/upload/${reportId}/status`);
}

/**
 * Retry processing a failed report.
 */
export async function retryReport(reportId: string): Promise<{ report_id: string; status: string; message: string }> {
  return fetchAPI(`/upload/${reportId}/retry`, {
    method: "POST",
  });
}

/**
 * Get the analysis status for a report.
 * TODO: Implement in FRD 5
 */
export async function getAnalysisStatus(
  _reportId: string
): Promise<{ status: string }> {
  // TODO: Implement status retrieval
  throw new Error("Not implemented - coming in FRD 5");
}

/**
 * Get the Source of Truth report.
 * TODO: Implement in FRD 13
 */
export async function getReport(
  _reportId: string
): Promise<{ report: unknown }> {
  // TODO: Implement report retrieval
  throw new Error("Not implemented - coming in FRD 13");
}

/**
 * Send a chat message to the chatbot.
 * TODO: Implement in FRD 14
 */
export async function sendChatMessage(
  _reportId: string,
  _message: string
): Promise<{ response: string }> {
  // TODO: Implement chat
  throw new Error("Not implemented - coming in FRD 14");
}
