/**
 * Report types for sustainability report analysis.
 */

import type { Claim, ClaimVerdict } from "./claim";
import type { AgentFinding } from "./agent";
import type { DisclosureGap, PillarSummary } from "./ifrs";

export type ReportStatus =
  | "uploaded"
  | "parsing"
  | "parsed"
  | "analyzing"
  | "completed"
  | "error";

export interface Report {
  id: string;
  filename: string;
  fileSizeBytes: number;
  pageCount: number | null;
  status: ReportStatus;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ContentStructure {
  sections: SectionInfo[];
  tableCount: number;
  chartCount: number;
}

export interface SectionInfo {
  title: string;
  pageStart: number;
  pageEnd: number;
  level: number;
}

export interface SourceOfTruthReport {
  report: Report;
  claims: ClaimWithVerdict[];
  pillarSummaries: PillarSummary[];
  disclosureGaps: DisclosureGap[];
  generatedAt: string;
}

export interface ClaimWithVerdict {
  claim: Claim;
  verdict: ClaimVerdict | null;
  findings: AgentFinding[];
}
