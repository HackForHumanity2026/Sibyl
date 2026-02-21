/**
 * DashboardGraph - Main React Flow network graph visualization.
 * Displays the multi-agent investigation pipeline in real-time.
 */

import { Component, useCallback, useMemo, useState, type ReactNode } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  type Node,
  type Edge,
  type NodeTypes,
  type EdgeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type { StreamEvent } from "@/services/sse";
import type { AgentNodeData, ClaimEdgeData } from "@/types/dashboard";
import { useDashboard } from "@/hooks/useDashboard";
import { AgentNode } from "./AgentNode";
import { ClaimEdge } from "./ClaimEdge";
import { EdgePopover } from "./EdgePopover";
import { getAgentHexColor } from "./layout";
import "./DashboardGraph.css";

// Error Boundary for graceful error handling
interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class DashboardErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error("Dashboard error:", error, errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="dashboard-graph dashboard-graph--error">
          <div className="dashboard-graph__placeholder">
            <svg
              className="dashboard-graph__icon"
              width="64"
              height="64"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <circle cx="12" cy="16" r="1" fill="currentColor" />
            </svg>
            <h3 className="dashboard-graph__title">Dashboard Error</h3>
            <p className="dashboard-graph__description">
              Something went wrong rendering the dashboard.
              {this.state.error?.message && (
                <span className="dashboard-graph__error-detail">
                  {this.state.error.message}
                </span>
              )}
            </p>
            <button
              className="dashboard-graph__retry-button"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const nodeTypes: NodeTypes = {
  agent: AgentNode as any,
};

const edgeTypes: EdgeTypes = {
  claim: ClaimEdge,
  reinvestigation: ClaimEdge,
  infoRequest: ClaimEdge,
};

interface DashboardGraphInnerProps {
  nodes: Node<AgentNodeData>[];
  edges: Edge<ClaimEdgeData>[];
  expandedNodeId: string | null;
  setExpandedNodeId: (id: string | null) => void;
  selectedEdgeId: string | null;
  setSelectedEdgeId: (id: string | null) => void;
}

function DashboardGraphInner({
  nodes,
  edges,
  expandedNodeId,
  setExpandedNodeId,
  selectedEdgeId,
  setSelectedEdgeId,
}: DashboardGraphInnerProps) {
  const [edgePopoverPosition, setEdgePopoverPosition] = useState({ x: 0, y: 0 });

  // Update node data with expansion state (memoized to avoid unnecessary re-renders)
  const nodesWithExpansion = useMemo(
    () =>
      nodes.map((node) => ({
        ...node,
        data: {
          ...node.data,
          expanded: expandedNodeId === node.id,
        },
        selected: expandedNodeId === node.id,
      })),
    [nodes, expandedNodeId]
  );

  // Update edge data with selection state (memoized to avoid unnecessary re-renders)
  const edgesWithSelection = useMemo(
    () =>
      edges.map((edge) => ({
        ...edge,
        selected: selectedEdgeId === edge.id,
      })),
    [edges, selectedEdgeId]
  );

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (expandedNodeId === node.id) {
        setExpandedNodeId(null);
      } else {
        setExpandedNodeId(node.id);
      }
      setSelectedEdgeId(null);
    },
    [expandedNodeId, setExpandedNodeId, setSelectedEdgeId]
  );

  const handleEdgeClick = useCallback(
    (event: React.MouseEvent, edge: Edge) => {
      // Get position relative to .dashboard-graph (the popover's positioned ancestor)
      const container = (event.target as HTMLElement).closest(".dashboard-graph");
      const rect = container?.getBoundingClientRect();
      if (rect) {
        setEdgePopoverPosition({
          x: event.clientX - rect.left,
          y: event.clientY - rect.top,
        });
      }
      setSelectedEdgeId(edge.id);
      setExpandedNodeId(null);
    },
    [setSelectedEdgeId, setExpandedNodeId]
  );

  const handlePaneClick = useCallback(() => {
    setExpandedNodeId(null);
    setSelectedEdgeId(null);
  }, [setExpandedNodeId, setSelectedEdgeId]);

  const selectedEdge = edges.find((e) => e.id === selectedEdgeId) || null;

  // Memoize onClose to prevent EdgePopover effect from re-running every render
  const handleEdgePopoverClose = useCallback(() => {
    setSelectedEdgeId(null);
  }, [setSelectedEdgeId]);

  return (
    <div className="dashboard-graph">
      <ReactFlow
        nodes={nodesWithExpansion}
        edges={edgesWithSelection}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodeClick={handleNodeClick}
        onEdgeClick={handleEdgeClick}
        onPaneClick={handlePaneClick}
        fitView
        minZoom={0.1}
        maxZoom={2.0}
        defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
        nodesDraggable={true}
        edgesReconnectable={false}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#2a2a2a" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={(node) =>
            getAgentHexColor((node.data as AgentNodeData).agentName)
          }
          maskColor="rgba(0, 0, 0, 0.6)"
          style={{ background: "hsl(224, 20%, 12%)" }}
        />
      </ReactFlow>

      {/* Edge popover */}
      <EdgePopover
        edge={selectedEdge}
        position={edgePopoverPosition}
        onClose={handleEdgePopoverClose}
      />
    </div>
  );
}

interface DashboardGraphProps {
  isAnalyzing: boolean;
  events: StreamEvent[];
  isConnected?: boolean;
  error?: string | null;
}

export function DashboardGraph({
  isAnalyzing,
  events,
  isConnected = true,
  error = null,
}: DashboardGraphProps) {
  const {
    nodes,
    edges,
    expandedNodeId,
    setExpandedNodeId,
    selectedEdgeId,
    setSelectedEdgeId,
  } = useDashboard(events, isAnalyzing);

  // Show loading/empty state if no events yet
  if (!isAnalyzing && events.length === 0) {
    return (
      <div className="dashboard-graph dashboard-graph--empty">
        <div className="dashboard-graph__placeholder">
          <svg
            className="dashboard-graph__icon"
            width="64"
            height="64"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <circle cx="12" cy="5" r="2" />
            <circle cx="5" cy="19" r="2" />
            <circle cx="19" cy="19" r="2" />
            <line x1="12" y1="7" x2="12" y2="12" />
            <line x1="12" y1="12" x2="5" y2="17" />
            <line x1="12" y1="12" x2="19" y2="17" />
          </svg>
          <h3 className="dashboard-graph__title">Investigation Dashboard</h3>
          <p className="dashboard-graph__description">
            The multi-agent investigation network will appear here once analysis begins.
          </p>
        </div>
      </div>
    );
  }

  return (
    <DashboardErrorBoundary>
      <ReactFlowProvider>
        <div className="dashboard-graph__wrapper">
          {/* Connection status indicator */}
          {isAnalyzing && !isConnected && (
            <div className="dashboard-graph__status dashboard-graph__status--reconnecting">
              <div className="dashboard-graph__status-spinner" />
              <span>Reconnecting...</span>
            </div>
          )}
          {error && (
            <div className="dashboard-graph__status dashboard-graph__status--error">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <circle cx="12" cy="16" r="1" fill="currentColor" />
              </svg>
              <span>{error}</span>
            </div>
          )}
          <DashboardGraphInner
            nodes={nodes}
            edges={edges}
            expandedNodeId={expandedNodeId}
            setExpandedNodeId={setExpandedNodeId}
            selectedEdgeId={selectedEdgeId}
            setSelectedEdgeId={setSelectedEdgeId}
          />
        </div>
      </ReactFlowProvider>
    </DashboardErrorBoundary>
  );
}
