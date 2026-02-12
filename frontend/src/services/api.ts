/**
 * API client for the Sibyl backend.
 */

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
    const error = await response.text();
    throw new Error(`API error: ${response.status} - ${error}`);
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
 * TODO: Implement in FRD 2
 */
export async function uploadReport(_file: File): Promise<{ reportId: string }> {
  // TODO: Implement file upload
  throw new Error("Not implemented - coming in FRD 2");
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
