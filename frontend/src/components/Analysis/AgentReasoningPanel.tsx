/**
 * AgentReasoningPanel - Real-time agent reasoning stream with tabs.
 * Implements FRD 5 Section 11.3-11.4.
 */

import { useCallback, useEffect, useRef, useState, memo } from "react";
import { useNavigate } from "react-router-dom";
import type { StreamEvent } from "@/services/sse";
import { formatAgentName, getAgentColor } from "@/services/sse";
import { ReasoningMessage } from "./ReasoningMessage";
import "./AgentReasoningPanel.css";

export interface AgentReasoningPanelProps {
  /** All events from the SSE stream */
  events: StreamEvent[];
  /** Events grouped by agent name */
  eventsByAgent: Record<string, StreamEvent[]>;
  /** Names of currently active agents */
  activeAgents: string[];
  /** Names of agents that have completed */
  completedAgents: string[];
  /** Names of agents that encountered errors */
  erroredAgents: string[];
  /** Whether the pipeline has completed */
  pipelineComplete: boolean;
  /** Whether the SSE is connected */
  isConnected: boolean;
  /** Report ID to navigate to on completion */
  reportId?: string;
}

/** Agent tab info */
interface AgentTab {
  id: string;
  name: string;
  displayName: string;
  color: string;
  status: "idle" | "active" | "completed" | "error";
  eventCount: number;
}

/** All possible agent IDs in order */
const AGENT_ORDER = [
  "claims",
  "orchestrator",
  "geography",
  "legal",
  "news_media",
  "academic",
  "data_metrics",
  "judge",
];

export const AgentReasoningPanel = memo(function AgentReasoningPanel({
  events,
  eventsByAgent,
  activeAgents,
  completedAgents,
  erroredAgents,
  pipelineComplete,
  isConnected,
  reportId,
}: AgentReasoningPanelProps) {
  const navigate = useNavigate();
  const [selectedAgent, setSelectedAgent] = useState<string>("all");
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const prevEventsLengthRef = useRef(events.length);

  // Build agent tabs from events
  const agentTabs: AgentTab[] = [
    {
      id: "all",
      name: "all",
      displayName: "All",
      color: "#94a3b8",
      status: pipelineComplete ? "completed" : isConnected ? "active" : "idle",
      eventCount: events.length,
    },
  ];

  // Add agent tabs that have events
  for (const agentId of AGENT_ORDER) {
    const agentEvents = eventsByAgent[agentId] || [];
    if (agentEvents.length === 0) continue;

    let status: "idle" | "active" | "completed" | "error" = "idle";
    if (erroredAgents.includes(agentId)) {
      status = "error";
    } else if (completedAgents.includes(agentId)) {
      status = "completed";
    } else if (activeAgents.includes(agentId)) {
      status = "active";
    }

    agentTabs.push({
      id: agentId,
      name: agentId,
      displayName: formatAgentName(agentId),
      color: getAgentColor(agentId),
      status,
      eventCount: agentEvents.length,
    });
  }

  // Get events for the selected tab
  const displayEvents =
    selectedAgent === "all" ? events : eventsByAgent[selectedAgent] || [];

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (
      autoScroll &&
      scrollContainerRef.current &&
      events.length > prevEventsLengthRef.current
    ) {
      scrollContainerRef.current.scrollTop =
        scrollContainerRef.current.scrollHeight;
    }
    prevEventsLengthRef.current = events.length;
  }, [events.length, autoScroll]);

  // Handle scroll to detect user scrolling up
  const handleScroll = useCallback(() => {
    if (!scrollContainerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } =
      scrollContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    setAutoScroll(isAtBottom);
  }, []);

  // Scroll to bottom button
  const scrollToBottom = useCallback(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop =
        scrollContainerRef.current.scrollHeight;
      setAutoScroll(true);
    }
  }, []);

  return (
    <div className="agent-reasoning-panel">
      {/* Agent tabs */}
      <div className="agent-reasoning-panel__tabs">
        {agentTabs.map((tab) => (
          <button
            key={tab.id}
            className={`agent-reasoning-panel__tab ${
              selectedAgent === tab.id
                ? "agent-reasoning-panel__tab--active"
                : ""
            } agent-reasoning-panel__tab--${tab.status}`}
            onClick={() => setSelectedAgent(tab.id)}
            style={
              {
                "--tab-color": tab.color,
              } as React.CSSProperties
            }
          >
            <span
              className={`agent-reasoning-panel__tab-indicator ${
                tab.status === "active"
                  ? "agent-reasoning-panel__tab-indicator--pulsing"
                  : ""
              }`}
              style={{ backgroundColor: tab.color }}
            />
            <span className="agent-reasoning-panel__tab-name">
              {tab.displayName}
            </span>
            {tab.status === "completed" && (
              <svg
                className="agent-reasoning-panel__tab-icon agent-reasoning-panel__tab-icon--check"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            )}
            {tab.status === "error" && (
              <svg
                className="agent-reasoning-panel__tab-icon agent-reasoning-panel__tab-icon--error"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </button>
        ))}
      </div>

      {/* Events stream */}
      <div
        ref={scrollContainerRef}
        className="agent-reasoning-panel__events"
        onScroll={handleScroll}
      >
        {displayEvents.length === 0 ? (
          <div className="agent-reasoning-panel__empty">
            {isConnected ? (
              <>
                <div className="agent-reasoning-panel__spinner" />
                <p>Waiting for agent activity...</p>
              </>
            ) : (
              <p>Connect to see agent reasoning</p>
            )}
          </div>
        ) : (
          <div className="agent-reasoning-panel__messages">
            {displayEvents.map((event, index) => (
              <ReasoningMessage
                key={`${event.timestamp}-${index}`}
                event={event}
                showAgent={selectedAgent === "all"}
              />
            ))}
          </div>
        )}

        {/* Scroll to bottom button */}
        {!autoScroll && displayEvents.length > 0 && (
          <button
            className="agent-reasoning-panel__scroll-btn"
            onClick={scrollToBottom}
          >
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M16.707 10.293a1 1 0 010 1.414l-6 6a1 1 0 01-1.414 0l-6-6a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l4.293-4.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            New events
          </button>
        )}
      </div>

      {/* Connection status / pipeline complete */}
      <div className="agent-reasoning-panel__footer">
        {pipelineComplete ? (
          <button
            onClick={() => reportId && navigate(`/report/${reportId}`)}
            disabled={!reportId}
            className="agent-reasoning-panel__view-report-btn"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" className="agent-reasoning-panel__view-report-icon">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            Pipeline complete — View Report
          </button>
        ) : (
          <span
            className={`agent-reasoning-panel__status ${
              isConnected
                ? "agent-reasoning-panel__status--connected"
                : "agent-reasoning-panel__status--disconnected"
            }`}
          >
            <span className="agent-reasoning-panel__status-dot" />
            {isConnected ? "Connected" : "Disconnected"}
          </span>
        )}
      </div>
    </div>
  );
});
