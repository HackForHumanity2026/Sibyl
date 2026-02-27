/**
 * useDashboard hook - Transforms SSE events into React Flow graph state.
 * Horizontal avatar village layout, with selectedAgentId for the bottom sheet.
 *
 * The graph state (nodeDataMap + edges) is cached at the module level keyed by
 * reportId so the bottom sheet reasoning streams survive navigation away and back.
 */

import { useCallback, useEffect, useMemo, useReducer, useState } from "react";
import type { Node, Edge } from "@xyflow/react";
import type { StreamEvent } from "@/services/sse";
import type { AgentName, AgentFinding, EvidenceType } from "@/types/agent";
import type {
  AgentNodeData,
  ClaimEdgeData,
  AgentSpecificContent,
  SatelliteContent,
  VerdictsContent,
  IFRSCoverage,
  ConsistencyCheck,
  Verdict,
} from "@/types/dashboard";
import { AGENT_POSITIONS, getAgentHexColor } from "@/components/Dashboard/layout";

// ─── Module-level graph state cache ──────────────────────────────────────────
// Keyed by reportId. Survives component unmounts so the bottom sheet can still
// show reasoning streams when the user navigates away and comes back.
const graphStateCache = new Map<string, GraphState>();

// =============================================================================
// Types
// =============================================================================

interface GraphState {
  nodeDataMap: Map<AgentName, AgentNodeData>;
  edges: Edge<ClaimEdgeData>[];
  lastProcessedIndex: number;
}

type GraphAction =
  | { type: "PROCESS_EVENTS"; events: StreamEvent[]; startIndex: number }
  | { type: "RESET" };

// Valid verdict values for runtime validation
const VALID_VERDICTS = ["verified", "unverified", "contradicted", "insufficient_evidence"] as const;

function isValidVerdict(v: unknown): v is Verdict["verdict"] {
  return typeof v === "string" && VALID_VERDICTS.includes(v as Verdict["verdict"]);
}

// =============================================================================
// Initial State
// =============================================================================

export const ALL_AGENTS: AgentName[] = [
  "claims",
  "orchestrator",
  "geography",
  "legal",
  "news_media",
  "academic",
  "data_metrics",
  "judge",
];

function createInitialNodeData(agentName: AgentName): AgentNodeData {
  return {
    agentName,
    status: "idle",
    claimsAssigned: 0,
    claimsCompleted: 0,
    findingsCount: 0,
    reasoningStream: [],
    findings: [],
    agentSpecificContent: undefined,
    expanded: false, // kept for type compat but not used in the new UI
  };
}

function createInitialState(): GraphState {
  const nodeDataMap = new Map<AgentName, AgentNodeData>();
  for (const agent of ALL_AGENTS) {
    nodeDataMap.set(agent, createInitialNodeData(agent));
  }
  return {
    nodeDataMap,
    edges: [],
    lastProcessedIndex: -1,
  };
}

// =============================================================================
// Event Processing
// =============================================================================

