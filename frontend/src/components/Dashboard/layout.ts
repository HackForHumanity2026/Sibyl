/**
 * Graph layout utilities for the Detective Dashboard.
 * Defines static positions for agent nodes in the React Flow graph.
 */

import type { AgentName } from "@/types/agent";
import type { NodePosition } from "@/types/dashboard";

export const LAYOUT_CONFIG = {
  claimsY: 50,
  orchestratorY: 200,
  specialistsY: 400,
  judgeY: 600,
  nodeSpacing: 150,
  centerX: 400,
};

export const AGENT_POSITIONS: Record<AgentName, NodePosition> = {
  claims: { x: 400, y: LAYOUT_CONFIG.claimsY },
  orchestrator: { x: 400, y: LAYOUT_CONFIG.orchestratorY },
  geography: { x: 100, y: LAYOUT_CONFIG.specialistsY },
  legal: { x: 250, y: LAYOUT_CONFIG.specialistsY },
  news_media: { x: 400, y: LAYOUT_CONFIG.specialistsY },
  academic: { x: 550, y: LAYOUT_CONFIG.specialistsY },
  data_metrics: { x: 700, y: LAYOUT_CONFIG.specialistsY },
  judge: { x: 400, y: LAYOUT_CONFIG.judgeY },
};

export const AGENT_DISPLAY_NAMES: Record<AgentName, string> = {
  claims: "Claims Agent",
  orchestrator: "Orchestrator",
  geography: "Geography Agent",
  legal: "Legal Agent",
  news_media: "News/Media Agent",
  academic: "Academic Agent",
  data_metrics: "Data/Metrics Agent",
  judge: "Judge Agent",
};

export const AGENT_CSS_COLORS: Record<AgentName, string> = {
  claims: "var(--agent-claims)",
  orchestrator: "var(--agent-orchestrator)",
  geography: "var(--agent-geography)",
  legal: "var(--agent-legal)",
  news_media: "var(--agent-news)",
  academic: "var(--agent-academic)",
  data_metrics: "var(--agent-data)",
  judge: "var(--agent-judge)",
};

export const AGENT_HEX_COLORS: Record<AgentName, string> = {
  claims: "#6b8ab8",
  orchestrator: "#d9d9d9",
  geography: "#4d9959",
  legal: "#8b5eb5",
  news_media: "#f5b800",
  academic: "#3d9999",
  data_metrics: "#e67346",
  judge: "#dc4242",
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
