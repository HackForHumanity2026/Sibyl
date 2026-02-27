/**
 * AgentDetailSheet — Bottom sheet that slides up when an agent avatar is clicked.
 * Shows the full reasoning stream, findings, and agent-specific content for
 * the selected agent, without blocking the graph above.
 */

import { useEffect, useRef, useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import type { AgentNodeData } from "@/types/dashboard";
import { AGENTS, EGG, AgentMark } from "@/components/AgentVillage";
import type { Agent } from "@/components/AgentVillage";
import { FindingsSummary } from "./FindingsSummary";
import { AgentSpecificDisplay } from "./AgentSpecificDisplay";
import { StatusIndicator } from "./StatusIndicator";
import { getAgentHexColor } from "./layout";

// ─── Lookup ───────────────────────────────────────────────────────────────────

const AGENT_BY_KEY = new Map<string, Agent>(
  AGENTS.map((a) => [a.agentKey, a])
);

// ─── Reasoning Messages ───────────────────────────────────────────────────────

function ReasoningFeed({ messages }: { messages: string[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <p className="text-sm text-[#8b7355] italic">
        No reasoning messages yet — waiting for activity…
      </p>
    );
  }

  return (
    <div ref={scrollRef} className="agent-detail-sheet__reasoning-scroll">
      {messages.map((msg, i) => (
        <div
          key={`${i}-${msg.slice(0, 12)}`}
          className="agent-detail-sheet__reasoning-item"
        >
          <span className="agent-detail-sheet__reasoning-bullet">·</span>
          <span className="agent-detail-sheet__reasoning-text">{msg}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Mini Egg for sheet header ─────────────────────────────────────────────────

function MiniEgg({ agent }: { agent: Agent }) {
  return (
    <motion.div
      animate={{ y: [0, -4, 0] }}
      transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
    >
      <svg viewBox="0 0 100 100" width={48} height={48} aria-hidden>
        <ellipse cx="50" cy="97" rx="22" ry="4" fill="#0003" />
        <path d={EGG} fill={agent.bodyColor} />
        <ellipse cx="35" cy="32" rx="10" ry="6" fill="white" opacity={0.35} transform="rotate(-30 35 32)" />
        <circle cx="37" cy="48" r="8.5" fill={agent.eyeColor} />
        <circle cx="63" cy="48" r="8.5" fill={agent.eyeColor} />
        <circle cx="37" cy="48" r="4.5" fill="white" />
        <circle cx="63" cy="48" r="4.5" fill="white" />
        <circle cx="35" cy="46" r="2" fill={agent.eyeColor} />
        <circle cx="61" cy="46" r="2" fill={agent.eyeColor} />
        <path d="M 38 62 Q 50 70 62 62" stroke={agent.eyeColor} strokeWidth="2.8" fill="none" strokeLinecap="round" />
        <AgentMark type={agent.mark} color={agent.markColor} />
      </svg>
    </motion.div>
  );
}

// ─── Tabs ─────────────────────────────────────────────────────────────────────

type SheetTab = "reasoning" | "findings" | "specific";

// ─── Main Component ───────────────────────────────────────────────────────────

interface AgentDetailSheetProps {
  agentId: string | null;
  nodeData: AgentNodeData | null;
  onClose: () => void;
}

export function AgentDetailSheet({ agentId, nodeData, onClose }: AgentDetailSheetProps) {
  const [tab, setTab] = useState<SheetTab>("reasoning");
  const sheetRef = useRef<HTMLDivElement>(null);

  const agent = agentId ? AGENT_BY_KEY.get(agentId) ?? null : null;
  const hexColor = agentId ? getAgentHexColor(agentId as Parameters<typeof getAgentHexColor>[0]) : "#8b7355";

  // Reset to reasoning tab whenever agent changes
  useEffect(() => {
    setTab("reasoning");
  }, [agentId]);

  // Close on Escape
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === "Escape") onClose();
  }, [onClose]);

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  const hasSpecific = !!nodeData?.agentSpecificContent;
  const hasFindings = (nodeData?.findings?.length ?? 0) > 0;

  // Status label
  const statusLabel = (s: string) => {
    if (s === "working") return "Working…";
    if (s === "completed") return "Completed";
    if (s === "error") return "Error";
    return "Idle";
  };

  return (
    <AnimatePresence>
      {agentId && nodeData && agent && (
        <>
          {/* Backdrop — covers only the lower part; clicking it closes the sheet */}
          <motion.div
            className="agent-detail-sheet__backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Sheet */}
          <motion.div
            ref={sheetRef}
            className="agent-detail-sheet"
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", stiffness: 320, damping: 32 }}
          >
            {/* Drag handle */}
            <div className="agent-detail-sheet__drag-handle" />

            {/* Header */}
            <div className="agent-detail-sheet__header">
              <div className="agent-detail-sheet__agent-info">
                <MiniEgg agent={agent} />
                <div className="agent-detail-sheet__agent-text">
                  <h2 className="agent-detail-sheet__agent-name" style={{ color: hexColor }}>
                    {agent.name}
                  </h2>
                  <p className="agent-detail-sheet__agent-role">{agent.role}</p>
                  <div className="agent-detail-sheet__status-row">
                    <StatusIndicator status={nodeData.status} color={hexColor} />
                    <span className="agent-detail-sheet__status-label">
                      {statusLabel(nodeData.status)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Stats */}
              <div className="agent-detail-sheet__stats">
                <div className="agent-detail-sheet__stat">
                  <span className="agent-detail-sheet__stat-value">{nodeData.claimsCompleted}</span>
                  <span className="agent-detail-sheet__stat-label">of {nodeData.claimsAssigned} claims</span>
                </div>
                <div className="agent-detail-sheet__stat">
                  <span className="agent-detail-sheet__stat-value">{nodeData.findingsCount}</span>
                  <span className="agent-detail-sheet__stat-label">findings</span>
                </div>
              </div>

              {/* Close button */}
              <button
                className="agent-detail-sheet__close"
                onClick={onClose}
                aria-label="Close agent details"
              >
                <X size={16} />
              </button>
            </div>

            {/* Tab bar */}
            <div className="agent-detail-sheet__tabs">
              <button
                className={`agent-detail-sheet__tab ${tab === "reasoning" ? "agent-detail-sheet__tab--active" : ""}`}
                onClick={() => setTab("reasoning")}
                style={tab === "reasoning" ? { borderBottomColor: hexColor, color: hexColor } : {}}
              >
                Reasoning
              </button>
              <button
                className={`agent-detail-sheet__tab ${tab === "findings" ? "agent-detail-sheet__tab--active" : ""}`}
                onClick={() => setTab("findings")}
                style={tab === "findings" ? { borderBottomColor: hexColor, color: hexColor } : {}}
                disabled={!hasFindings}
              >
                Findings
                {hasFindings && (
                  <span className="agent-detail-sheet__tab-badge" style={{ backgroundColor: hexColor }}>
                    {nodeData.findingsCount}
                  </span>
                )}
              </button>
              {hasSpecific && (
                <button
                  className={`agent-detail-sheet__tab ${tab === "specific" ? "agent-detail-sheet__tab--active" : ""}`}
                  onClick={() => setTab("specific")}
                  style={tab === "specific" ? { borderBottomColor: hexColor, color: hexColor } : {}}
                >
                  Details
                </button>
              )}
            </div>

            {/* Tab content */}
            <div className="agent-detail-sheet__content">
              {tab === "reasoning" && (
                <ReasoningFeed messages={nodeData.reasoningStream} />
              )}
              {tab === "findings" && (
                <FindingsSummary findings={nodeData.findings} />
              )}
              {tab === "specific" && nodeData.agentSpecificContent && (
                <AgentSpecificDisplay content={nodeData.agentSpecificContent} />
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
