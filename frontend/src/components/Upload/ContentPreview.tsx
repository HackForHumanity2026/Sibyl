/**
 * Content structure preview after parsing.
 * Implements FRD 2 Section 2.4 - ContentPreview.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, ChevronRight, ChevronDown, BookOpen, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
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
    <ul className={cn("space-y-0.5", level > 0 && "ml-4 mt-0.5")}>
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
      ? `${section.page_start}–${section.page_end}`
      : `${section.page_start}`;

  return (
    <li>
      <div
        className={cn(
          "flex items-center gap-2 py-1 px-2 rounded-md transition-colors",
          hasChildren && "cursor-pointer hover:bg-[#f5ecdb]"
        )}
        onClick={() => hasChildren && setIsExpanded(!isExpanded)}
      >
        {hasChildren ? (
          isExpanded
            ? <ChevronDown className="w-3.5 h-3.5 text-[#8b7355] shrink-0" />
            : <ChevronRight className="w-3.5 h-3.5 text-[#8b7355] shrink-0" />
        ) : (
          <span className="w-3.5 shrink-0" />
        )}

        <BookOpen className={cn(
          "w-3.5 h-3.5 shrink-0",
          section.level === 1 ? "text-[#4a3c2e]" : "text-slate-300"
        )} />

        <span className={cn(
          "flex-1 truncate text-sm",
          section.level === 1 ? "font-medium text-slate-700" : "text-[#6b5344]"
        )}>
          {section.title}
        </span>

        <span className="text-xs text-slate-300 shrink-0 font-mono">p.{pageRange}</span>
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

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="glass-card overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-slate-100">
          <div className="flex items-start gap-4">
            <div className="w-11 h-11 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center shrink-0">
              <FileText className="w-5 h-5 text-emerald-600" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-slate-800 truncate">{filename}</h3>
              <p className="text-xs text-[#8b7355] mt-0.5">
                {pageCount} pages · {totalSections} sections · {contentStructure.table_count} tables ·{" "}
                ~{contentStructure.estimated_word_count.toLocaleString()} words
              </p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 divide-x divide-slate-100 border-b border-slate-100">
          {[
            { label: "Pages",    value: pageCount },
            { label: "Sections", value: totalSections },
            { label: "Tables",   value: contentStructure.table_count },
          ].map(({ label, value }) => (
            <div key={label} className="p-4 text-center">
              <div className="text-2xl font-bold text-slate-800">{value}</div>
              <div className="text-xs text-[#8b7355]">{label}</div>
            </div>
          ))}
        </div>

        {/* Section tree */}
        {contentStructure.sections.length > 0 && (
          <div className="p-4 max-h-72 overflow-y-auto">
            <p className="text-xs font-medium text-[#8b7355] uppercase tracking-wide mb-2">
              Document Structure
            </p>
            <SectionTree sections={contentStructure.sections} />
          </div>
        )}

        {/* CTA */}
        <div className="p-4 bg-[#f5ecdb] border-t border-slate-100">
          <button
            onClick={() => navigate(`/analysis/${reportId}`)}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-slate-900 text-white text-sm font-medium hover:bg-slate-700 transition-colors"
          >
            Begin Analysis
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
