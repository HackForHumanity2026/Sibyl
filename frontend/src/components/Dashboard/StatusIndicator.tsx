/**
 * StatusIndicator - Visual indicator for agent status.
 * Shows pulsing animation for working, checkmark for completed, warning for error.
 */

import { motion } from "framer-motion";
import type { AgentStatusValue } from "@/types/agent";

interface StatusIndicatorProps {
  status: AgentStatusValue;
  color: string;
}

const STATUS_LABELS: Record<AgentStatusValue, string> = {
  idle: "Idle",
  working: "Working",
  completed: "Completed",
  error: "Error",
};

export function StatusIndicator({ status, color }: StatusIndicatorProps) {
  const ariaLabel = `Agent status: ${STATUS_LABELS[status]}`;

  if (status === "working") {
    return (
      <motion.div
        className="status-indicator status-indicator--working"
        style={{ backgroundColor: color }}
        role="status"
        aria-label={ariaLabel}
        animate={{
          scale: [1, 1.3, 1],
          opacity: [1, 0.7, 1],
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
    );
  }

  if (status === "completed") {
    return (
      <div
        className="status-indicator status-indicator--completed"
        role="status"
        aria-label={ariaLabel}
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          aria-hidden="true"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div
        className="status-indicator status-indicator--error"
        role="status"
        aria-label={ariaLabel}
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          aria-hidden="true"
        >
          <line x1="12" y1="9" x2="12" y2="13" />
          <circle cx="12" cy="17" r="1" fill="currentColor" />
        </svg>
      </div>
    );
  }

  // Idle state
  return (
    <div
      className="status-indicator status-indicator--idle"
      style={{ backgroundColor: color }}
      role="status"
      aria-label={ariaLabel}
    />
  );
}
