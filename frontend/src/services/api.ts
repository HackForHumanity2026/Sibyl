/**
 * API client for the Sibyl backend.
 * Implements FRD 3 Section 8.3.
 */

import type { ReportStatusResponse, UploadResponse } from "@/types/report";
import type {
  AnalysisStatusResponse,
  Claim,
  ClaimsListResponse,
  ClaimPriority,
  ClaimType,
  StartAnalysisResponse,
} from "@/types/claim";

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

// ============================================================================
// Reports API (FRD 4)
// ============================================================================

/**
 * Get the URL for fetching a report's PDF binary.
 * Used by the PDF viewer component.
 */
export function getPDFUrl(reportId: string): string {
  return `${API_BASE}/reports/${reportId}/pdf`;
}

// ============================================================================
// Analysis API (FRD 3)
// ============================================================================

/**
 * Start claims extraction analysis for a report.
 */
export async function startAnalysis(reportId: string): Promise<StartAnalysisResponse> {
  return fetchAPI<StartAnalysisResponse>(`/analysis/${reportId}/start`, {
    method: "POST",
  });
}

/**
 * Get the analysis status for a report.
 */
export async function getAnalysisStatus(reportId: string): Promise<AnalysisStatusResponse> {
  return fetchAPI<AnalysisStatusResponse>(`/analysis/${reportId}/status`);
}

/**
 * Get paginated list of claims for a report.
 */
export async function getClaims(
  reportId: string,
  params?: {
    type?: ClaimType;
    priority?: ClaimPriority;
    page?: number;
    size?: number;
  }
): Promise<ClaimsListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.type) searchParams.set("type", params.type);
  if (params?.priority) searchParams.set("priority", params.priority);
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.size) searchParams.set("size", String(params.size));

  const queryString = searchParams.toString();
  const endpoint = `/analysis/${reportId}/claims${queryString ? `?${queryString}` : ""}`;

  return fetchAPI<ClaimsListResponse>(endpoint);
}

/**
 * Get a single claim by ID.
 */
export async function getClaim(reportId: string, claimId: string): Promise<Claim> {
  return fetchAPI<Claim>(`/analysis/${reportId}/claims/${claimId}`);
}

// ============================================================================
// Satellite API (FRD 12)
// ============================================================================

/**
 * Get a signed URL for a satellite image from Microsoft Planetary Computer.
 */
export async function getSatelliteImageUrl(stacItemUrl: string): Promise<string> {
  const response = await fetchAPI<{ url: string }>(
    `/satellite/signed-url?stac_item_url=${encodeURIComponent(stacItemUrl)}`
  );
  if (typeof response?.url !== "string") {
    throw new Error("Invalid response from satellite API: missing url field");
  }
  return response.url;
}

// ============================================================================
// Future APIs (stubs)
// ============================================================================

/**
 * Get the Source of Truth report.
 * TODO: Implement in FRD 13
 */
export async function getReport(
  _reportId: string
): Promise<{ report: unknown }> {
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
  throw new Error("Not implemented - coming in FRD 14");
}
