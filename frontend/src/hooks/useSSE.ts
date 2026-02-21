/**
 * useSSE hook - Real-time pipeline event streaming.
 * Implements FRD 5 Section 11.6.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import {
  createSSEConnection,
  type StreamEvent,
} from "@/services/sse";

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
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pipelineComplete, setPipelineComplete] = useState(false);

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

  // Handle incoming events
  const handleEvent = useCallback((event: StreamEvent, _id: number) => {
    setEvents((prev) => [...prev, event]);

    // Close connection on terminal events to prevent EventSource auto-reconnect
    if (
      event.event_type === "pipeline_completed" ||
      event.event_type === "error"
    ) {
      if (event.event_type === "pipeline_completed") {
        setPipelineComplete(true);
      }
      // Close the connection to prevent the EventSource from
      // auto-reconnecting after the server ends the stream.
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    }
  }, []);

  // Handle connection open
  const handleOpen = useCallback(() => {
    setIsConnected(true);
    setError(null);
  }, []);

  // Handle connection error
  const handleError = useCallback((e: Event) => {
    console.error("SSE connection error:", e);
    setIsConnected(false);
    // Don't set error for normal close
    if ((e.target as EventSource).readyState === EventSource.CLOSED) {
      // Connection closed, might be intentional
    } else {
      setError("Connection error. Will retry...");
    }
  }, []);

  // Clear events
  const clearEvents = useCallback(() => {
    setEvents([]);
    setPipelineComplete(false);
    setError(null);
  }, []);

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

    // Don't connect if not enabled or no reportId
    if (!enabled || !reportId) {
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

    // Cleanup on unmount or dependency change
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
