/**
 * DocsPage — Product overview & reference documentation for Sibyl.
 *
 * Design: warm cream palette, alternating avatar + text blocks, blur fade-ins,
 * subtle Lucide icons, no emojis, no cold greys.
 */

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import {
  FileSearch,
  Network,
  Scale,
  MessageSquare,
  CheckCircle2,
  XCircle,
  HelpCircle,
  RotateCcw,
  ArrowRight,
  BookOpen,
  Layers,
  Cpu,
} from "lucide-react";
import { AGENTS, EGG, AgentMark } from "@/components/AgentVillage";
import type { Agent } from "@/components/AgentVillage";

// ─── Mini inline avatar (pure SVG, no motion — used in docs cards) ───────────

function MiniEgg({ agent, size = 80 }: { agent: Agent; size?: number }) {
  return (
    <svg viewBox="0 0 100 100" width={size} height={size} aria-label={agent.name}>
      <ellipse cx="50" cy="97" rx="22" ry="4" fill="#0003" />
      <path d={EGG} fill={agent.bodyColor} />
      <ellipse cx="35" cy="32" rx="10" ry="6" fill="white" opacity={0.35} transform="rotate(-30 35 32)" />
      <circle cx="37" cy="48" r="8.5" fill={agent.eyeColor} />
      <circle cx="63" cy="48" r="8.5" fill={agent.eyeColor} />
      <circle cx="37" cy="48" r="4.5" fill="white" />
      <circle cx="63" cy="48" r="4.5" fill="white" />
      <circle cx="35" cy="46" r="2" fill={agent.eyeColor} />
      <circle cx="61" cy="46" r="2" fill={agent.eyeColor} />
      <circle cx="40" cy="44" r="1.2" fill="white" opacity={0.8} />
      <circle cx="66" cy="44" r="1.2" fill="white" opacity={0.8} />
      <path d="M 38 62 Q 50 70 62 62" stroke={agent.eyeColor} strokeWidth="2.8" fill="none" strokeLinecap="round" />
      <AgentMark type={agent.mark} color={agent.markColor} />
    </svg>
  );
}

// ─── Scroll-triggered fade wrapper ───────────────────────────────────────────

function FadeIn({
  children,
  delay = 0,
  className,
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  return (
    <motion.div
      ref={ref}
      className={className}
      initial={{ opacity: 0, y: 18, filter: "blur(5px)" }}
      animate={inView ? { opacity: 1, y: 0, filter: "blur(0px)" } : {}}
      transition={{ duration: 0.5, ease: "easeOut", delay }}
    >
      {children}
    </motion.div>
  );
}

// ─── Section heading ──────────────────────────────────────────────────────────

function SectionHeading({
  icon: Icon,
  label,
  title,
}: {
  icon: React.ElementType;
  label: string;
  title: string;
}) {
  return (
    <FadeIn>
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
        <Icon size={14} color="#8b7355" />
        <span style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "#8b7355" }}>
          {label}
        </span>
      </div>
      <h2
        style={{
          fontSize: "1.75rem",
          fontWeight: 800,
          color: "#4a3c2e",
          letterSpacing: "-0.02em",
          margin: 0,
          lineHeight: 1.15,
        }}
      >
        {title}
      </h2>
    </FadeIn>
  );
}

// ─── Verdict badge ────────────────────────────────────────────────────────────

function VerdictBadge({
  icon: Icon,
  label,
  color,
  bg,
}: {
  icon: React.ElementType;
  label: string;
  color: string;
  bg: string;
}) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.35rem",
        padding: "0.3rem 0.75rem",
        borderRadius: "9999px",
        background: bg,
        color,
        fontSize: "12px",
        fontWeight: 600,
      }}
    >
      <Icon size={12} />
      {label}
    </div>
  );
}

// ─── Agent card — alternating layout ─────────────────────────────────────────

