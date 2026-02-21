/**
 * TypeScript types for the Detective Dashboard (FRD 12).
 */

import type { AgentFinding, AgentName, AgentStatusValue } from "./agent";

// =============================================================================
// Node Data Types
// =============================================================================

export interface AgentNodeData extends Record<string, unknown> {
  agentName: AgentName;
  status: AgentStatusValue;
  claimsAssigned: number;
  claimsCompleted: number;
  findingsCount: number;
  reasoningStream: string[];
  findings: AgentFinding[];
  agentSpecificContent?: AgentSpecificContent;
  expanded: boolean;
}

// =============================================================================
// Edge Data Types
// =============================================================================

export type EdgeType = "claim" | "reinvestigation" | "infoRequest";
export type EdgeVolume = "low" | "medium" | "high";

export interface EdgeMessage {
  id: string;
  claimId?: string;
  claimText?: string;
  requestDescription?: string;
  responseText?: string;
  timestamp: string;
}

export interface ClaimEdgeData extends Record<string, unknown> {
  edgeType: EdgeType;
  claimCount?: number;
  volume: EdgeVolume;
  direction: "forward" | "backward";
  label?: string;
  cycleNumber?: number;
  messages: EdgeMessage[];
  sourceAgentColor?: string;
}

// =============================================================================
// Agent-Specific Content Types
// =============================================================================

export interface SatelliteContent {
  type: "satellite";
  imageReferences: string[];
  location: {
    name: string;
    coordinates: [number, number]; // [lat, lon]
  };
  imageryDate: string;
  beforeDate?: string;
  ndviValues?: {
    min: number;
    max: number;
    mean: number;
  };
  changeMetrics?: Record<string, unknown>;
}

export interface IFRSCoverage {
  pillar: "governance" | "strategy" | "risk_management" | "metrics_targets";
  paragraphsCovered: number;
  paragraphsTotal: number;
  paragraphsPartial: number;
  paragraphsGaps: number;
}

export interface IFRSCoverageContent {
  type: "ifrs_coverage";
  coverage: IFRSCoverage[];
}

export interface ConsistencyCheck {
  id: string;
  checkName: string;
  description: string;
  status: "pass" | "fail" | "pending";
  result?: string;
  details?: string | Record<string, unknown>;
}

export interface ConsistencyChecksContent {
  type: "consistency_checks";
  checks: ConsistencyCheck[];
}

export interface Verdict {
  claimId: string;
  claimText: string;
  verdict: "verified" | "unverified" | "contradicted" | "insufficient_evidence";
  cycleCount: number;
  reasoning: string;
}

export interface VerdictsContent {
  type: "verdicts";
  verdicts: Verdict[];
}

export type AgentSpecificContent =
  | SatelliteContent
  | IFRSCoverageContent
  | ConsistencyChecksContent
  | VerdictsContent;

// =============================================================================
// Graph Selection State Types (UI state for selected/expanded elements)
// =============================================================================

export interface GraphSelectionState {
  expandedNodeId: string | null;
  selectedEdgeId: string | null;
}

// =============================================================================
// Layout Types
// =============================================================================

export interface NodePosition {
  x: number;
  y: number;
}

export const NODE_DIMENSIONS = {
  collapsed: { width: 180, height: 80 },
  expanded: { width: 320, minHeight: 400, maxHeight: 600 },
};