function processEvent(state: GraphState, event: StreamEvent): GraphState {
  const { event_type, agent_name, data, timestamp } = event;
  const agentName = agent_name as AgentName | null;

  switch (event_type) {
    case "agent_started": {
      if (!agentName) return state;
      const nodeData = state.nodeDataMap.get(agentName);
      if (!nodeData) return state;
      const newMap = new Map(state.nodeDataMap);
      newMap.set(agentName, { ...nodeData, status: "working" });
      return { ...state, nodeDataMap: newMap };
    }

    case "agent_thinking": {
      if (!agentName) return state;
      const nodeData = state.nodeDataMap.get(agentName);
      if (!nodeData) return state;
      const message = (data.message as string) || "Processing...";
      const newMap = new Map(state.nodeDataMap);
      newMap.set(agentName, {
        ...nodeData,
        status: "working",
        reasoningStream: [...nodeData.reasoningStream.slice(-49), message],
      });
      return { ...state, nodeDataMap: newMap };
    }

    case "agent_completed": {
      if (!agentName) return state;
      const nodeData = state.nodeDataMap.get(agentName);
      if (!nodeData) return state;
      const newMap = new Map(state.nodeDataMap);
      newMap.set(agentName, {
        ...nodeData,
        status: "completed",
        claimsCompleted: (data.claims_processed as number) || nodeData.claimsCompleted,
      });
      return { ...state, nodeDataMap: newMap };
    }

    case "claim_routed": {
      const assignedAgents = (data.assigned_agents as string[]) || [];
      const claimId = data.claim_id as string;
      const claimText = data.claim_text as string;

      const newEdges: Edge<ClaimEdgeData>[] = assignedAgents.map((target) => ({
        id: `orchestrator-${target}-${claimId}`,
        source: "orchestrator",
        target,
        type: "claim",
        sourceHandle: null,
        targetHandle: null,
        data: {
          edgeType: "claim",
          volume: "low",
          direction: "forward",
          messages: [{ id: `msg-${claimId}`, claimId, claimText, timestamp }],
          sourceAgentColor: getAgentHexColor("orchestrator"),
        },
      }));

      const orchestratorData = state.nodeDataMap.get("orchestrator");
      if (orchestratorData) {
        const newMap = new Map(state.nodeDataMap);
        newMap.set("orchestrator", {
          ...orchestratorData,
          claimsAssigned: orchestratorData.claimsAssigned + 1,
        });
        for (const target of assignedAgents) {
          const targetData = newMap.get(target as AgentName);
          if (targetData) {
            newMap.set(target as AgentName, {
              ...targetData,
              claimsAssigned: targetData.claimsAssigned + 1,
            });
          }
        }
        return { ...state, nodeDataMap: newMap, edges: mergeEdges(state.edges, newEdges) };
      }
      return { ...state, edges: mergeEdges(state.edges, newEdges) };
    }

    case "evidence_found": {
      if (!agentName) return state;
      const nodeData = state.nodeDataMap.get(agentName);
      if (!nodeData) return state;

      const finding = parseAgentFinding(data, agentName);
      const agentSpecificContent = updateAgentSpecificContent(
        nodeData.agentSpecificContent,
        agentName,
        data
      );

      const newMap = new Map(state.nodeDataMap);
      newMap.set(agentName, {
        ...nodeData,
        findingsCount: nodeData.findingsCount + 1,
        findings: [...nodeData.findings.slice(-19), finding],
        agentSpecificContent,
      });

      const claimId = data.claim_id as string;
      const newEdge: Edge<ClaimEdgeData> = {
        id: `${agentName}-judge-${claimId}-${Date.now()}`,
        source: agentName,
        target: "judge",
        type: "claim",
        data: {
          edgeType: "claim",
          volume: "low",
          direction: "forward",
          messages: [{ id: `evidence-${claimId}`, claimId, timestamp }],
          sourceAgentColor: getAgentHexColor(agentName),
        },
      };

      return { ...state, nodeDataMap: newMap, edges: [...state.edges, newEdge] };
    }

    case "verdict_issued": {
      const judgeData = state.nodeDataMap.get("judge");
      if (!judgeData) return state;

      const verdictValue = isValidVerdict(data.verdict)
        ? data.verdict
        : "insufficient_evidence";

      const verdict: Verdict = {
        claimId: data.claim_id as string,
        claimText: (data.claim_text as string) || "Claim",
        verdict: verdictValue,
        cycleCount: (data.iteration_count as number) || 1,
        reasoning: (data.reasoning as string) || "",
      };

      let agentSpecificContent = judgeData.agentSpecificContent as VerdictsContent | undefined;
      if (!agentSpecificContent || agentSpecificContent.type !== "verdicts") {
        agentSpecificContent = { type: "verdicts", verdicts: [] };
      }

      const newMap = new Map(state.nodeDataMap);
      newMap.set("judge", {
        ...judgeData,
        agentSpecificContent: {
          type: "verdicts",
          verdicts: [...agentSpecificContent.verdicts, verdict],
        },
      });
      return { ...state, nodeDataMap: newMap };
    }

    case "reinvestigation": {
      const cycleNumber = (data.cycle as number) || 2;
      const claimIds = (data.claim_ids as string[]) || [];

      const newEdge: Edge<ClaimEdgeData> = {
        id: `reinvestigation-${cycleNumber}-${Date.now()}`,
        source: "judge",
        target: "orchestrator",
        type: "reinvestigation",
        data: {
          edgeType: "reinvestigation",
          volume: "medium",
          direction: "backward",
          cycleNumber,
          label: `Cycle ${cycleNumber}`,
          messages: [{
            id: `reinv-${cycleNumber}`,
            requestDescription: `Re-investigation for ${claimIds.length} claims`,
            timestamp,
          }],
          sourceAgentColor: getAgentHexColor("judge"),
        },
      };

      const orchestratorData = state.nodeDataMap.get("orchestrator");
      if (orchestratorData) {
        const newMap = new Map(state.nodeDataMap);
        newMap.set("orchestrator", { ...orchestratorData, status: "working" });
        return { ...state, nodeDataMap: newMap, edges: [...state.edges, newEdge] };
      }
      return { ...state, edges: [...state.edges, newEdge] };
    }

    case "info_request_routed": {
      const requestingAgent = data.requesting_agent as AgentName;
      const targetAgents = (data.target_agents as string[]) || [];
      const description = data.description as string;

      const newEdges: Edge<ClaimEdgeData>[] = [];
      newEdges.push({
        id: `info-req-${requestingAgent}-orchestrator-${Date.now()}`,
        source: requestingAgent,
        target: "orchestrator",
        type: "infoRequest",
        data: {
          edgeType: "infoRequest",
          volume: "low",
          direction: "forward",
          label: "Info Request",
          messages: [{ id: `req-${Date.now()}`, requestDescription: description, timestamp }],
          sourceAgentColor: getAgentHexColor(requestingAgent),
        },
      });
      for (const target of targetAgents) {
        newEdges.push({
          id: `info-req-orchestrator-${target}-${Date.now()}`,
          source: "orchestrator",
          target,
          type: "infoRequest",
          data: {
            edgeType: "infoRequest",
            volume: "low",
            direction: "forward",
            label: description?.slice(0, 20) || "Request",
            messages: [],
            sourceAgentColor: getAgentHexColor("orchestrator"),
          },
        });
      }
      return { ...state, edges: [...state.edges, ...newEdges] };
    }

    case "info_response_posted": {
      const respondingAgent = data.responding_agent as AgentName;
      const nodeData = state.nodeDataMap.get(respondingAgent);
      if (!nodeData) return state;
      const response = data.response as string;
      const newMap = new Map(state.nodeDataMap);
      newMap.set(respondingAgent, {
        ...nodeData,
        reasoningStream: [
          ...nodeData.reasoningStream.slice(-49),
          `Response: ${response?.slice(0, 80)}...`,
        ],
      });
      return { ...state, nodeDataMap: newMap };
    }

    case "pipeline_completed": {
      const newMap = new Map(state.nodeDataMap);
      for (const [agent, nodeData] of newMap) {
        if (nodeData.status === "working") {
          newMap.set(agent, { ...nodeData, status: "completed" });
        }
      }
      return { ...state, nodeDataMap: newMap };
    }

    case "error": {
      if (!agentName) return state;
      const nodeData = state.nodeDataMap.get(agentName);
      if (!nodeData) return state;
      const newMap = new Map(state.nodeDataMap);
      newMap.set(agentName, { ...nodeData, status: "error" });
      return { ...state, nodeDataMap: newMap };
    }

    default:
      return state;
  }
}

