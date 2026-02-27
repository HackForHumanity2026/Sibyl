/**
 * EggAvatarNode — Custom React Flow node that renders an egg-shaped agent avatar.
 * Replaces the old rectangular AgentNode with a character-based design.
 * Shows:
 *  - The egg avatar (from AgentVillage) with floating animation
 *  - Agent name + role below
 *  - Most recent reasoning message (crossfade animated)
 *  - Status glow ring (idle/working/completed/error)
 */

import { memo, useState, useEffect } from "react";
import { Handle, Position } from "@xyflow/react";
import { motion, AnimatePresence, useMotionValue, animate } from "framer-motion";
import type { AgentNodeData } from "@/types/dashboard";
import { AGENTS, EGG, AgentMark } from "@/components/AgentVillage";
import type { Agent } from "@/components/AgentVillage";

// Map backend AgentName to the avatar definition
const AGENT_BY_KEY = new Map<string, Agent>(
  AGENTS.map((a) => [a.agentKey, a])
);

interface EggAvatarNodeProps {
  data: AgentNodeData & { onSelect?: (id: string) => void };
  selected?: boolean;
}

/** Status ring colors */
const STATUS_GLOW: Record<string, string> = {
  idle: "transparent",
  working: "#d97706",
  completed: "#10b981",
  error: "#f43f5e",
};

