/**
 * ReasoningMessage - Renders a single event from the agent reasoning stream.
 * Implements FRD 5 Section 11.5.
 */

import { memo } from "react";
import type { StreamEvent } from "@/services/sse";
import { formatAgentName, getAgentColor, getEventMessage } from "@/services/sse";
import "./ReasoningMessage.css";

export interface ReasoningMessageProps {
  event: StreamEvent;
  showAgent?: boolean;
}

/**
 * Format a timestamp as relative time (e.g., "2s ago", "1m ago").
 */
function formatRelativeTime(timestamp: string): string {
  if (!timestamp) return "";

  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);

    if (diffSec < 60) {
      return diffSec <= 1 ? "just now" : `${diffSec}s ago`;
    }

    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) {
      return `${diffMin}m ago`;
    }

    const diffHr = Math.floor(diffMin / 60);
    return `${diffHr}h ago`;
  } catch {
    return "";
  }
}

/**
 * Get the CSS class modifier for the event type.
 */
function getEventTypeClass(eventType: string): string {
  const classMap: Record<string, string> = {
    agent_started: "started",
    agent_thinking: "thinking",
    agent_completed: "completed",
    claim_routed: "routed",
    evidence_found: "evidence",
    verdict_issued: "verdict",
    reinvestigation: "reinvestigation",
    pipeline_completed: "complete",
    error: "error",
  };

  return classMap[eventType] || "default";
}

/**
 * Get verdict badge color.
 */
function getVerdictColor(verdict: string): string {
  const colorMap: Record<string, string> = {
    verified: "#22c55e", // green
    unverified: "#94a3b8", // gray
    contradicted: "#dc2626", // red
    insufficient_evidence: "#f59e0b", // amber
  };

  return colorMap[verdict] || "#94a3b8";
}

export const ReasoningMessage = memo(function ReasoningMessage({
  event,
  showAgent = true,
}: ReasoningMessageProps) {
  const message = getEventMessage(event);
  const agentColor = getAgentColor(event.agent_name);
  const eventClass = getEventTypeClass(event.event_type);
  const timeStr = formatRelativeTime(event.timestamp);

  // Special rendering for verdict events
  if (event.event_type === "verdict_issued") {
    const verdict = event.data.verdict as string;
    const verdictColor = getVerdictColor(verdict);

    return (
      <div className={`reasoning-message reasoning-message--${eventClass}`}>
        <div className="reasoning-message__header">
          {showAgent && (
            <span className="reasoning-message__agent">
              <span
                className="reasoning-message__agent-dot"
                style={{ backgroundColor: agentColor }}
              />
              {formatAgentName(event.agent_name)}
            </span>
          )}
          <span className="reasoning-message__time">{timeStr}</span>
        </div>
        <div className="reasoning-message__content">
          <span className="reasoning-message__text">Verdict: </span>
          <span
            className="reasoning-message__verdict-badge"
            style={{ backgroundColor: verdictColor }}
          >
            {verdict}
          </span>
        </div>
      </div>
    );
  }

  // Special rendering for error events
  if (event.event_type === "error") {
    return (
      <div className={`reasoning-message reasoning-message--${eventClass}`}>
        <div className="reasoning-message__header">
          {showAgent && event.agent_name && (
            <span className="reasoning-message__agent">
              <span
                className="reasoning-message__agent-dot"
                style={{ backgroundColor: agentColor }}
              />
              {formatAgentName(event.agent_name)}
            </span>
          )}
          <span className="reasoning-message__time">{timeStr}</span>
        </div>
        <div className="reasoning-message__content reasoning-message__content--error">
          <svg
            className="reasoning-message__error-icon"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
          <span className="reasoning-message__text">{message}</span>
        </div>
      </div>
    );
  }

  // Special rendering for pipeline_completed
  if (event.event_type === "pipeline_completed") {
    return (
      <div className={`reasoning-message reasoning-message--${eventClass}`}>
        <div className="reasoning-message__header">
          <span className="reasoning-message__agent reasoning-message__agent--system">
            <svg
              className="reasoning-message__complete-icon"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            Pipeline Complete
          </span>
          <span className="reasoning-message__time">{timeStr}</span>
        </div>
        <div className="reasoning-message__content">
          <span className="reasoning-message__text">{message}</span>
        </div>
      </div>
    );
  }

  // Default rendering
  return (
    <div className={`reasoning-message reasoning-message--${eventClass}`}>
      <div className="reasoning-message__header">
        {showAgent && (
          <span className="reasoning-message__agent">
            <span
              className="reasoning-message__agent-dot"
              style={{ backgroundColor: agentColor }}
            />
            {formatAgentName(event.agent_name)}
          </span>
        )}
        <span className="reasoning-message__time">{timeStr}</span>
      </div>
      <div className="reasoning-message__content">
        <span className="reasoning-message__text">{message}</span>
      </div>
    </div>
  );
});