function graphReducer(state: GraphState, action: GraphAction): GraphState {
  switch (action.type) {
    case "PROCESS_EVENTS": {
      let newState = state;
      for (let i = action.startIndex; i < action.events.length; i++) {
        newState = processEvent(newState, action.events[i]);
      }
      return { ...newState, lastProcessedIndex: action.events.length - 1 };
    }
    case "RESET":
      return createInitialState();
    default:
      return state;
  }
}

// =============================================================================
// Helpers
// =============================================================================

function mergeEdges(
  existing: Edge<ClaimEdgeData>[],
  newEdges: Edge<ClaimEdgeData>[]
): Edge<ClaimEdgeData>[] {
  const edgeMap = new Map<string, Edge<ClaimEdgeData>>();
  for (const edge of existing) edgeMap.set(edge.id, edge);
  for (const edge of newEdges) {
    const existingEdge = edgeMap.get(edge.id);
    if (existingEdge?.data && edge.data) {
      edgeMap.set(edge.id, {
        ...existingEdge,
        data: {
          ...existingEdge.data,
          messages: [...(existingEdge.data.messages || []), ...(edge.data.messages || [])],
          volume: getVolumeFromCount(
            (existingEdge.data.messages?.length || 0) + (edge.data.messages?.length || 0)
          ),
        },
      });
    } else {
      edgeMap.set(edge.id, edge);
    }
  }
  return Array.from(edgeMap.values());
}

function getVolumeFromCount(count: number): "low" | "medium" | "high" {
  if (count >= 10) return "high";
  if (count >= 5) return "medium";
  return "low";
}

function parseAgentFinding(data: Record<string, unknown>, agentName: AgentName): AgentFinding {
  const evidenceType = (data.evidence_type as EvidenceType) || "quantitative_check";
  return {
    id: (data.finding_id as string) || `finding-${Date.now()}`,
    agentName,
    claimId: (data.claim_id as string) || "",
    evidenceType,
    summary: (data.summary as string) || "",
    details: (data.details as Record<string, unknown>) || {},
    supportsClaim: data.supports_claim as boolean | null,
    confidence: (data.confidence as "high" | "medium" | "low") || null,
    iteration: (data.iteration as number) || 1,
    createdAt: new Date().toISOString(),
  };
}