function AgentCard({
  agent,
  index,
}: {
  agent: Agent;
  index: number;
}) {
  const isRight = index % 2 === 1; // odd → avatar on right
  return (
    <FadeIn delay={0.05} className="docs-agent-card">
      <div
        style={{
          display: "flex",
          flexDirection: isRight ? "row-reverse" : "row",
          alignItems: "flex-start",
          gap: "2.5rem",
          padding: "2rem 0",
          borderBottom: "1px solid #eddfc8",
        }}
      >
        {/* Avatar block */}
        <div style={{ flexShrink: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}>
          <MiniEgg agent={agent} size={100} />
          <span style={{ fontSize: "13px", fontWeight: 700, color: "#4a3c2e" }}>{agent.name}</span>
          <span
            style={{
              fontSize: "10px",
              fontWeight: 600,
              letterSpacing: "0.07em",
              textTransform: "uppercase",
              color: "#8b7355",
            }}
          >
            {agent.role}
          </span>
        </div>

        {/* Text block */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ fontSize: "0.9375rem", color: "#4a3c2e", lineHeight: 1.65, margin: "0 0 1rem" }}>
            {agent.longDesc}
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
            {agent.capabilities.map((cap) => (
              <span
                key={cap}
                style={{
                  fontSize: "11px",
                  padding: "2px 10px",
                  background: "#f5ecdb",
                  color: "#6b5344",
                  borderRadius: "4px",
                  fontWeight: 500,
                }}
              >
                {cap}
              </span>
            ))}
          </div>
          {agent.specialTool && (
            <p style={{ marginTop: "0.75rem", fontSize: "12px", color: "#8b7355" }}>
              <span style={{ fontWeight: 600, color: "#6b5344" }}>Special tool:</span> {agent.specialTool}
            </p>
          )}
        </div>
      </div>
    </FadeIn>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

// Exclude message_pool from the displayed agents
const DISPLAY_AGENTS = AGENTS.filter((a) => a.agentKey !== "message_pool");

export function DocsPage() {
  return (
    <div
      style={{
        minHeight: "100%",
        background: "#fff6e9",
        overflowY: "auto",
        color: "#4a3c2e",
      }}
    >
      {/* ── Hero ── */}
      <div
        style={{
          maxWidth: "700px",
          margin: "0 auto",
          padding: "clamp(2rem, 5vh, 3.5rem) 2rem 4rem",
        }}
      >
        <motion.div
          initial={{ opacity: 0, y: -16, filter: "blur(8px)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        >
          <h1
            style={{
              fontSize: "clamp(2.5rem, 5vw, 3.5rem)",
              fontWeight: 800,
              color: "#4a3c2e",
              letterSpacing: "-0.03em",
              lineHeight: 1.1,
              margin: "0 0 1.25rem",
            }}
          >
            How Sibyl Works
          </h1>
          <p style={{ fontSize: "1.0625rem", color: "#6b5344", lineHeight: 1.7, maxWidth: "560px" }}>
            Sibyl is a multi-agent AI system that verifies sustainability report claims against IFRS S1/S2 standards,
            scientific research, geographic data, and real-world news — then delivers a structured, evidence-backed
            compliance report.
          </p>
        </motion.div>

        {/* Quick stat row */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.25, ease: "easeOut" }}
          style={{
            display: "flex",
            gap: "2rem",
            marginTop: "2.5rem",
            paddingTop: "2rem",
            borderTop: "1px solid #e0d4bf",
            flexWrap: "wrap",
          }}
        >
          {[
            { label: "Specialist agents", value: "7" },
            { label: "IFRS paragraphs covered", value: "44" },
            { label: "Verdict types", value: "4" },
          ].map(({ label, value }) => (
            <div key={label}>
              <div style={{ fontSize: "2rem", fontWeight: 800, color: "#4a3c2e", letterSpacing: "-0.02em" }}>{value}</div>
              <div style={{ fontSize: "12px", color: "#8b7355", marginTop: "2px" }}>{label}</div>
            </div>
          ))}
        </motion.div>
      </div>

      {/* ── What is a Sustainability Report? ── */}
      <div style={{ maxWidth: "700px", margin: "0 auto", padding: "0 2rem 5rem" }}>
        <SectionHeading icon={FileSearch} label="Context" title="Sustainability Reports & IFRS S1/S2" />
        <FadeIn delay={0.1}>
          <p style={{ fontSize: "0.9375rem", color: "#4a3c2e", lineHeight: 1.7, margin: "1.25rem 0 1rem" }}>
            IFRS S1 and S2 are the new global baseline for sustainability disclosures. S1 covers general sustainability
            risk and opportunity disclosures; S2 covers climate-specific disclosures — physical risks, transition plans,
            Scope 1/2/3 emissions, and governance structures. Listed companies are required to report against these
            standards, but the reports are dense, technical, and hard to audit at scale.
          </p>
          <p style={{ fontSize: "0.9375rem", color: "#4a3c2e", lineHeight: 1.7, margin: "0 0 1rem" }}>
            Sibyl automates this audit. It extracts every verifiable claim from a report, routes each claim to
            specialist agents for independent evidence gathering, and synthesises the findings into a structured
            verdict — with paragraph-level citations and disclosure gap analysis.
          </p>
          <div
            style={{
              background: "#f5ecdb",
              borderLeft: "3px solid #d97706",
              padding: "0.875rem 1.125rem",
              borderRadius: "0 8px 8px 0",
              marginTop: "1.25rem",
            }}
          >
            <p style={{ fontSize: "0.875rem", color: "#4a3c2e", margin: 0, lineHeight: 1.6 }}>
              <strong>Example:</strong> A company states "We achieved a 42% reduction in Scope 1 emissions against our 2019
              baseline." Sibyl extracts this claim, sends it to Rhea (data verification), Newton (scientific methodology),
              Mike (IFRS paragraph mapping), and Yahu (news & regulatory filings) — all in parallel.
            </p>
          </div>
        </FadeIn>
      </div>

      {/* ── Pipeline overview ── */}
      <div style={{ background: "#f5ecdb", padding: "4rem 0" }}>
        <div style={{ maxWidth: "700px", margin: "0 auto", padding: "0 2rem" }}>
          <SectionHeading icon={Network} label="Architecture" title="The Investigation Pipeline" />
          <FadeIn delay={0.1}>
            <p style={{ fontSize: "0.9375rem", color: "#4a3c2e", lineHeight: 1.7, margin: "1.25rem 0 2rem" }}>
              Each analysis runs a structured pipeline. Agents communicate asynchronously through a shared message pool,
              allowing the Orchestrator to coordinate complex multi-hop investigations without blocking.
            </p>
          </FadeIn>

          {/* Pipeline steps */}
          {[
            { step: "01", title: "Claim Extraction", desc: "Menny reads the full report and identifies every verifiable statement — quantitative targets, governance disclosures, risk assessments, and commitments.", icon: FileSearch },
            { step: "02", title: "Orchestration", desc: "Bron receives the claim list and dispatches each claim to the appropriate specialist agents. She tracks in-flight investigations and waits for findings.", icon: Cpu },
            { step: "03", title: "Specialist Verification", desc: "Five specialist agents (Legal, Data, News, Academic, Geography) independently research their assigned claims and post findings back to the message pool.", icon: Layers },
            { step: "04", title: "Verdict & Report", desc: "Vera evaluates the combined findings and issues a verdict for each claim. If evidence is insufficient, she may request reinvestigation before ruling. The final report is structured by IFRS pillar.", icon: Scale },
          ].map(({ step, title, desc, icon: Icon }, i) => (
            <FadeIn key={step} delay={i * 0.07}>
              <div style={{ display: "flex", gap: "1.25rem", marginBottom: "1.5rem" }}>
                <div style={{ flexShrink: 0, display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <div
                    style={{
                      width: "36px",
                      height: "36px",
                      borderRadius: "50%",
                      background: "#fff6e9",
                      border: "1.5px solid #e0d4bf",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Icon size={15} color="#8b7355" />
                  </div>
                  {i < 3 && <div style={{ width: "1px", height: "28px", background: "#e0d4bf", marginTop: "4px" }} />}
                </div>
                <div style={{ paddingTop: "6px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.3rem" }}>
                    <span style={{ fontSize: "10px", fontWeight: 700, color: "#8b7355", letterSpacing: "0.06em" }}>{step}</span>
                    <span style={{ fontSize: "0.9375rem", fontWeight: 700, color: "#4a3c2e" }}>{title}</span>
                  </div>
                  <p style={{ fontSize: "0.875rem", color: "#6b5344", lineHeight: 1.6, margin: 0 }}>{desc}</p>
                </div>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>

      {/* ── Message Pool ── */}
      <div style={{ maxWidth: "700px", margin: "0 auto", padding: "5rem 2rem" }}>
        <SectionHeading icon={MessageSquare} label="Infrastructure" title="The Message Pool" />
        <FadeIn delay={0.1}>
          <p style={{ fontSize: "0.9375rem", color: "#4a3c2e", lineHeight: 1.7, margin: "1.25rem 0 1rem" }}>
            The message pool is a shared, asynchronous communication layer between all agents. Rather than agents calling
            each other directly, any agent can post an info request — a structured question — to the pool. The
            Orchestrator polls the pool and routes the response back to the requesting agent.
          </p>
          <p style={{ fontSize: "0.9375rem", color: "#4a3c2e", lineHeight: 1.7, margin: "0 0 1.5rem" }}>
            This decouples the agents: a specialist never waits on another specialist. The Orchestrator is the sole
            consumer of pool messages, preventing race conditions and ensuring a single source of truth for investigation
            state. In the investigation graph, the message pool appears as a central table surrounded by the five
            specialist agents — you can watch messages flow in and out in real time.
          </p>

          {/* Message flow illustration */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              padding: "1.25rem",
              background: "#f5ecdb",
              borderRadius: "12px",
              flexWrap: "wrap",
            }}
          >
            {[
              { label: "Specialist", sub: "posts info request" },
              null,
              { label: "Message Pool", sub: "queues request" },
              null,
              { label: "Orchestrator", sub: "routes & responds" },
            ].map((item, i) =>
              item === null ? (
                <ArrowRight key={i} size={16} color="#c8a97a" style={{ flexShrink: 0 }} />
              ) : (
                <div key={i} style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "12px", fontWeight: 700, color: "#4a3c2e" }}>{item.label}</div>
                  <div style={{ fontSize: "10px", color: "#8b7355" }}>{item.sub}</div>
                </div>
              )
            )}
          </div>
        </FadeIn>
      </div>

      {/* ── Verdict types ── */}
      <div style={{ background: "#f5ecdb", padding: "4rem 0" }}>
        <div style={{ maxWidth: "700px", margin: "0 auto", padding: "0 2rem" }}>
          <SectionHeading icon={Scale} label="Output" title="Verdict Types" />
          <FadeIn delay={0.1}>
            <p style={{ fontSize: "0.9375rem", color: "#4a3c2e", lineHeight: 1.7, margin: "1.25rem 0 2rem" }}>
              Every claim receives one of four verdicts from Vera, based on the totality of evidence:
            </p>
          </FadeIn>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            {[
              {
                icon: CheckCircle2,
                label: "Verified",
                color: "#059669",
                bg: "#d1fae5",
                desc: "All evidence supports the claim. Sources are cited and methodology is sound.",
              },
              {
                icon: XCircle,
                label: "Contradicted",
                color: "#dc2626",
                bg: "#fee2e2",
                desc: "External evidence directly conflicts with the claim — regulatory findings, news, or data discrepancies.",
              },
              {
                icon: HelpCircle,
                label: "Unverified",
                color: "#d97706",
                bg: "#fef3c7",
                desc: "Evidence is insufficient to confirm or deny. May trigger reinvestigation.",
              },
              {
                icon: RotateCcw,
                label: "Reinvestigating",
                color: "#7c3aed",
                bg: "#ede9fe",
                desc: "Vera has sent the claim back to specialists for additional evidence before ruling.",
              },
            ].map(({ icon: Icon, label, color, bg, desc }) => (
              <FadeIn key={label}>
                <div
                  style={{
                    background: "#fff6e9",
                    padding: "1.25rem",
                    height: "100%",
                  }}
                >
                  <div style={{ marginBottom: "0.75rem" }}>
                    <VerdictBadge icon={Icon} label={label} color={color} bg={bg} />
                  </div>
                  <p style={{ fontSize: "0.875rem", color: "#6b5344", lineHeight: 1.6, margin: 0 }}>{desc}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </div>

      {/* ── Agent roster ── */}
      <div style={{ maxWidth: "700px", margin: "0 auto", padding: "5rem 2rem 2rem" }}>
        <SectionHeading icon={Cpu} label="Agents" title="Meet the Village" />
        <FadeIn delay={0.1}>
          <p style={{ fontSize: "0.9375rem", color: "#4a3c2e", lineHeight: 1.7, margin: "1.25rem 0 0" }}>
            Each agent is specialised for a distinct dimension of evidence. Together they form an interlocking system
            where no single agent&apos;s finding is taken at face value — every verdict is cross-referenced.
          </p>
        </FadeIn>
      </div>

      <div style={{ maxWidth: "700px", margin: "0 auto", padding: "0 2rem 6rem" }}>
        {DISPLAY_AGENTS.map((agent, i) => (
          <AgentCard key={agent.id} agent={agent} index={i} />
        ))}
      </div>

      {/* ── Footer ── */}
      <div style={{ borderTop: "1px solid #e0d4bf", padding: "2.5rem 2rem", textAlign: "center" }}>
        <p style={{ fontSize: "12px", color: "#8b7355" }}>
          Sibyl · IFRS S1/S2 Sustainability Verification
        </p>
      </div>
    </div>
  );
}
