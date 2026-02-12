/**
 * Agent types for the multi-agent pipeline.
 */

export type AgentName =
  | "claims"
  | "orchestrator"
  | "geography"
  | "legal"
  | "news_media"
  | "academic"
  | "data_metrics"
  | "judge";

export type AgentStatusValue = "idle" | "working" | "completed" | "error";

export type EvidenceType =
  | "satellite_imagery"
  | "legal_analysis"
  | "news_article"
  | "academic_paper"
  | "quantitative_check"
  | "benchmark_comparison";

export type ConfidenceLevel = "high" | "medium" | "low";

export interface AgentStatus {
  agentName: AgentName;
  status: AgentStatusValue;
  claimsAssigned: number;
  claimsCompleted: number;
  errorMessage: string | null;
}

export interface AgentFinding {
  id: string;
  agentName: AgentName;
  claimId: string;
  evidenceType: EvidenceType;
  summary: string;
  details: Record<string, unknown>;
  supportsClaim: boolean | null;
  confidence: ConfidenceLevel | null;
  iteration: number;
  createdAt: string;
}

export interface InfoRequest {
  requestId: string;
  requestingAgent: AgentName;
  description: string;
  context: Record<string, unknown>;
  status: "pending" | "routed" | "responded";
}

export interface InfoResponse {
  requestId: string;
  respondingAgent: AgentName;
  response: string;
  details: Record<string, unknown>;
}
