/**
 * useSSE hook - Real-time pipeline event streaming.
 * Implements FRD 5 Section 11.6.
 *
 * Events are cached in a module-level Map keyed by reportId so they
 * survive component unmounts (e.g. switching tabs or navigating away
 * and back). The cache is never cleared automatically; clearEvents()
 * removes the cache entry for the current reportId.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import {
  createSSEConnection,
  type StreamEvent,
} from "@/services/sse";

// ─── Module-level event cache ────────────────────────────────────────────────
// Survives React component unmounts so events are available when user returns.
const eventsCache = new Map<string, StreamEvent[]>();
const pipelineCompleteCache = new Set<string>();

export interface UseSSEReturn {
  /** All received events in chronological order */
  events: StreamEvent[];
  /** Events grouped by agent name */
  eventsByAgent: Record<string, StreamEvent[]>;
  /** Whether the SSE connection is open */
  isConnected: boolean;
  /** Connection error message, if any */
  error: string | null;
  /** Names of currently active agents */
  activeAgents: string[];
  /** Names of agents that have completed */
  completedAgents: string[];
  /** Names of agents that encountered errors */
  erroredAgents: string[];
  /** Whether the pipeline has completed */
  pipelineComplete: boolean;
  /** Clear all events */
  clearEvents: () => void;
}

/**
 * Hook for managing SSE connections to the analysis stream.
 *
 * @param reportId - The report's unique identifier
 * @param enabled - Whether to connect (default: true when reportId is provided)
 * @returns SSE state and event data
 */
export function useSSE(
  reportId: string | undefined,
  enabled: boolean = true
): UseSSEReturn {
  // Seed initial state from cache so events are visible immediately on mount
  const [events, setEvents] = useState<StreamEvent[]>(() =>
    reportId ? (eventsCache.get(reportId) ?? []) : []
  );
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pipelineComplete, setPipelineComplete] = useState<boolean>(() =>
    reportId ? pipelineCompleteCache.has(reportId) : false
  );

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Group events by agent
  const eventsByAgent: Record<string, StreamEvent[]> = {};
  for (const event of events) {
    const agentKey = event.agent_name || "system";
    if (!eventsByAgent[agentKey]) {
      eventsByAgent[agentKey] = [];
    }
    eventsByAgent[agentKey].push(event);
  }

  // Derive active/completed/errored agents from events
  const agentStates: Record<
    string,
    { started: boolean; completed: boolean; errored: boolean }
  > = {};

  for (const event of events) {
    if (!event.agent_name) continue;
    const agent = event.agent_name;

    if (!agentStates[agent]) {
      agentStates[agent] = { started: false, completed: false, errored: false };
    }

    if (event.event_type === "agent_started") {
      agentStates[agent].started = true;
      agentStates[agent].completed = false; // Reset on re-start
    } else if (event.event_type === "agent_completed") {
      agentStates[agent].completed = true;
    } else if (event.event_type === "error") {
      agentStates[agent].errored = true;
    }
  }

  const activeAgents = Object.entries(agentStates)
    .filter(([, state]) => state.started && !state.completed && !state.errored)
    .map(([agent]) => agent);

  const completedAgents = Object.entries(agentStates)
    .filter(([, state]) => state.completed)
    .map(([agent]) => agent);

  const erroredAgents = Object.entries(agentStates)
    .filter(([, state]) => state.errored)
    .map(([agent]) => agent);

  // Handle incoming events — updates state AND the module-level cache
  const handleEvent = useCallback(
    (event: StreamEvent, _id: number) => {
      setEvents((prev) => {
        const next = [...prev, event];
        // Persist to module-level cache
        if (reportId) eventsCache.set(reportId, next);
        return next;
      });

      if (event.event_type === "pipeline_completed") {
        setPipelineComplete(true);
        if (reportId) pipelineCompleteCache.add(reportId);
        // Close to prevent auto-reconnect after the server ends the stream
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
      } else if (event.event_type === "error") {
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
      }
    },
    [reportId]
  );

  // Handle connection open
  const handleOpen = useCallback(() => {
    setIsConnected(true);
    setError(null);
  }, []);

  // Handle connection error
  const handleError = useCallback((e: Event) => {
    console.error("SSE connection error:", e);
    setIsConnected(false);
    if ((e.target as EventSource).readyState !== EventSource.CLOSED) {
      setError("Connection error. Will retry...");
    }
  }, []);

  // Clear events for this report (also wipes the cache entry)
  const clearEvents = useCallback(() => {
    setEvents([]);
    setPipelineComplete(false);
    setError(null);
    if (reportId) {
      eventsCache.delete(reportId);
      pipelineCompleteCache.delete(reportId);
    }
  }, [reportId]);

  // When reportId changes, seed state from cache
  useEffect(() => {
    if (reportId) {
      const cached = eventsCache.get(reportId);
      if (cached && cached.length > 0) {
        setEvents(cached);
      }
      if (pipelineCompleteCache.has(reportId)) {
        setPipelineComplete(true);
      }
    }
  }, [reportId]);

  // Connect/disconnect based on reportId and enabled
  useEffect(() => {
    // Cleanup previous connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Don't connect if not enabled or no reportId, or already complete
    if (!enabled || !reportId || pipelineCompleteCache.has(reportId)) {
      setIsConnected(false);
      return;
    }

    // Create new connection
    const eventSource = createSSEConnection(
      reportId,
      handleEvent,
      handleError,
      handleOpen
    );
    eventSourceRef.current = eventSource;

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [reportId, enabled, handleEvent, handleError, handleOpen]);

  return {
    events,
    eventsByAgent,
    isConnected,
    error,
    activeAgents,
    completedAgents,
    erroredAgents,
    pipelineComplete,
    clearEvents,
  };
}
