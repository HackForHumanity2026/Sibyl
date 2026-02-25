/**
 * Home page with hero section and PDF upload.
 * Implements FRD 2 Section 1 - Home Page UI.
 */

import { motion } from "framer-motion";
import { useUpload } from "@/hooks/useUpload";
import { UploadZone, UploadProgress, ContentPreview } from "@/components/Upload";
import { LeafBackground } from "@/components/LeafBackground";
import { AgentVillage } from "@/components/AgentVillage";
import { RefreshCw, ArrowLeft } from "lucide-react";

// ─── Animation config ─────────────────────────────────────────────────────────

/** Each word springs up from below while simultaneously unblurring. */
const wordVariants = {
  hidden: {
    opacity: 0,
    y: 30,
    filter: "blur(12px)",
  },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: {
      type: "spring" as const,
      stiffness: 82,
      damping: 13,
      mass: 1.3,
    },
  },
};

// ─── Primitives ───────────────────────────────────────────────────────────────

/** A single animated word. Renders inline-block so it sits in text flow. */
function Word({ text, className }: { text: string; className?: string }) {
  return (
    <motion.span
      variants={wordVariants}
      style={{ display: "inline-block", marginRight: "0.28em" }}
      className={className}
    >
      {text}
    </motion.span>
  );
}

// ─── Hero heading ─────────────────────────────────────────────────────────────

function HeroHeading() {
  return (
    <motion.h1
      className="text-6xl font-bold text-slate-900 mb-5 tracking-tight leading-[1.15]"
      initial="hidden"
      animate="visible"
      variants={{
        hidden: {},
        visible: { transition: { staggerChildren: 0.075 } },
      }}
    >
      {/* Line 1 */}
      <span className="block">
        {["The", "Agent", "Collective"].map((w, i) => (
          <Word key={i} text={w} />
        ))}
      </span>
      {/* Line 2 — muted weight */}
      <span className="block text-[#8b7355] font-light">
        {["for", "Sustainability"].map((w, i) => (
          <Word key={i} text={w} />
        ))}
      </span>
    </motion.h1>
  );
}

// ─── Hero subheading ──────────────────────────────────────────────────────────

const S1_URL =
  "https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards-issb/english/2023/issued/part-a/issb-2023-a-ifrs-s1-general-requirements-for-disclosure-of-sustainability-related-financial-information.pdf?bypass=on";
const S2_URL =
  "https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards-issb/english/2023/issued/part-a/issb-2023-a-ifrs-s2-climate-related-disclosures.pdf?bypass=on";

const PRE_LINK_WORDS = [
  "A", "collective", "of", "specialised", "AI", "agents", "—",
  "each", "with", "unique", "tools,", "training,", "and", "capabilities",
  "—", "verifying", "every", "claim", "in", "your", "sustainability",
  "report", "against",
];

function HeroSubheading() {
  return (
    <motion.p
      className="text-lg text-[#4a3c2e] leading-relaxed max-w-xl mx-auto"
      initial="hidden"
      animate="visible"
      variants={{
        hidden: {},
        visible: {
          transition: {
            delayChildren: 0.38,
            staggerChildren: 0.012,
          },
        },
      }}
    >
      {/* Plain words */}
      {PRE_LINK_WORDS.map((w, i) => (
        <Word key={i} text={w} />
      ))}

      {/* IFRS S1 link — single animated token */}
      <motion.span
        variants={wordVariants}
        style={{ display: "inline-block", marginRight: "0.28em" }}
      >
        <a
          href={S1_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="font-bold underline text-[#4a3c2e] hover:text-slate-900 transition-colors"
        >
          IFRS S1
        </a>
      </motion.span>

      {/* "and" */}
      <Word text="and" />

      {/* IFRS S2 link — single animated token */}
      <motion.span
        variants={wordVariants}
        style={{ display: "inline-block" }}
      >
        <a
          href={S2_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="font-bold underline text-[#4a3c2e] hover:text-slate-900 transition-colors"
        >
          IFRS S2
        </a>
        {/* Period stays attached to the link token */}
        <span className="text-[#4a3c2e]">.</span>
      </motion.span>
    </motion.p>
  );
}

// ─── Page ──────────────────────────────────────────────────────────────────────

export function HomePage() {
  const {
    uploadState,
    report,
    error,
    file,
    startedAt,
    uploadFile,
    retry,
    reset,
  } = useUpload();

  const renderContent = () => {
    switch (uploadState) {
      case "idle":
        return <UploadZone onUpload={uploadFile} />;

      case "uploading":
      case "processing":
        return (
          <UploadProgress
            filename={file?.name ?? "Unknown file"}
            fileSizeBytes={file?.size ?? 0}
            status={report?.status ?? "uploaded"}
            startedAt={startedAt ?? new Date()}
          />
        );

      case "complete":
        if (report?.content_structure) {
          return (
            <div className="space-y-4">
              <ContentPreview
                reportId={report.report_id}
                filename={report.filename}
                contentStructure={report.content_structure}
                pageCount={report.page_count ?? 0}
              />
              <div className="flex justify-center">
                <button
                  onClick={reset}
                  className="flex items-center gap-1.5 text-sm text-[#8b7355] hover:text-slate-700 transition-colors"
                >
                  <ArrowLeft size={14} />
                  Upload another
                </button>
              </div>
            </div>
          );
        }
        return <UploadZone onUpload={uploadFile} />;

      case "error":
        return (
          <div className="w-full max-w-xl mx-auto">
            <UploadProgress
              filename={file?.name ?? "Unknown file"}
              fileSizeBytes={file?.size ?? 0}
              status="error"
              errorMessage={error}
              startedAt={startedAt ?? new Date()}
            />
            <div className="mt-5 flex justify-center gap-3">
              <button
                onClick={retry}
                className="flex items-center gap-1.5 px-5 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-700 transition-colors"
              >
                <RefreshCw size={14} />
                Retry
              </button>
              <button
                onClick={reset}
                className="flex items-center gap-1.5 px-5 py-2.5 bg-[#fff6e9] border border-slate-200 text-[#4a3c2e] rounded-xl text-sm font-medium hover:bg-[#f5ecdb] transition-colors"
              >
                <ArrowLeft size={14} />
                Start over
              </button>
            </div>
          </div>
        );

      default:
        return <UploadZone onUpload={uploadFile} />;
    }
  };

  return (
    <div className="relative flex flex-col items-center min-h-full py-14 px-4 overflow-hidden">
      <LeafBackground />

      {/* Hero — word-by-word spring + blur entrance */}
      <div className="relative z-10 text-center max-w-3xl mb-12 pt-6">
        <HeroHeading />
        <HeroSubheading />
      </div>

      {/* Upload widget */}
      <div className="relative z-10 w-full max-w-2xl">{renderContent()}</div>

      {/* Agent Collective — only on idle state */}
      {uploadState === "idle" && <AgentVillage />}
    </div>
  );
}
