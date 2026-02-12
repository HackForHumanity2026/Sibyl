/**
 * Claim types for sustainability report verification.
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

export interface SourceLocation {
  page: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Claim {
  id: string;
  reportId: string;
  claimText: string;
  claimType: ClaimType;
  sourcePage: number;
  sourceLocation: SourceLocation | null;
  ifrsParagraphs: string[];
  priority: ClaimPriority;
  agentReasoning: string | null;
  createdAt: string;
  updatedAt: string;
}

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

export interface IFRSMapping {
  paragraph: string;
  status: "compliant" | "non_compliant" | "partial";
}
