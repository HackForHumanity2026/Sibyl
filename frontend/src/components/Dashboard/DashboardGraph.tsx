/**
 * DashboardGraph — Horizontal avatar-based React Flow graph for the Investigation tab.
 *
 * Layout: Claims (Menny) → Orchestrator (Bron) → Pentagon of 5 Specialists → Judge (Vera)
 *
 * The 5 specialists surround a central Message Pool table node.
 * Clicking an avatar opens a bottom sheet with full reasoning + findings.
 */

import { Component, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
// Dynamically imported to avoid hard Vite build errors if not yet installed in container
let confetti: ((opts: Record<string, unknown>) => void) | null = null;
import("canvas-confetti").then((m) => { confetti = m.default as typeof confetti; }).catch(() => {});
import { motion, AnimatePresence } from "framer-motion";
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  ReactFlowProvider,
  useReactFlow,
  type Node,
  type Edge,
  type NodeTypes,
  type EdgeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type { StreamEvent } from "@/services/sse";
import type { AgentNodeData, ClaimEdgeData } from "@/types/dashboard";
import { useDashboard } from "@/hooks/useDashboard";
import { EggAvatarNode } from "./EggAvatarNode";
import { MessagePoolNode } from "./MessagePoolNode";
import { ClaimEdge } from "./ClaimEdge";
import { AgentDetailSheet } from "./AgentDetailSheet";
import { VillageBackground } from "./VillageBackground";
import { AGENTS } from "@/components/AgentVillage";
import { AGENT_POSITIONS, getAgentHexColor } from "./layout";
import "./DashboardGraph.css";

// ─── Error Boundary ──────────────────────────────────────────────────────────

interface ErrorBoundaryProps { children: ReactNode }
interface ErrorBoundaryState { hasError: boolean; error: Error | null }

class DashboardErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: Error) { return { hasError: true, error }; }
  render() {
    if (this.state.hasError) {
      return (
        <div className="dashboard-graph dashboard-graph--empty">
          <div className="dashboard-graph__placeholder">
            <p className="dashboard-graph__title">Graph error</p>
            <p className="dashboard-graph__description">{this.state.error?.message}</p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// ─── Node / Edge type maps ───────────────────────────────────────────────────

const nodeTypes: NodeTypes = {
  agent: EggAvatarNode,
  messagePool: MessagePoolNode,
};
const edgeTypes: EdgeTypes = {
  claim: ClaimEdge,
  reinvestigation: ClaimEdge,
  infoRequest: ClaimEdge,
};

// ─── Agent Navigator Bar ─────────────────────────────────────────────────────

interface AgentNavBarProps {
  nodes: Node<AgentNodeData>[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

/** Small status-dot thumbnails at the bottom of the graph canvas. */
function AgentNavBar({ nodes, selectedId, onSelect }: AgentNavBarProps) {
  // Only show actual agent nodes, not the messagePool node
  const agentNodes = nodes.filter((n) => n.type === "agent");
  return (
    <div className="agent-nav-bar">
      <span className="agent-nav-bar__label">Click to inspect</span>
      <div className="agent-nav-bar__agents">
        {agentNodes.map((node) => {
          const agentDef = AGENTS.find((a) => a.agentKey === node.id);
          const hexColor = getAgentHexColor(node.id as Parameters<typeof getAgentHexColor>[0]);
          const isSelected = selectedId === node.id;
          const isWorking = node.data.status === "working";
          return (
            <button
              key={node.id}
              className={`agent-nav-bar__item ${isSelected ? "agent-nav-bar__item--selected" : ""}`}
              onClick={() => onSelect(node.id)}
              title={agentDef?.name ?? node.id}
              style={{
                borderColor: isSelected || isWorking ? hexColor : "transparent",
                boxShadow: isWorking ? `0 0 0 2px ${hexColor}44` : undefined,
              }}
            >
              {/* Tiny egg */}
              <svg viewBox="0 0 100 100" width={20} height={20} aria-hidden>
                <path
                  d="M 50 12 C 78 12, 90 35, 90 57 C 90 79, 73 90, 50 90 C 27 90, 10 79, 10 57 C 10 35, 22 12, 50 12 Z"
                  fill={agentDef?.bodyColor ?? "#eddfc8"}
                />
                <circle cx="37" cy="48" r="7" fill={agentDef?.eyeColor ?? "#4a3c2e"} />
                <circle cx="63" cy="48" r="7" fill={agentDef?.eyeColor ?? "#4a3c2e"} />
                <circle cx="37" cy="48" r="3.5" fill="white" />
                <circle cx="63" cy="48" r="3.5" fill="white" />
              </svg>

              {/* Status dot */}
              <span
                className={`agent-nav-bar__dot ${isWorking ? "agent-nav-bar__dot--pulse" : ""}`}
                style={{ backgroundColor: hexColor }}
              />

              <span className="agent-nav-bar__name">{agentDef?.name ?? node.id}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ─── Inner graph (inside ReactFlowProvider) ──────────────────────────────────

interface DashboardGraphInnerProps {
  nodes: Node[];
  edges: Edge<ClaimEdgeData>[];
  selectedAgentId: string | null;
  onAgentSelect: (id: string | null) => void;
}

function DashboardGraphInner({
  nodes,
  edges,
  selectedAgentId: _selectedAgentId,
  onAgentSelect,
}: DashboardGraphInnerProps) {
  const { fitView } = useReactFlow();

  // Re-fit view whenever nodes first become populated (fitView on mount runs before nodes load)
  const hasFittedRef = useRef(false);
  useEffect(() => {
    if (nodes.length > 0 && !hasFittedRef.current) {
      hasFittedRef.current = true;
      // Small delay to ensure the canvas has measured itself
      const raf = requestAnimationFrame(() => fitView({ padding: 0.04, duration: 300 }));
      return () => cancelAnimationFrame(raf);
    }
  }, [nodes.length, fitView]);

  // Inject the onSelect callback into agent nodes only
  const nodesWithCallback = useMemo<Node[]>(
    () =>
      nodes.map((n) => {
        if (n.type !== "agent") return n;
        return {
          ...n,
          data: {
            ...(n.data as AgentNodeData),
            onSelect: (id: string) => onAgentSelect(id),
          },
        };
      }),
    [nodes, onAgentSelect]
  );

  const handlePaneClick = useCallback(() => {
    onAgentSelect(null);
  }, [onAgentSelect]);

  return (
    <ReactFlow
      nodes={nodesWithCallback}
      edges={edges}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      onPaneClick={handlePaneClick}
      fitView
      fitViewOptions={{ padding: 0.04 }}
      minZoom={0.2}
      maxZoom={2.0}
      defaultViewport={{ x: 0, y: 0, zoom: 0.7 }}
      nodesDraggable={false}
      edgesReconnectable={false}
      nodesConnectable={false}
      proOptions={{ hideAttribution: true }}
    >
      <Background
        color="#e0d4bf"
        gap={40}
        variant={BackgroundVariant.Dots}
        size={1.5}
      />
      <Controls showInteractive={false} />
    </ReactFlow>
  );
}

// ─── Main Export ─────────────────────────────────────────────────────────────

export interface DashboardGraphProps {
  isAnalyzing: boolean;
  events: StreamEvent[];
  isConnected?: boolean;
  error?: string | null;
  pipelineComplete?: boolean;
  reportId?: string;
}

export function DashboardGraph({
  isAnalyzing,
  events,
  isConnected = true,
  error = null,
  pipelineComplete: pipelineCompleteProp,
  reportId,
}: DashboardGraphProps) {
  const { nodes: agentNodes, edges, selectedAgentId, setSelectedAgentId } = useDashboard(events, isAnalyzing, reportId);
  const confettiFiredRef = useRef(false);

  const pipelineComplete = pipelineCompleteProp ?? events.some((e) => e.event_type === "pipeline_completed");

  // Fire confetti once when pipeline completes
  useEffect(() => {
    if (pipelineComplete && !confettiFiredRef.current) {
      confettiFiredRef.current = true;
      confetti?.({ particleCount: 80, angle: 60, spread: 55, origin: { x: 0, y: 0.6 }, colors: ["#d97706", "#10b981", "#4a3c2e", "#f59e0b", "#dc2626"] });
      setTimeout(() => {
        confetti?.({ particleCount: 80, angle: 120, spread: 55, origin: { x: 1, y: 0.6 }, colors: ["#d97706", "#10b981", "#4a3c2e", "#f59e0b", "#dc2626"] });
      }, 200);
    }
  }, [pipelineComplete]);

  // Build the message pool node (injected directly, not from useDashboard)
  // zIndex: -1 so specialist agent nodes always render on top when positions overlap
  const messagePoolNode = useMemo<Node>(() => ({
    id: "message_pool",
    type: "messagePool",
    position: AGENT_POSITIONS["message_pool"],
    data: { events },
    selectable: false,
    focusable: false,
    draggable: false,
    zIndex: -1,
  }), [events]);

  // Combine agent nodes with the pool node
  const allNodes = useMemo<Node[]>(
    () => [...agentNodes, messagePoolNode],
    [agentNodes, messagePoolNode]
  );

  const selectedNodeData = useMemo<AgentNodeData | null>(() => {
    if (!selectedAgentId) return null;
    return agentNodes.find((n) => n.id === selectedAgentId)?.data ?? null;
  }, [agentNodes, selectedAgentId]);

  // Empty / loading state
  if (!isAnalyzing && events.length === 0) {
    return (
      <div className="dashboard-graph dashboard-graph--empty">
        <div className="dashboard-graph__placeholder">
          <p className="dashboard-graph__title">Investigation graph</p>
          <p className="dashboard-graph__description">
            Start an analysis to see the agent village come to life.
          </p>
        </div>
      </div>
    );
  }

  return (
    <DashboardErrorBoundary>
      <ReactFlowProvider>
        <div className="dashboard-graph__wrapper">
          {/* Status banners */}
          {isAnalyzing && !isConnected && (
            <div className="dashboard-graph__status dashboard-graph__status--reconnecting">
              <div className="dashboard-graph__status-spinner" />
              <span>Reconnecting…</span>
            </div>
          )}
          {error && (
            <div className="dashboard-graph__status dashboard-graph__status--error">
              <span>{error}</span>
            </div>
          )}

          {/* Village background — behind canvas */}
          <VillageBackground />

          {/* Main graph canvas */}
          <div className="dashboard-graph">
            <DashboardGraphInner
              nodes={allNodes}
              edges={edges}
              selectedAgentId={selectedAgentId}
              onAgentSelect={setSelectedAgentId}
            />
          </div>

          {/* Agent navigator bar at bottom */}
          <AgentNavBar
            nodes={agentNodes}
            selectedId={selectedAgentId}
            onSelect={setSelectedAgentId}
          />

          {/* Bottom sheet detail panel */}
          <AgentDetailSheet
            agentId={selectedAgentId}
            nodeData={selectedNodeData}
            onClose={() => setSelectedAgentId(null)}
          />
        </div>
      </ReactFlowProvider>
    </DashboardErrorBoundary>
  );
}
