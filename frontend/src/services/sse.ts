/**
 * SSE (Server-Sent Events) client service for real-time pipeline updates.
 * Implements FRD 5 Section 11.7.
 */

// API base URL - same as in api.ts
const API_BASE = "http://localhost:8000/api/v1";

/**
 * StreamEvent types as defined by the backend.
 */
export type StreamEventType =
  | "agent_started"
  | "agent_thinking"
  | "agent_completed"
  | "claim_routed"
  | "evidence_found"
  | "verdict_issued"
  | "reinvestigation"
  | "info_request_posted"
  | "info_request_routed"
  | "info_response_posted"
  | "pipeline_completed"
  | "error";

/**
 * A single event from the SSE stream.
 */
export interface StreamEvent {
  event_type: StreamEventType;
  agent_name: string | null;
  data: Record<string, unknown>;
  timestamp: string;
}

/**
 * Parsed SSE message from the stream.
 */
export interface SSEMessage {
  id: number;
  type: StreamEventType;
  event: StreamEvent;
}

/**
 * Create an SSE connection to the analysis stream.
 *
 * @param reportId - The report's unique identifier
 * @param onEvent - Callback for each received event
 * @param onError - Callback for connection errors
 * @param onOpen - Callback when connection opens
 * @returns EventSource instance (call .close() to disconnect)
 */
export function createSSEConnection(
  reportId: string,
  onEvent: (event: StreamEvent, id: number) => void,
  onError: (error: Event) => void,
  onOpen: () => void
): EventSource {
  const url = `${API_BASE}/stream/${reportId}`;
  const eventSource = new EventSource(url);

  eventSource.onopen = onOpen;
  eventSource.onerror = onError;

  // Listen for all event types.
  // NOTE: "error" is handled separately below because the browser's native
  // EventSource fires its own "error" Event when the connection closes/fails.
  // Registering addEventListener("error") would catch both, and the native
  // error Event has no .data property, causing JSON.parse(undefined) to throw.
  const eventTypes: StreamEventType[] = [
    "agent_started",
    "agent_thinking",
    "agent_completed",
    "claim_routed",
    "evidence_found",
    "verdict_issued",
    "reinvestigation",
    "info_request_posted",
    "info_request_routed",
    "info_response_posted",
    "pipeline_completed",
  ];

  for (const eventType of eventTypes) {
    eventSource.addEventListener(eventType, (e: MessageEvent) => {
      try {
        const event: StreamEvent = JSON.parse(e.data);
        const id = parseInt(e.lastEventId, 10) || 0;
        onEvent(event, id);
      } catch (err) {
        console.error("Failed to parse SSE event:", err, e.data);
      }
    });
  }

  // Handle the application "error" event type separately.
  // Only parse if it's a MessageEvent with data (i.e., from the server),
  // ignoring the browser's native connection-error Events.
  eventSource.addEventListener("error", (e: Event) => {
    if (e instanceof MessageEvent && e.data != null) {
      try {
        const event: StreamEvent = JSON.parse(e.data);
        const id = parseInt(e.lastEventId, 10) || 0;
        onEvent(event, id);
      } catch (err) {
        console.error("Failed to parse SSE error event:", err, e.data);
      }
    }
    // Native connection errors are handled by eventSource.onerror above.
  });

  return eventSource;
}

/**
 * Get a human-readable message from a stream event.
 */
export function getEventMessage(event: StreamEvent): string {
  const { event_type, agent_name, data } = event;

  switch (event_type) {
    case "agent_started":
      return `${formatAgentName(agent_name)} started processing...`;
    case "agent_thinking":
      return (data.message as string) || "Thinking...";
    case "agent_completed": {
      const claims = data.claims_processed as number | undefined;
      const findings = data.findings_count as number | undefined;
      if (claims !== undefined && findings !== undefined) {
        return `Completed. ${claims} claims processed, ${findings} findings.`;
      }
      return "Completed.";
    }
    case "claim_routed": {
      const agents = (data.assigned_agents as string[]) || [];
      return `Routed to ${agents.map(formatAgentName).join(", ")}`;
    }
    case "evidence_found":
      return (data.summary as string) || "Evidence found.";
    case "verdict_issued": {
      const verdict = data.verdict as string;
      return `Verdict: ${verdict}`;
    }
    case "reinvestigation": {
      const cycle = data.cycle as number;
      return `Requesting re-investigation (cycle ${cycle})`;
    }
    case "pipeline_completed": {
      const totalClaims = data.total_claims as number;
      const totalVerdicts = data.total_verdicts as number;
      return `Analysis complete. ${totalClaims} claims, ${totalVerdicts} verdicts.`;
    }
    case "error":
      return `Error: ${(data.message as string) || "Unknown error"}`;
    default:
      return event_type;
  }
}

/**
 * Format an agent name for display.
 */
export function formatAgentName(agentName: string | null): string {
  if (!agentName) return "System";

  const nameMap: Record<string, string> = {
    claims: "Claims Agent",
    orchestrator: "Orchestrator",
    geography: "Geography Agent",
    legal: "Legal Agent",
    news_media: "News/Media Agent",
    academic: "Academic Agent",
    data_metrics: "Data/Metrics Agent",
    judge: "Judge Agent",
    compiler: "Report Compiler",
  };

  return nameMap[agentName] || agentName;
}

/**
 * Get the color associated with an agent.
 */
export function getAgentColor(agentName: string | null): string {
  if (!agentName) return "#94a3b8"; // slate-400

  const colorMap: Record<string, string> = {
    claims: "#64748b", // slate blue
    orchestrator: "#e2e8f0", // white/silver
    geography: "#22c55e", // forest green
    legal: "#7c3aed", // deep purple
    news_media: "#f59e0b", // amber/gold
    academic: "#14b8a6", // teal
    data_metrics: "#f97316", // coral/orange
    judge: "#dc2626", // crimson red
    compiler: "#6b7280", // gray
  };

  return colorMap[agentName] || "#94a3b8";
}