function EggAvatarNodeComponent({ data }: EggAvatarNodeProps) {
  const { agentName, status, reasoningStream, onSelect } = data;
  const [isHovered, setIsHovered] = useState(false);
  const floatY = useMotionValue(0);

  const agent = AGENT_BY_KEY.get(agentName);

  // Continuous float animation separate from hover (prevents snap-back bug)
  useEffect(() => {
    if (!agent) return;
    let cancelled = false;
    const runFloat = async () => {
      if (cancelled) return;
      await animate(floatY, -5, { duration: agent.floatDuration / 2, ease: "easeInOut", delay: agent.floatDelay });
      if (cancelled) return;
      await animate(floatY, 0, { duration: agent.floatDuration / 2, ease: "easeInOut" });
      if (cancelled) return;
      runFloat();
    };
    runFloat();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agent?.floatDelay, agent?.floatDuration]);

  const latestReasoning = reasoningStream[reasoningStream.length - 1] ?? null;
  const glowColor = STATUS_GLOW[status] ?? "transparent";
  const isWorking = status === "working";

  if (!agent) return null;

  return (
    <div className="egg-avatar-node" onClick={() => onSelect?.(agentName)}>
      {/* Left handle — receives edges, pushed inward to avatar border */}
      <Handle
        type="target"
        position={Position.Left}
        className="egg-avatar-node__handle"
        style={{ top: 52, left: 39 }}
      />

      {/* Avatar wrapper with glow ring */}
      <div className="egg-avatar-node__avatar-wrap">
        {/* Status glow ring — behind the avatar */}
        {status !== "idle" && (
          <motion.div
            className="egg-avatar-node__glow-ring"
            style={{ borderColor: glowColor }}
            animate={
              isWorking
                ? { boxShadow: [`0 0 0 0 ${glowColor}44`, `0 0 0 10px ${glowColor}00`] }
                : {}
            }
            transition={isWorking ? { duration: 1.4, repeat: Infinity, ease: "easeOut" } : {}}
          />
        )}

        {/* Egg SVG — float driven by motion value, hover only scales */}
        <motion.div
          style={{ y: floatY, cursor: "pointer" }}
          whileHover={{ scale: 1.1 }}
          onHoverStart={() => setIsHovered(true)}
          onHoverEnd={() => setIsHovered(false)}
        >
          <svg viewBox="0 0 100 100" width={96} height={96} aria-label={`${agent.name} - ${agent.role}`}>
            {/* Shadow */}
            <ellipse cx="50" cy="97" rx="22" ry="4" fill="#0004" />
            {/* Body */}
            <path d={EGG} fill={agent.bodyColor} />
            {/* Shine */}
            <ellipse cx="35" cy="32" rx="10" ry="6" fill="white" opacity={0.35} transform="rotate(-30 35 32)" />

            {/* Eyes */}
            <AnimatePresence mode="wait">
              {isHovered ? (
                <motion.g key="happy" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <path d="M 29 49 Q 37 41 45 49" stroke={agent.eyeColor} strokeWidth="3" fill="none" strokeLinecap="round" />
                  <path d="M 55 49 Q 63 41 71 49" stroke={agent.eyeColor} strokeWidth="3" fill="none" strokeLinecap="round" />
                  <ellipse cx="24" cy="57" rx="9" ry="5.5" fill={agent.blushColor} opacity={0.55} />
                  <ellipse cx="76" cy="57" rx="9" ry="5.5" fill={agent.blushColor} opacity={0.55} />
                </motion.g>
              ) : (
                <motion.g key="neutral" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <circle cx="37" cy="48" r="8.5" fill={agent.eyeColor} />
                  <circle cx="63" cy="48" r="8.5" fill={agent.eyeColor} />
                  <circle cx="37" cy="48" r="4.5" fill="white" />
                  <circle cx="63" cy="48" r="4.5" fill="white" />
                  <circle cx="35" cy="46" r="2" fill={agent.eyeColor} />
                  <circle cx="61" cy="46" r="2" fill={agent.eyeColor} />
                  <circle cx="40" cy="44" r="1.2" fill="white" opacity={0.8} />
                  <circle cx="66" cy="44" r="1.2" fill="white" opacity={0.8} />
                </motion.g>
              )}
            </AnimatePresence>

            {/* Smile */}
            <motion.path
              d={isHovered ? "M 35 64 Q 50 76 65 64" : "M 38 62 Q 50 70 62 62"}
              stroke={agent.eyeColor}
              strokeWidth="2.8"
              fill="none"
              strokeLinecap="round"
              animate={{ d: isHovered ? "M 35 64 Q 50 76 65 64" : "M 38 62 Q 50 70 62 62" }}
              transition={{ duration: 0.15 }}
            />

            {/* Mark */}
            <AgentMark type={agent.mark} color={agent.markColor} />
          </svg>
        </motion.div>
      </div>

      {/* Name + role */}
      <div className="egg-avatar-node__label">
        <span className="egg-avatar-node__name">{agent.name}</span>
        <span className="egg-avatar-node__role">{agent.role}</span>
      </div>

      {/* Reasoning stream — single line crossfade. Static when completed. */}
      <div className="egg-avatar-node__reasoning">
        <AnimatePresence mode="wait">
          {status === "completed" ? (
            /* Completed: show a calm "Done" regardless of reasoning stream */
            <motion.p
              key="completed"
              className="egg-avatar-node__reasoning-text egg-avatar-node__reasoning-text--idle"
              style={{ color: "#10b981" }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              Done
            </motion.p>
          ) : status === "error" ? (
            <motion.p
              key="error"
              className="egg-avatar-node__reasoning-text egg-avatar-node__reasoning-text--idle"
              style={{ color: "#f43f5e" }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              Error
            </motion.p>
          ) : latestReasoning ? (
            <motion.p
              key={latestReasoning}
              className="egg-avatar-node__reasoning-text"
              style={{ color: isWorking ? agent.markColor : "#8b7355" }}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.25 }}
            >
              {latestReasoning.length > 90
                ? latestReasoning.slice(0, 90) + "…"
                : latestReasoning}
            </motion.p>
          ) : (
            <motion.p
              key="idle"
              className="egg-avatar-node__reasoning-text egg-avatar-node__reasoning-text--idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              Waiting…
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      {/* Right handle — sends edges, pushed inward to avatar border */}
      <Handle
        type="source"
        position={Position.Right}
        className="egg-avatar-node__handle"
        style={{ top: 52, right: 39 }}
      />
    </div>
  );
}

export const EggAvatarNode = memo(EggAvatarNodeComponent, (prev, next) => {
  const pd = prev.data;
  const nd = next.data;
  return (
    pd.status === nd.status &&
    pd.reasoningStream === nd.reasoningStream &&
    pd.findingsCount === nd.findingsCount &&
    pd.claimsCompleted === nd.claimsCompleted &&
    pd.agentSpecificContent === nd.agentSpecificContent
  );
});
