/**
 * Source of Truth Report types.
 * Implements FRD 13.
 */

import type { IFRSPillar } from "./ifrs";

// ============================================================================
// Agent and Verdict Types
// ============================================================================

export type AgentName =
  | "claims"
  | "orchestrator"
  | "geography"
  | "legal"
  | "news_media"
  | "academic"
  | "data_metrics"
  | "judge";

export type VerdictStatus =
  | "verified"
  | "unverified"
  | "contradicted"
  | "insufficient_evidence";

export type ClaimType =
  | "geographic"
  | "quantitative"
  | "legal_governance"
  | "strategic"
  | "environmental";

export type ConfidenceLevel = "high" | "medium" | "low";

export type GapType = "fully_unaddressed" | "partially_addressed";

export type Severity = "high" | "medium" | "low";

// ============================================================================
// Evidence Chain Types
// ============================================================================

export interface EvidenceChainEntry {
  finding_id: string;
  agent_name: AgentName;
  evidence_type: string;
  summary: string;
  supports_claim: boolean | null;
  confidence: ConfidenceLevel | null;
  reasoning: string | null;
  iteration: number;
  created_at: string;
}

// ============================================================================
// IFRS Mapping Types
// ============================================================================

export interface IFRSMappingResponse {
  paragraph_id: string;
  pillar: string;
  relevance: string | null;
}

// ============================================================================
// Claim Response Types
// ============================================================================

export interface ClaimResponse {
  claim_id: string;
  claim_text: string;
  claim_type: ClaimType;
  source_page: number;
  source_location: { source_context?: string } | null;
  ifrs_paragraphs: IFRSMappingResponse[];
  priority: "high" | "medium" | "low";
  agent_reasoning: string | null;
  created_at: string;
}

export interface VerdictResponse {
  verdict_id: string;
  verdict: VerdictStatus;
  reasoning: string;
  ifrs_mapping: Record<string, unknown>[];
  evidence_summary: Record<string, unknown> | null;
  iteration_count: number;
  created_at: string;
}

export interface ClaimWithVerdictResponse {
  claim: ClaimResponse;
  verdict: VerdictResponse | null;
  evidence_chain: EvidenceChainEntry[];
}

// ============================================================================
// Disclosure Gap Types
// ============================================================================

export interface DisclosureGapResponse {
  gap_id: string;
  paragraph_id: string;
  pillar: IFRSPillar;
  gap_type: GapType;
  requirement_text: string;
  missing_requirements: string[];
  materiality_context: string;
  severity: Severity;
  s1_counterpart: string | null;
}

// ============================================================================
// Pillar Section Types
// ============================================================================

export interface PillarSummaryResponse {
  total_claims: number;
  verified_claims: number;
  unverified_claims: number;
  contradicted_claims: number;
  insufficient_evidence_claims: number;
  disclosure_gaps: number;
}

export interface PillarSectionResponse {
  pillar: IFRSPillar;
  pillar_display_name: string;
  claims: ClaimWithVerdictResponse[];
  gaps: DisclosureGapResponse[];
  summary: PillarSummaryResponse;
}

// ============================================================================
// Report Summary Types
// ============================================================================

export interface VerdictBreakdown {
  verified: number;
  unverified: number;
  contradicted: number;
  insufficient_evidence: number;
}

export interface ReportSummaryResponse {
  report_id: string;
  total_claims: number;
  verdicts_by_type: VerdictBreakdown;
  gaps_by_status: Record<GapType, number>;
  pipeline_iterations: number;
  compiled_at: string;
}

// ============================================================================
// Full Report Response
// ============================================================================

export interface SourceOfTruthReportResponse {
  report_id: string;
  filename: string;
  status: string;
  summary: ReportSummaryResponse;
  pillars: Record<IFRSPillar, PillarSectionResponse>;
  compiled_at: string;
}

// ============================================================================
// Paginated Response Types
// ============================================================================

export interface ClaimsListPaginatedResponse {
  claims: ClaimWithVerdictResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface GapsListPaginatedResponse {
  gaps: DisclosureGapResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================================
// Filter Types
// ============================================================================

export interface ReportFilters {
  pillar?: IFRSPillar;
  claimType?: ClaimType;
  verdict?: VerdictStatus;
  agent?: AgentName;
  ifrsSearch?: string;
  gapStatus?: GapType;
}

// ============================================================================
// Agent Color Mapping (FRD 13 Appendix D)
// ============================================================================

export const AGENT_COLORS: Record<AgentName, string> = {
  claims: "#64748b",      // Slate blue
  orchestrator: "#ffffff", // White/silver
  geography: "#16a34a",   // Forest green
  legal: "#9333ea",       // Deep purple
  news_media: "#f59e0b",  // Amber/gold
  academic: "#14b8a6",    // Teal
  data_metrics: "#f97316", // Coral/orange
  judge: "#dc2626",       // Crimson red
};

// ============================================================================
// Verdict Color Mapping (FRD 13 Appendix D)
// ============================================================================

export const VERDICT_COLORS: Record<VerdictStatus, { bg: string; text: string; border: string }> = {
  verified: {
    bg: "bg-green-500/20",
    text: "text-green-400",
    border: "border-green-500",
  },
  unverified: {
    bg: "bg-yellow-500/20",
    text: "text-yellow-400",
    border: "border-yellow-500",
  },
  contradicted: {
    bg: "bg-red-500/20",
    text: "text-red-400",
    border: "border-red-500",
  },
  insufficient_evidence: {
    bg: "bg-yellow-500/20",
    text: "text-yellow-400",
    border: "border-yellow-500",
  },
};

// ============================================================================
// Gap Status Color Mapping (FRD 13 Appendix D)
// ============================================================================

export const GAP_COLORS: Record<GapType, { bg: string; border: string }> = {
  fully_unaddressed: {
    bg: "bg-gray-500/20",
    border: "border-gray-500",
  },
  partially_addressed: {
    bg: "bg-orange-500/20",
    border: "border-orange-500",
  },
};

// ============================================================================
// Pillar Display Information
// ============================================================================

export type PillarIconName = "Building2" | "Target" | "AlertTriangle" | "BarChart3";

export const PILLAR_INFO: Record<IFRSPillar, { displayName: string; icon: PillarIconName; description: string }> = {
  governance: {
    displayName: "Governance",
    icon: "Building2",
    description: "Board oversight, management roles, and accountability structures",
  },
  strategy: {
    displayName: "Strategy",
    icon: "Target",
    description: "Transition plans, resource allocation, and strategic decisions",
  },
  risk_management: {
    displayName: "Risk Management",
    icon: "AlertTriangle",
    description: "Risk identification, assessment, and integration with ERM",
  },
  metrics_targets: {
    displayName: "Metrics & Targets",
    icon: "BarChart3",
    description: "GHG emissions, climate targets, and performance metrics",
  },
};
