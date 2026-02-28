/**
 * AgentVillage — cute egg-shaped agent avatars for the HomePage landing section.
 * Hover to see tooltip, click to open detail modal.
 *
 * Key exports (also used by the Investigation graph):
 *   AGENTS, Agent, EGG, AgentMark, EggAvatar, EggAvatarProps
 */

import { useState, useEffect } from "react";
import { motion, AnimatePresence, useMotionValue, animate } from "framer-motion";
import { X } from "lucide-react";
import type { AgentName } from "@/types/agent";

// ─── Agent Definitions ────────────────────────────────────────────────────────

export interface Agent {
  id: string;
  /** Maps to the backend AgentName type for graph lookup */
  agentKey: AgentName;
  name: string;
  role: string;
  shortDesc: string;
  longDesc: string;
  specialTool: string;
  capabilities: string[];
  bodyColor: string;
  eyeColor: string;
  blushColor: string;
  markColor: string;
  floatDelay: number;
  floatDuration: number;
  mark: "crown" | "doc" | "scales" | "chart" | "waves" | "book" | "globe" | "gavel";
}

export const AGENTS: Agent[] = [
  {
    id: "bron",
    agentKey: "orchestrator",
    name: "Bron",
    role: "Orchestrator",
    shortDesc: "Bron runs the whole investigation. He reads every claim, decides which agents to send it to, and waits for their findings before assembling the final verdict. Think of her as the editor-in-chief. Nothing gets published without her sign-off.",
    longDesc:
      "Bron is the conductor of the Agent Collective. He receives each extracted claim, decides which specialist agents should investigate it, coordinates inter-agent information requests, and synthesises all findings into a final verdict. Nothing happens without Bron knowing about it.",
    specialTool: "Multi-agent orchestration framework",
    capabilities: [
      "Claim routing & prioritisation",
      "Inter-agent communication",
      "Pipeline state management",
      "Evidence synthesis",
    ],
    bodyColor: "#fff1d0",
    eyeColor: "#92400e",
    blushColor: "#fcd34d",
    markColor: "#d97706",
    floatDelay: 0,
    floatDuration: 5.2,
    mark: "crown",
  },
  {
    id: "menny",
    agentKey: "claims",
    name: "Menny",
    role: "Claims Extractor",
    shortDesc: "Menny is the first one in. He reads the entire report and pulls out every statement that can actually be checked — targets, commitments, governance claims, risk disclosures. Without Menny, there's nothing to investigate.",
    longDesc:
      "Menny tears through the sustainability report page by page, flagging every verifiable claim — commitments, metrics, governance statements, and risk declarations. He categorises each claim by type and importance before passing them to the investigation crew.",
    specialTool: "Document parsing & claim detection pipeline",
    capabilities: [
      "Claim categorisation (5 types)",
      "IFRS paragraph pre-mapping",
      "Priority scoring",
      "Source page attribution",
    ],
    bodyColor: "#fef9c3",
    eyeColor: "#854d0e",
    blushColor: "#fde68a",
    markColor: "#ca8a04",
    floatDelay: 0.4,
    floatDuration: 4.8,
    mark: "doc",
  },
  {
    id: "mike",
    agentKey: "legal",
    name: "Mike",
    role: "Legal Agent",
    shortDesc: "Mike is the compliance expert. He maps every claim to the exact IFRS S1/S2 paragraph it should satisfy, then checks which required disclosures are missing. If there's a gap between what the report says and what IFRS demands, Mike finds it.",
    longDesc:
      "Mike is the compliance specialist. He maps each claim to specific IFRS S1/S2 paragraphs, checks for disclosure gaps, and identifies whether required disclosures are fully addressed, partially addressed, or missing entirely. His output powers the S1/S2 cross-mapping view.",
    specialTool: "IFRS S1/S2 paragraph knowledge base",
    capabilities: [
      "Disclosure gap detection",
      "Governance claim analysis (S2.5–7)",
      "Strategy & risk compliance (S2.14, S2.24–26)",
      "Partial vs. unaddressed gap classification",
    ],
    bodyColor: "#dbeafe",
    eyeColor: "#1e3a8a",
    blushColor: "#93c5fd",
    markColor: "#2563eb",
    floatDelay: 0.8,
    floatDuration: 5.6,
    mark: "scales",
  },
  {
    id: "rhea",
    agentKey: "data_metrics",
    name: "Rhea",
    role: "Data & Metrics Agent",
    shortDesc: "Rhea checks if the numbers actually add up. She validates Scope 1/2/3 totals, tests whether reduction targets are mathematically achievable, and compares figures against industry benchmarks. Spotting a \"42% reduction by 2030\" that doesn't match the baseline is exactly her job.",
    longDesc:
      "Rhea cross-checks every quantitative claim for mathematical consistency, methodology alignment, and benchmark plausibility. She validates Scope 1/2/3 totals, checks reduction targets against baselines and timelines, and flags any figures that don't add up.",
    specialTool: "GHG quantitative validation engine",
    capabilities: [
      "Mathematical consistency checks",
      "GHG Protocol methodology validation",
      "Industry benchmark comparison",
      "Target achievability & timeline analysis",
    ],
    bodyColor: "#ccfbf1",
    eyeColor: "#134e4a",
    blushColor: "#5eead4",
    markColor: "#0d9488",
    floatDelay: 1.2,
    floatDuration: 4.6,
    mark: "chart",
  },
  {
    id: "izzy",
    agentKey: "news_media",
    name: "Izzy",
    role: "News & Media Agent",
    shortDesc: "Izzy searches public news, investigative journalism, and regulatory filings for anything that confirms or contradicts what the report claims. If a company says it hit a target but a regulator fined them that same year, Izzy finds the story.",
    longDesc:
      "Izzy searches public news, investigative journalism, press releases, and regulatory actions for evidence supporting or contradicting each claim. She ranks sources by credibility tier and flags any public record that contradicts the report's statements.",
    specialTool: "Web search & live news retrieval",
    capabilities: [
      "Four-tier source credibility ranking",
      "Contradiction detection across public records",
      "Regulatory filing & press release analysis",
      "Real-time news coverage scanning",
    ],
    bodyColor: "#fee2e2",
    eyeColor: "#7f1d1d",
    blushColor: "#fca5a5",
    markColor: "#dc2626",
    floatDelay: 1.6,
    floatDuration: 5.0,
    mark: "waves",
  },
  {
    id: "newton",
    agentKey: "academic",
    name: "Newton",
    role: "Academic Research Agent",
    shortDesc: "Newton digs into academic databases and published research to check whether a claim aligns with scientific consensus. If a company cites a methodology or makes an environmental assertion, Newton finds out whether the science actually backs it up.",
    longDesc:
      "Newton queries academic databases and research repositories to find scientific consensus, published methodologies, and empirical evidence for or against the report's claims. He's particularly powerful for environmental targets and emissions methodology claims — a little Newton energy never hurts.",
    specialTool: "Academic database & research repository search",
    capabilities: [
      "Scientific consensus assessment",
      "Emissions & environmental methodology verification",
      "Peer-reviewed evidence retrieval",
      "Claim-to-literature alignment scoring",
    ],
    bodyColor: "#ede9fe",
    eyeColor: "#3b0764",
    blushColor: "#c4b5fd",
    markColor: "#7c3aed",
    floatDelay: 2.0,
    floatDuration: 5.4,
    mark: "book",
  },
  {
    id: "columbo",
    agentKey: "geography",
    name: "Columbo",
    role: "Geography Agent",
    shortDesc: "Columbo cross-checks location-based claims against satellite imagery and geographic databases. If a report says 23 facilities in Southeast Asia face physical climate risk, Columbo checks whether those facilities and their exposure levels are real.",
    longDesc:
      "Columbo validates location-based claims — physical risk exposures, facility counts, regional operations — against satellite imagery and geographic databases. Like his namesake, he always has just one more question — and that question is usually about whether that facility is actually where you said it was.",
    specialTool: "Satellite imagery & geographic database API",
    capabilities: [
      "Physical risk location mapping",
      "Facility & asset count verification",
      "Regional climate exposure data sourcing",
      "Cross-referencing reported locations vs. real-world data",
    ],
    bodyColor: "#d1fae5",
    eyeColor: "#064e3b",
    blushColor: "#6ee7b7",
    markColor: "#059669",
    floatDelay: 2.4,
    floatDuration: 4.9,
    mark: "globe",
  },
  {
    id: "judy",
    agentKey: "judge",
    name: "Judy",
    role: "Judge",
    shortDesc: "Judy weighs all the evidence and delivers the final verdict on every claim. She reads the findings from every specialist agent and decides whether each claim is verified, unverified, contradicted, or lacking sufficient evidence — then writes the reasoning.",
    longDesc:
      "Judy is the final word. After every specialist agent has submitted their findings, she evaluates the totality of evidence — legal, scientific, journalistic, geographic, and quantitative — and issues a verdict for each claim. If the evidence is contradictory, she may send claims back for reinvestigation before ruling.",
    specialTool: "Multi-source evidence synthesis & verdict engine",
    capabilities: [
      "Cross-agent evidence synthesis",
      "Verdict issuance (verified / unverified / contradicted)",
      "Re-investigation requests on conflicting evidence",
      "Confidence scoring & reasoning generation",
    ],
    bodyColor: "#fde2e2",
    eyeColor: "#7f1d1d",
    blushColor: "#fca5a5",
    markColor: "#dc2626",
    floatDelay: 2.8,
    floatDuration: 5.1,
    mark: "gavel",
  },
];