function updateAgentSpecificContent(
  current: AgentSpecificContent | undefined,
  agentName: AgentName,
  eventData: Record<string, unknown>
): AgentSpecificContent | undefined {
  const details = eventData.details as Record<string, unknown> | undefined;
  if (!details) return current;

  switch (agentName) {
    case "geography": {
      const imageRefs = details.image_references as string[] | undefined;
      const location = details.location as { name: string; coordinates: [number, number] } | undefined;
      const imageryDates = details.imagery_dates as string[] | undefined;
      if (location) {
        return {
          type: "satellite",
          imageReferences: imageRefs || [],
          location,
          imageryDate: imageryDates?.[0] || new Date().toISOString().slice(0, 10),
          ndviValues: details.ndvi_values as SatelliteContent["ndviValues"],
        };
      }
      return current;
    }

    case "legal": {
      const ifrsMappings = details.ifrs_mappings as Array<Record<string, unknown>> | undefined;
      if (!ifrsMappings) return current;
      const pillarMap = new Map<IFRSCoverage["pillar"], IFRSCoverage>();
      for (const mapping of ifrsMappings) {
        const pillar = (mapping.pillar as IFRSCoverage["pillar"]) || "governance";
        const status = mapping.compliance_status as string;
        let pillarData = pillarMap.get(pillar);
        if (!pillarData) {
          pillarData = { pillar, paragraphsCovered: 0, paragraphsTotal: 0, paragraphsPartial: 0, paragraphsGaps: 0 };
          pillarMap.set(pillar, pillarData);
        }
        pillarData.paragraphsTotal++;
        if (status === "fully_addressed") pillarData.paragraphsCovered++;
        else if (status === "partially_addressed") pillarData.paragraphsPartial++;
        else pillarData.paragraphsGaps++;
      }
      return { type: "ifrs_coverage", coverage: Array.from(pillarMap.values()) };
    }

    case "data_metrics": {
      const checks = details.consistency_checks as Array<Record<string, unknown>> | undefined;
      if (!checks) return current;
      const consistencyChecks: ConsistencyCheck[] = checks.map((check, i) => ({
        id: `check-${i}`,
        checkName: (check.check_name as string) || "Check",
        description: (check.description as string) || "",
        status: (check.status as ConsistencyCheck["status"]) || "pending",
        result: check.result as string | undefined,
        details: check.details as string | undefined,
      }));
      return { type: "consistency_checks", checks: consistencyChecks };
    }

    default:
      return current;
  }
}

// =============================================================================
// Hook
// =============================================================================

export interface UseDashboardReturn {
  nodes: Node<AgentNodeData>[];
  edges: Edge<ClaimEdgeData>[];
  /** Agent id whose detail sheet is currently open */
  selectedAgentId: string | null;
  setSelectedAgentId: (id: string | null) => void;
  isLoading: boolean;
}

export function useDashboard(
  events: StreamEvent[],
  isAnalyzing: boolean,
  reportId?: string
): UseDashboardReturn {
  const [graphState, dispatch] = useReducer(
    graphReducer,
    undefined,
    () => (reportId ? (graphStateCache.get(reportId) ?? createInitialState()) : createInitialState())
  );
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  const handleSetSelectedAgentId = useCallback((id: string | null) => {
    setSelectedAgentId(id);
  }, []);

  // Process new events
  useEffect(() => {
    if (events.length > graphState.lastProcessedIndex + 1) {
      dispatch({
        type: "PROCESS_EVENTS",
        events,
        startIndex: graphState.lastProcessedIndex + 1,
      });
    }
  }, [events, graphState.lastProcessedIndex]);

  // Persist graph state to module-level cache whenever it changes
  useEffect(() => {
    if (reportId) {
      graphStateCache.set(reportId, graphState);
    }
  }, [reportId, graphState]);

  // Reset when starting new analysis
  useEffect(() => {
    if (isAnalyzing && events.length === 0) {
      dispatch({ type: "RESET" });
      setSelectedAgentId(null);
    }
  }, [isAnalyzing, events.length]);

  // Build React Flow nodes from state
  const nodes = useMemo<Node<AgentNodeData>[]>(() => {
    const result: Node<AgentNodeData>[] = [];
    for (const agentName of ALL_AGENTS) {
      const nodeData = graphState.nodeDataMap.get(agentName);
      if (!nodeData) {
        console.warn(`Missing node data for agent: ${agentName}`);
        continue;
      }
      const position = AGENT_POSITIONS[agentName];
      result.push({
        id: agentName,
        type: "agent",
        position,
        data: { ...nodeData, expanded: false },
      });
    }
    return result;
  }, [graphState.nodeDataMap]);

  return {
    nodes,
    edges: graphState.edges,
    selectedAgentId,
    setSelectedAgentId: handleSetSelectedAgentId,
    isLoading: isAnalyzing && events.length === 0,
  };
}
