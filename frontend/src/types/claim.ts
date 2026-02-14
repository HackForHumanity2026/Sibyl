/**
 * Claim types for sustainability report verification.
 * Implements FRD 3 Section 8.2.
 */

export type ClaimType =
  | "geographic"
  | "quantitative"
  | "legal_governance"
  | "strategic"
  | "environmental";

export type ClaimPriority = "high" | "medium" | "low";

export type ClaimVerdictStatus =
  | "verified"
  | "unverified"
  | "contradicted"
  | "insufficient_evidence";

/**
 * IFRS paragraph mapping with relevance explanation.
 */
export interface IFRSMapping {
  paragraph_id: string;
  pillar: string;
  relevance: string;
}

/**
 * Source location with context for PDF highlighting.
 */
export interface SourceLocation {
  source_context: string;
}

/**
 * A verifiable sustainability claim extracted from a report.
 */
export interface Claim {
  id: string;
  claim_text: string;
  claim_type: ClaimType;
  source_page: number;
  source_location: SourceLocation | null;
  ifrs_paragraphs: IFRSMapping[];
  priority: ClaimPriority;
  agent_reasoning: string | null;
  created_at: string;
}

/**
 * Response for analysis status polling.
 */
export interface AnalysisStatusResponse {
  report_id: string;
  status: string;
  claims_count: number;
  claims_by_type: Record<ClaimType, number>;
  claims_by_priority: Record<ClaimPriority, number>;
  error_message: string | null;
  updated_at: string;
}

/**
 * Paginated response for claims list.
 */
export interface ClaimsListResponse {
  claims: Claim[];
  total: number;
  page: number;
  size: number;
}

/**
 * Response after starting analysis.
 */
export interface StartAnalysisResponse {
  report_id: string;
  status: string;
  message: string;
}

/**
 * Judge Agent's verdict on a claim.
 */
export interface ClaimVerdict {
  id: string;
  claimId: string;
  verdict: ClaimVerdictStatus;
  reasoning: string;
  ifrsMapping: IFRSMapping[];
  evidenceSummary: Record<string, unknown>;
  iterationCount: number;
  createdAt: string;
}