// ─── SVG Marks ────────────────────────────────────────────────────────────────

export function AgentMark({ type, color }: { type: Agent["mark"]; color: string }) {
  switch (type) {
    case "crown":
      return (
        <path
          d="M 38 28 L 40 35 L 44 28 L 50 33 L 56 28 L 60 35 L 62 28 L 62 40 L 38 40 Z"
          fill={color}
          opacity={0.9}
        />
      );
    case "doc":
      return (
        <g transform="translate(39, 62)" opacity={0.9}>
          <rect x="0" y="0" width="22" height="18" rx="2" fill={color} />
          <rect x="3" y="4" width="16" height="2" rx="1" fill="white" opacity={0.7} />
          <rect x="3" y="8" width="12" height="2" rx="1" fill="white" opacity={0.7} />
          <rect x="3" y="12" width="10" height="2" rx="1" fill="white" opacity={0.7} />
        </g>
      );
    case "scales":
      return (
        <g transform="translate(35, 62)" opacity={0.9} stroke={color} fill="none" strokeWidth="2">
          <line x1="15" y1="0" x2="15" y2="16" strokeLinecap="round" />
          <line x1="5" y1="6" x2="25" y2="6" strokeLinecap="round" />
          <path d="M 5 6 L 0 14 L 10 14 Z" fill={color} />
          <path d="M 25 6 L 20 14 L 30 14 Z" fill={color} />
        </g>
      );
    case "chart":
      return (
        <g transform="translate(35, 64)" opacity={0.9}>
          <rect x="0" y="10" width="8" height="8" rx="1" fill={color} />
          <rect x="11" y="5" width="8" height="13" rx="1" fill={color} />
          <rect x="22" y="0" width="8" height="18" rx="1" fill={color} />
        </g>
      );
    case "waves":
      return (
        <g transform="translate(32, 65)" opacity={0.9} stroke={color} fill="none" strokeWidth="2" strokeLinecap="round">
          <path d="M 0 10 Q 6 4 12 10 Q 18 16 24 10" />
          <path d="M 4 16 Q 10 10 16 16 Q 22 22 28 16" />
          <circle cx="18" cy="4" r="3" fill={color} />
        </g>
      );
    case "book":
      return (
        <g transform="translate(34, 64)" opacity={0.9}>
          <rect x="0" y="0" width="14" height="16" rx="1" fill={color} />
          <rect x="16" y="0" width="14" height="16" rx="1" fill={color} />
          <line x1="14" y1="0" x2="16" y2="0" stroke="white" strokeWidth="2" />
          <line x1="14" y1="16" x2="16" y2="16" stroke="white" strokeWidth="2" />
          <rect x="2" y="4" width="10" height="1.5" rx="0.5" fill="white" opacity={0.6} />
          <rect x="2" y="7" width="8" height="1.5" rx="0.5" fill="white" opacity={0.6} />
          <rect x="18" y="4" width="10" height="1.5" rx="0.5" fill="white" opacity={0.6} />
          <rect x="18" y="7" width="8" height="1.5" rx="0.5" fill="white" opacity={0.6} />
        </g>
      );
    case "globe":
      return (
        <g transform="translate(37, 62)" opacity={0.9} fill="none" stroke={color} strokeWidth="1.8">
          <circle cx="13" cy="10" r="10" />
          <ellipse cx="13" cy="10" rx="5" ry="10" />
          <line x1="3" y1="10" x2="23" y2="10" />
          <line x1="5" y1="4" x2="21" y2="4" />
          <line x1="5" y1="16" x2="21" y2="16" />
        </g>
      );
    case "gavel":
      return (
        <g transform="translate(33, 62)" opacity={0.9}>
          {/* Gavel head */}
          <rect x="0" y="0" width="20" height="9" rx="2.5" fill={color} />
          {/* Strike band on head */}
          <rect x="4" y="0" width="4" height="9" rx="1" fill="white" opacity={0.25} />
          {/* Handle */}
          <rect
            x="14" y="7"
            width="22" height="4"
            rx="2"
            fill={color}
            transform="rotate(35 14 7)"
          />
          {/* Base plate */}
          <rect x="2" y="16" width="28" height="4" rx="2" fill={color} opacity={0.6} />
        </g>
      );
    default:
      return null;
  }
}

