/**
 * IFRS S1/S2 types for compliance mapping.
 */

export type IFRSPillar =
  | "governance"
  | "strategy"
  | "risk_management"
  | "metrics_targets";

export type ComplianceStatus =
  | "compliant"
  | "non_compliant"
  | "partial"
  | "not_applicable";

export interface IFRSParagraph {
  id: string;
  pillar: IFRSPillar;
  standard: "S1" | "S2";
  number: string;
  title: string;
  description: string;
  subRequirements: string[];
}

export interface DisclosureGap {
  paragraphId: string;
  paragraph: IFRSParagraph;
  gapType: "fully_unaddressed" | "partially_addressed";
  missingRequirements: string[];
  materialityContext: string;
  severity: "high" | "medium" | "low";
}

export interface PillarSummary {
  pillar: IFRSPillar;
  totalClaims: number;
  verifiedClaims: number;
  contradictedClaims: number;
  unverifiedClaims: number;
  insufficientEvidenceClaims: number;
  disclosureGaps: number;
}
