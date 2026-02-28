/**
 * Graph layout utilities for the Agent Village graph.
 * Defines static positions for egg-avatar nodes in a horizontal React Flow layout:
 *
 *   Claims (left) → Orchestrator → Pentagon of 5 Specialists → Judge (right)
 *
 * The 5 specialists form a pentagon around a central Message Pool table:
 *
 *              geography (top)
 *             /               \
 *        legal                 news_media
 *             \               /
 *         academic       data_metrics
 *                [ TABLE ]
 */

import type { AgentName } from "@/types/agent";
import type { NodePosition } from "@/types/dashboard";

// Pentagon geometry:
// Center of the specialist cluster: (660, 350)
// Radius from center to each specialist: 210px
// The 5 points arranged so the top vertex points up (12 o'clock)
// Standard pentagon angles from top: 0°, 72°, 144°, 216°, 288°

const CLUSTER_CX = 660;   // x-center of the specialist pentagon
const CLUSTER_CY = 350;   // y-center
const CLUSTER_R  = 200;   // radius from center to each specialist node

// Helper: convert polar (angle from top, clockwise) to cartesian
function pentagonPoint(angleDeg: number): { x: number; y: number } {
  const rad = (angleDeg - 90) * (Math.PI / 180); // -90° so 0° = top
  return {
    x: Math.round(CLUSTER_CX + CLUSTER_R * Math.cos(rad)),
    y: Math.round(CLUSTER_CY + CLUSTER_R * Math.sin(rad)),
  };
}

// Five pentagon vertices (clockwise from top)
// geography=top, news_media=upper-right, data_metrics=lower-right,
// academic=lower-left, legal=upper-left
const PENTAGON = {
  geography:    pentagonPoint(0),   // top
  news_media:   pentagonPoint(72),  // upper-right
  data_metrics: pentagonPoint(144), // lower-right
  academic:     pentagonPoint(216), // lower-left
  legal:        pentagonPoint(288), // upper-left
};

export const LAYOUT_CONFIG = {
  claimsX:      80,
  orchestratorX: 280,
  judgeX:       1040,
  centreY:      CLUSTER_CY,
  // Keep these for the reinvestigation swoop calculation
  specialistsX: CLUSTER_CX,
  specialistSpacing: 160,
};

export const AGENT_POSITIONS: Record<AgentName | "message_pool", NodePosition> = {
  claims:       { x: LAYOUT_CONFIG.claimsX,      y: LAYOUT_CONFIG.centreY },
  orchestrator: { x: LAYOUT_CONFIG.orchestratorX, y: LAYOUT_CONFIG.centreY },
  geography:    PENTAGON.geography,
  news_media:   PENTAGON.news_media,
  data_metrics: PENTAGON.data_metrics,
  academic:     PENTAGON.academic,
  legal:        PENTAGON.legal,
  judge:        { x: LAYOUT_CONFIG.judgeX, y: LAYOUT_CONFIG.centreY },
  // Message pool table node.
  // Node positions are top-left anchored; each EggAvatarNode is ~180px wide and ~190px tall,
  // so the visual centroid of the five specialists is shifted to roughly (CLUSTER_CX+90, CLUSTER_CY+100).
  // A 200×100 pool node should have its top-left at centroid minus half its size → (650, 400).
  message_pool: { x: CLUSTER_CX - 10, y: CLUSTER_CY + 50 },
};

export const AGENT_DISPLAY_NAMES: Record<AgentName, string> = {
  claims:       "Menny",
  orchestrator: "Bron",
  geography:    "Columbo",
  legal:        "Mike",
  news_media:   "Izzy",
  academic:     "Newton",
  data_metrics: "Rhea",
  judge:        "Judy",
};

export const AGENT_CSS_COLORS: Record<AgentName, string> = {
  claims:       "var(--agent-claims)",
  orchestrator: "var(--agent-orchestrator)",
  geography:    "var(--agent-geography)",
  legal:        "var(--agent-legal)",
  news_media:   "var(--agent-news)",
  academic:     "var(--agent-academic)",
  data_metrics: "var(--agent-data)",
  judge:        "var(--agent-judge)",
};

export const AGENT_HEX_COLORS: Record<AgentName, string> = {
  claims:       "#ca8a04",
  orchestrator: "#d97706",
  geography:    "#059669",
  legal:        "#2563eb",
  news_media:   "#dc2626",
  academic:     "#7c3aed",
  data_metrics: "#0d9488",
  judge:        "#dc2626",
};

export function getAgentPosition(agentName: AgentName): NodePosition {
  return AGENT_POSITIONS[agentName] || { x: 400, y: 400 };
}

export function getAgentDisplayName(agentName: AgentName): string {
  return AGENT_DISPLAY_NAMES[agentName] || agentName;
}

export function getAgentCSSColor(agentName: AgentName): string {
  return AGENT_CSS_COLORS[agentName] || "var(--muted-foreground)";
}

export function getAgentHexColor(agentName: AgentName): string {
  return AGENT_HEX_COLORS[agentName] || "#94a3b8";
}

const ALL_AGENT_NAMES: AgentName[] = [
  "claims",
  "orchestrator",
  "geography",
  "legal",
  "news_media",
  "academic",
  "data_metrics",
  "judge",
];

export function isAgentName(value: string): value is AgentName {
  return ALL_AGENT_NAMES.includes(value as AgentName);
}