// ─── Single Egg Avatar ────────────────────────────────────────────────────────

export interface EggAvatarProps {
  agent: Agent;
  isHovered: boolean;
  onHover: (v: boolean) => void;
  onClick: () => void;
  size?: number;
}

export const EGG = "M 50 12 C 78 12, 90 35, 90 57 C 90 79, 73 90, 50 90 C 27 90, 10 79, 10 57 C 10 35, 22 12, 50 12 Z";

export function EggAvatar({ agent, isHovered, onHover, onClick, size = 72 }: EggAvatarProps) {
  // Separate float Y from hover to prevent snap-back on hover-end.
  // floatY runs continuously; whileHover only affects scale.
  const floatY = useMotionValue(0);

  useEffect(() => {
    let cancelled = false;

    const runFloat = async () => {
      if (cancelled) return;
      // Drift up
      await animate(floatY, -7, { duration: agent.floatDuration / 2, ease: "easeInOut", delay: agent.floatDelay });
      if (cancelled) return;
      // Drift back down
      await animate(floatY, 0, { duration: agent.floatDuration / 2, ease: "easeInOut" });
      if (cancelled) return;
      runFloat(); // loop
    };

    runFloat();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agent.floatDelay, agent.floatDuration]);

  return (
    <motion.div
      className="flex flex-col items-center gap-2 cursor-pointer select-none"
      style={{ y: floatY }}
      whileHover={{ scale: 1.13 }}
      onHoverStart={() => onHover(true)}
      onHoverEnd={() => onHover(false)}
      onClick={onClick}
    >
      <svg viewBox="0 0 100 100" width={size} height={size} aria-label={`${agent.name} - ${agent.role}`}>
        {/* Shadow */}
        <ellipse cx="50" cy="97" rx="22" ry="4" fill="#0005" />

        {/* Body */}
        <path d={EGG} fill={agent.bodyColor} />

        {/* Shine */}
        <ellipse cx="35" cy="32" rx="10" ry="6" fill="white" opacity={0.35} transform="rotate(-30 35 32)" />

        {/* Eyes */}
        <AnimatePresence mode="wait">
          {isHovered ? (
            <motion.g key="happy" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {/* Happy squint arcs */}
              <path
                d="M 29 49 Q 37 41 45 49"
                stroke={agent.eyeColor}
                strokeWidth="3"
                fill="none"
                strokeLinecap="round"
              />
              <path
                d="M 55 49 Q 63 41 71 49"
                stroke={agent.eyeColor}
                strokeWidth="3"
                fill="none"
                strokeLinecap="round"
              />
              {/* Blush */}
              <ellipse cx="24" cy="57" rx="9" ry="5.5" fill={agent.blushColor} opacity={0.55} />
              <ellipse cx="76" cy="57" rx="9" ry="5.5" fill={agent.blushColor} opacity={0.55} />
            </motion.g>
          ) : (
            <motion.g key="neutral" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {/* Open eyes */}
              <circle cx="37" cy="48" r="8.5" fill={agent.eyeColor} />
              <circle cx="63" cy="48" r="8.5" fill={agent.eyeColor} />
              {/* Pupils */}
              <circle cx="37" cy="48" r="4.5" fill="white" />
              <circle cx="63" cy="48" r="4.5" fill="white" />
              <circle cx="35" cy="46" r="2" fill={agent.eyeColor} />
              <circle cx="61" cy="46" r="2" fill={agent.eyeColor} />
              {/* Sparkle */}
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

        {/* Agent mark emblem */}
        <AgentMark type={agent.mark} color={agent.markColor} />
      </svg>

      {/* Name tag */}
      <div className="text-center">
        <p className="text-xs font-semibold text-[#4a3c2e] leading-tight">{agent.name}</p>
        <p className="text-[10px] text-[#8b7355] leading-tight">{agent.role}</p>
      </div>
    </motion.div>
  );
}

// ─── Tooltip ──────────────────────────────────────────────────────────────────

function Tooltip({ text, agentName, agentRole }: { text: string; agentName: string; agentRole: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.94 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 4, scale: 0.96 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
      className="absolute bottom-full mb-4 left-1/2 -translate-x-1/2 z-50 pointer-events-none"
      style={{ width: 260 }}
    >
      <div className="bg-[#2d1f14] text-[#fff6e9] rounded-xl px-4 py-3.5 shadow-xl">
        {/* Header */}
        <div className="flex items-center gap-2 mb-2 pb-2 border-b border-[#ffffff18]">
          <span className="text-xs font-bold text-[#fff6e9]">{agentName}</span>
          <span className="text-[10px] text-[#c8a97a] font-medium">{agentRole}</span>
        </div>
        {/* Body */}
        <p className="text-xs text-[#eddfc8] leading-relaxed">{text}</p>
      </div>
      {/* Arrow */}
      <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px
                      border-[6px] border-transparent border-t-[#2d1f14]" />
    </motion.div>
  );
}

// ─── Agent Modal ──────────────────────────────────────────────────────────────

function AgentModal({ agent, onClose }: { agent: Agent; onClose: () => void }) {
  const [hovered, setHovered] = useState(false);

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        {/* Backdrop */}
        <motion.div
          className="absolute inset-0 bg-black/40"
          onClick={onClose}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        />

        {/* Panel */}
        <motion.div
          className="relative bg-[#fff6e9] rounded-2xl p-8 max-w-md w-full shadow-2xl"
          initial={{ opacity: 0, y: 24, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 16, scale: 0.97 }}
          transition={{ type: "spring", stiffness: 380, damping: 28 }}
        >
          {/* Close */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1.5 text-[#6b5344] hover:text-[#4a3c2e] transition-colors"
            aria-label="Close"
          >
            <X size={18} />
          </button>

          {/* Avatar */}
          <div className="flex justify-center mb-5">
            <motion.div
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
            >
              <svg viewBox="0 0 100 100" width="110" height="110"
                onMouseEnter={() => setHovered(true)}
                onMouseLeave={() => setHovered(false)}
              >
                <ellipse cx="50" cy="97" rx="22" ry="4" fill="#0005" />
                <path d={EGG} fill={agent.bodyColor} />
                <ellipse cx="35" cy="32" rx="10" ry="6" fill="white" opacity={0.35}
                  transform="rotate(-30 35 32)" />
                {hovered ? (
                  <>
                    <path d="M 29 49 Q 37 41 45 49" stroke={agent.eyeColor} strokeWidth="3"
                      fill="none" strokeLinecap="round" />
                    <path d="M 55 49 Q 63 41 71 49" stroke={agent.eyeColor} strokeWidth="3"
                      fill="none" strokeLinecap="round" />
                    <ellipse cx="24" cy="57" rx="9" ry="5.5" fill={agent.blushColor} opacity={0.55} />
                    <ellipse cx="76" cy="57" rx="9" ry="5.5" fill={agent.blushColor} opacity={0.55} />
                    <path d="M 35 64 Q 50 76 65 64" stroke={agent.eyeColor} strokeWidth="2.8"
                      fill="none" strokeLinecap="round" />
                  </>
                ) : (
                  <>
                    <circle cx="37" cy="48" r="8.5" fill={agent.eyeColor} />
                    <circle cx="63" cy="48" r="8.5" fill={agent.eyeColor} />
                    <circle cx="37" cy="48" r="4.5" fill="white" />
                    <circle cx="63" cy="48" r="4.5" fill="white" />
                    <circle cx="35" cy="46" r="2" fill={agent.eyeColor} />
                    <circle cx="61" cy="46" r="2" fill={agent.eyeColor} />
                    <circle cx="40" cy="44" r="1.2" fill="white" opacity={0.8} />
                    <circle cx="66" cy="44" r="1.2" fill="white" opacity={0.8} />
                    <path d="M 38 62 Q 50 70 62 62" stroke={agent.eyeColor} strokeWidth="2.8"
                      fill="none" strokeLinecap="round" />
                  </>
                )}
                <AgentMark type={agent.mark} color={agent.markColor} />
              </svg>
            </motion.div>
          </div>

          {/* Name + role */}
          <h2 className="text-2xl font-bold text-[#4a3c2e] text-center mb-0.5">{agent.name}</h2>
          <p className="text-sm font-medium text-[#6b5344] text-center mb-5">{agent.role}</p>

          {/* Description */}
          <p className="text-sm text-[#4a3c2e] leading-relaxed mb-5">{agent.longDesc}</p>

          {/* Special Tool */}
          <div className="mb-4 p-3 rounded-lg" style={{ backgroundColor: agent.bodyColor }}>
            <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: agent.markColor }}>
              Special Tool
            </p>
            <p className="text-sm font-semibold text-[#4a3c2e]">{agent.specialTool}</p>
          </div>

          {/* Capabilities */}
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-[#8b7355] mb-2">
              Capabilities
            </p>
            <ul className="space-y-1.5">
              {agent.capabilities.map((cap) => (
                <li key={cap} className="flex items-start gap-2 text-sm text-[#4a3c2e]">
                  <span
                    className="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0"
                    style={{ backgroundColor: agent.markColor }}
                  />
                  {cap}
                </li>
              ))}
            </ul>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// ─── Main Export ──────────────────────────────────────────────────────────────

// The landing page shows all agents including the judge
const LANDING_AGENTS = AGENTS;

export function AgentVillage() {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [modalAgent, setModalAgent] = useState<Agent | null>(null);

  return (
    <>
      <div className="relative z-10 w-full max-w-4xl mx-auto mt-[2vh] mb-[1vh] px-4">
        {/* Section label */}
        <p className="text-center text-xs font-bold uppercase tracking-widest text-[#8b7355] mb-3 lg:mb-6">
          Meet the Village
        </p>

        {/* Avatars row */}
        <div className="flex items-end justify-center gap-3 lg:gap-5 flex-wrap">
          {LANDING_AGENTS.map((agent) => (
            <div key={agent.id} className="relative flex flex-col items-center">
              <AnimatePresence>
                {hoveredId === agent.id && (
                  <Tooltip
                    text={agent.shortDesc}
                    agentName={agent.name}
                    agentRole={agent.role}
                  />
                )}
              </AnimatePresence>

              <EggAvatar
                agent={agent}
                isHovered={hoveredId === agent.id}
                onHover={(v) => setHoveredId(v ? agent.id : null)}
                onClick={() => setModalAgent(agent)}
              />
            </div>
          ))}
        </div>

        <p className="text-center text-xs text-[#8b7355] mt-2 lg:mt-4">
          Click any agent to learn what they do
        </p>
      </div>

      {/* Modal */}
      {modalAgent && (
        <AgentModal agent={modalAgent} onClose={() => setModalAgent(null)} />
      )}
    </>
  );
}
