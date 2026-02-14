/**
 * Report types for sustainability report analysis.
 */

import type { Claim, ClaimVerdict } from "./claim";
import type { AgentFinding } from "./agent";
import type { DisclosureGap, PillarSummary } from "./ifrs";

export type ReportStatus =
  | "uploaded"
  | "parsing"
  | "embedding"
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

export interface SectionInfo {
  title: string;
  level: number;
  page_start: number;
  page_end: number | null;
  children: SectionInfo[];
}

export interface ContentStructure {
  sections: SectionInfo[];
  table_count: number;
  page_count: number;
  estimated_word_count: number;
}

export interface UploadResponse {
  report_id: string;
  filename: string;
  file_size_bytes: number;
  status: ReportStatus;
  created_at: string;
}

export interface ReportStatusResponse {
  report_id: string;
  filename: string;
  file_size_bytes: number;
  status: ReportStatus;
  page_count: number | null;
  content_structure: ContentStructure | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
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
