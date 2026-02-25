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
// Source of Truth Report API (FRD 13)
// ============================================================================

import type {
  SourceOfTruthReportResponse,
  ClaimsListPaginatedResponse,
  GapsListPaginatedResponse,
  ReportSummaryResponse,
  ReportFilters,
  MockSeedResponse,
} from "@/types/sourceOfTruth";

/**
 * Get the full Source of Truth report.
 */
export async function getSourceOfTruthReport(
  reportId: string
): Promise<SourceOfTruthReportResponse> {
  return fetchAPI<SourceOfTruthReportResponse>(`/report/${reportId}`);
}

/**
 * Get claims with filtering and pagination.
 */
export async function getReportClaims(
  reportId: string,
  filters?: ReportFilters,
  page: number = 1,
  pageSize: number = 50
): Promise<ClaimsListPaginatedResponse> {
  const searchParams = new URLSearchParams();
  if (filters?.pillar) searchParams.set("pillar", filters.pillar);
  if (filters?.verdict) searchParams.set("verdict", filters.verdict);
  if (filters?.claimType) searchParams.set("claim_type", filters.claimType);
  if (filters?.agent) searchParams.set("agent", filters.agent);
  searchParams.set("page", String(page));
  searchParams.set("page_size", String(pageSize));

  const queryString = searchParams.toString();
  return fetchAPI<ClaimsListPaginatedResponse>(
    `/report/${reportId}/claims?${queryString}`
  );
}

/**
 * Get disclosure gaps with filtering and pagination.
 */
export async function getReportGaps(
  reportId: string,
  filters?: { pillar?: string; gapStatus?: string },
  page: number = 1,
  pageSize: number = 50
): Promise<GapsListPaginatedResponse> {
  const searchParams = new URLSearchParams();
  if (filters?.pillar) searchParams.set("pillar", filters.pillar);
  if (filters?.gapStatus) searchParams.set("gap_status", filters.gapStatus);
  searchParams.set("page", String(page));
  searchParams.set("page_size", String(pageSize));

  const queryString = searchParams.toString();
  return fetchAPI<GapsListPaginatedResponse>(
    `/report/${reportId}/gaps?${queryString}`
  );
}

/**
 * Get report summary statistics only.
 */
export async function getReportSummary(
  reportId: string
): Promise<ReportSummaryResponse> {
  return fetchAPI<ReportSummaryResponse>(`/report/${reportId}/summary`);
}

/**
 * Create a mock report record (dev only).
 */
export async function createMockReport(): Promise<{
  report_id: string;
  message: string;
}> {
  return fetchAPI<{ report_id: string; message: string }>(`/report/mock`, {
    method: "POST",
  });
}

/**
 * Seed mock data into an existing report (dev only).
 */
export async function seedMockReport(
  reportId: string
): Promise<MockSeedResponse> {
  return fetchAPI<MockSeedResponse>(`/report/${reportId}/seed-mock`, {
    method: "POST",
  });
}

/**
 * List all reports in the system.
 */
export async function listReports(): Promise<
  Array<{
    report_id: string;
    filename: string;
    status: string;
    file_size_bytes: number;
    page_count: number | null;
    created_at: string;
    updated_at: string;
  }>
> {
  return fetchAPI<
    Array<{
      report_id: string;
      filename: string;
      status: string;
      file_size_bytes: number;
      page_count: number | null;
      created_at: string;
      updated_at: string;
    }>
  >(`/report/`);
}

// ============================================================================
// Chat API (FRD 14)
// ============================================================================

import type { ConversationHistoryResponse } from "@/types/chat";

/**
 * Get conversation history for a report.
 */
export async function getChatHistory(reportId: string): Promise<ConversationHistoryResponse> {
  return fetchAPI<ConversationHistoryResponse>(`/chat/${reportId}/history`);
}

/**
 * Send a chat message URL (for SSE streaming).
 * Returns the URL to use with EventSource or fetch streaming.
 */
export function getChatMessageUrl(reportId: string): string {
  return `${API_BASE}/chat/${reportId}/message`;
}

