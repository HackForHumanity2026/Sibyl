/**
 * Content structure preview after parsing.
 * Implements FRD 2 Section 2.4 - ContentPreview.
 *
 * Redesigned: clean hierarchy, no redundant stats grid, warm colors throughout.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronRight, ChevronDown, ArrowRight } from "lucide-react";
import type { ContentStructure, SectionInfo } from "@/types/report";

interface ContentPreviewProps {
  reportId: string;
  filename: string;
  contentStructure: ContentStructure;
  pageCount: number;
}

interface SectionTreeProps {
  sections: SectionInfo[];
  level?: number;
}

function SectionTree({ sections, level = 0 }: SectionTreeProps) {
  return (
    <ul style={{ listStyle: "none", margin: 0, padding: 0, paddingLeft: level > 0 ? "1rem" : 0 }}>
      {sections.map((section, index) => (
        <SectionItem key={`${level}-${index}`} section={section} />
      ))}
    </ul>
  );
}

function SectionItem({ section }: { section: SectionInfo }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasChildren = section.children && section.children.length > 0;
  const pageRange =
    section.page_end && section.page_end !== section.page_start
      ? `p.${section.page_start}–${section.page_end}`
      : `p.${section.page_start}`;

  return (
    <li>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          padding: "0.3rem 0",
          borderLeft: section.level === 1 ? "2px solid #e0d4bf" : "2px solid transparent",
          paddingLeft: "0.5rem",
          cursor: hasChildren ? "pointer" : "default",
        }}
        onClick={() => hasChildren && setIsExpanded(!isExpanded)}
      >
        {hasChildren ? (
          isExpanded
            ? <ChevronDown style={{ width: "12px", height: "12px", color: "#8b7355", flexShrink: 0 }} />
            : <ChevronRight style={{ width: "12px", height: "12px", color: "#8b7355", flexShrink: 0 }} />
        ) : (
          <span style={{ width: "12px", flexShrink: 0 }} />
        )}

        <span
          style={{
            flex: 1,
            fontSize: "13px",
            color: section.level === 1 ? "#4a3c2e" : "#6b5344",
            fontWeight: section.level === 1 ? 500 : 400,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {section.title}
        </span>

        <span style={{ fontSize: "11px", color: "#c8a97a", flexShrink: 0, fontVariantNumeric: "tabular-nums" }}>
          {pageRange}
        </span>
      </div>

      {hasChildren && isExpanded && (
        <SectionTree sections={section.children} level={section.level} />
      )}
    </li>
  );
}

function countAllSections(sections: SectionInfo[]): number {
  let count = sections.length;
  for (const section of sections) {
    if (section.children) count += countAllSections(section.children);
  }
  return count;
}

export function ContentPreview({
  reportId,
  filename,
  contentStructure,
  pageCount,
}: ContentPreviewProps) {
  const navigate = useNavigate();
  const totalSections = countAllSections(contentStructure.sections);
  const wordCount = contentStructure.estimated_word_count;

  return (
    <div style={{ width: "100%", maxWidth: "520px", margin: "0 auto" }}>
      <div className="glass-card" style={{ overflow: "hidden" }}>

        {/* ── Hero header: filename + stats ── */}
        <div style={{ padding: "1.5rem 1.5rem 1rem" }}>
          <h3
            style={{
              fontSize: "1.0625rem",
              fontWeight: 600,
              color: "#4a3c2e",
              margin: "0 0 0.5rem",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {filename}
          </h3>

          {/* Inline stat pills */}
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            {[
              { label: "pages", value: pageCount },
              { label: "sections", value: totalSections },
              ...(contentStructure.table_count > 0 ? [{ label: "tables", value: contentStructure.table_count }] : []),
              { label: "words", value: `~${wordCount.toLocaleString()}` },
            ].map(({ label, value }) => (
              <span
                key={label}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.2rem",
                  padding: "0.2rem 0.6rem",
                  background: "#f5ecdb",
                  borderRadius: "9999px",
                  fontSize: "12px",
                  color: "#6b5344",
                  fontWeight: 500,
                }}
              >
                <strong style={{ color: "#4a3c2e" }}>{value}</strong> {label}
              </span>
            ))}
          </div>
        </div>

        {/* ── Section tree ── */}
        {contentStructure.sections.length > 0 && (
          <div
            style={{
              padding: "0 1.5rem 1rem",
              maxHeight: "260px",
              overflowY: "auto",
              borderTop: "1px solid #e0d4bf",
            }}
          >
            <p
              style={{
                fontSize: "10px",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                color: "#8b7355",
                margin: "0.875rem 0 0.5rem",
              }}
            >
              Document Structure
            </p>
            <SectionTree sections={contentStructure.sections} />
          </div>
        )}

        {/* ── CTA ── */}
        <div style={{ padding: "1rem 1.5rem" }}>
          <button
            onClick={() => navigate(`/analysis/${reportId}`)}
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.5rem",
              padding: "0.75rem 1.5rem",
              background: "#4a3c2e",
              color: "#fff6e9",
              border: "none",
              borderRadius: "10px",
              fontSize: "0.875rem",
              fontWeight: 500,
              cursor: "pointer",
              transition: "background 0.15s",
            }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "#6b5344"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "#4a3c2e"; }}
          >
            Begin Analysis
            <ArrowRight style={{ width: "16px", height: "16px" }} />
          </button>
        </div>

      </div>
    </div>
  );
}
