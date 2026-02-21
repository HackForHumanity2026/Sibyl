/**
 * AgentNode - Custom React Flow node for displaying agents.
 * Shows agent status, reasoning stream, findings, and agent-specific content.
 */

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { motion, AnimatePresence } from "framer-motion";
import type { AgentNodeData } from "@/types/dashboard";
import { StatusIndicator } from "./StatusIndicator";
import { ReasoningStream } from "./ReasoningStream";
import { FindingsSummary } from "./FindingsSummary";
import { AgentSpecificDisplay } from "./AgentSpecificDisplay";
import { getAgentDisplayName, getAgentCSSColor, getAgentHexColor } from "./layout";

interface AgentNodeProps {
  data: AgentNodeData;
  selected?: boolean;
}

function AgentNodeComponent({ data, selected }: AgentNodeProps) {
  const {
    agentName,
    status,
    claimsAssigned,
    claimsCompleted,
    findingsCount,
    reasoningStream,
    findings,
    agentSpecificContent,
    expanded,
  } = data;

  const displayName = getAgentDisplayName(agentName);
  const cssColor = getAgentCSSColor(agentName);
  const hexColor = getAgentHexColor(agentName);

  return (
    <motion.div
      className={`agent-node agent-node--${status} ${expanded ? "agent-node--expanded" : ""} ${selected ? "agent-node--selected" : ""}`}
      style={
        {
          "--agent-color": cssColor,
          "--agent-color-hex": hexColor,
          borderColor: hexColor,
        } as React.CSSProperties
      }
      layout
      initial={false}
      animate={{
        width: expanded ? 320 : 180,
        height: expanded ? "auto" : 80,
      }}
      transition={{ duration: 0.2, ease: "easeOut" }}
    >
      {/* Input handle (top) */}
      <Handle
        type="target"
        position={Position.Top}
        className="agent-node__handle"
        style={{ background: hexColor }}
      />

      {/* Header */}
      <div className="agent-node__header">
        <StatusIndicator status={status} color={hexColor} />
        <span className="agent-node__name">{displayName}</span>
      </div>

      {/* Collapsed view */}
      {!expanded && (
        <div className="agent-node__summary">
          <span className="agent-node__stat">
            {claimsCompleted}/{claimsAssigned} claims
          </span>
          <span className="agent-node__stat">{findingsCount} findings</span>
        </div>
      )}

      {/* Expanded view */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            className="agent-node__expanded-content"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
          >
            {/* Stats bar */}
            <div className="agent-node__stats-bar">
              <span className="agent-node__stat-pill">
                Claims: {claimsCompleted}/{claimsAssigned}
              </span>
              <span className="agent-node__stat-pill">
                Findings: {findingsCount}
              </span>
            </div>

            {/* Reasoning stream */}
            <ReasoningStream messages={reasoningStream} />

            {/* Findings summary */}
            <FindingsSummary findings={findings} />

            {/* Agent-specific content */}
            {agentSpecificContent && (
              <AgentSpecificDisplay content={agentSpecificContent} />
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Output handle (bottom) */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="agent-node__handle"
        style={{ background: hexColor }}
      />
    </motion.div>
  );
}

export const AgentNode = memo(AgentNodeComponent, (prev, next) => {
  return (
    prev.data.status === next.data.status &&
    prev.data.expanded === next.data.expanded &&
    prev.data.findingsCount === next.data.findingsCount &&
    prev.data.claimsCompleted === next.data.claimsCompleted &&
    prev.data.claimsAssigned === next.data.claimsAssigned &&
    prev.data.reasoningStream === next.data.reasoningStream &&
    prev.data.findings === next.data.findings &&
    prev.data.agentSpecificContent === next.data.agentSpecificContent &&
    prev.selected === next.selected
  );
});
