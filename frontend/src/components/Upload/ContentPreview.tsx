/**
 * Content structure preview after parsing.
 *
 * Implements FRD 2 Section 2.4 - ContentPreview.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FileText,
  ChevronRight,
  ChevronDown,
  Table2,
  BookOpen,
  ArrowRight,
} from "lucide-react";
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
    <ul className={cn("space-y-1", level > 0 && "ml-4 mt-1")}>
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
      ? `pp. ${section.page_start}-${section.page_end}`
      : `p. ${section.page_start}`;

  return (
    <li>
      <div
        className={cn(
          "flex items-center gap-2 py-1.5 px-2 rounded-md transition-colors",
          hasChildren && "cursor-pointer hover:bg-muted/50"
        )}
        onClick={() => hasChildren && setIsExpanded(!isExpanded)}
      >
        {/* Expand/collapse icon */}
        {hasChildren ? (
          isExpanded ? (
            <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />
          ) : (
            <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
          )
        ) : (
          <span className="w-4 flex-shrink-0" />
        )}

        {/* Section icon based on level */}
        <BookOpen
          className={cn(
            "w-4 h-4 flex-shrink-0",
            section.level === 1
              ? "text-primary"
              : section.level === 2
                ? "text-primary/70"
                : "text-muted-foreground"
          )}
        />

        {/* Section title */}
        <span
          className={cn(
            "flex-1 truncate",
            section.level === 1
              ? "font-medium text-foreground"
              : "text-muted-foreground"
          )}
        >
          {section.title}
        </span>

        {/* Page numbers */}
        <span className="text-xs text-muted-foreground flex-shrink-0">
          {pageRange}
        </span>
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <SectionTree sections={section.children} level={section.level} />
      )}
    </li>
  );
}

function countAllSections(sections: SectionInfo[]): number {
  let count = sections.length;
  for (const section of sections) {
    if (section.children) {
      count += countAllSections(section.children);
    }
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

  const handleBeginAnalysis = () => {
    navigate(`/analysis/${reportId}`);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-border">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-lg bg-green-500/10 flex items-center justify-center flex-shrink-0">
              <FileText className="w-6 h-6 text-green-500" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-lg text-foreground truncate">
                {filename}
              </h3>
              <p className="text-sm text-muted-foreground mt-1">
                {pageCount} pages · {totalSections} sections ·{" "}
                {contentStructure.table_count} tables
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                ~{contentStructure.estimated_word_count.toLocaleString()} words
              </p>
            </div>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 divide-x divide-border border-b border-border">
          <div className="p-4 text-center">
            <div className="text-2xl font-bold text-foreground">{pageCount}</div>
            <div className="text-xs text-muted-foreground">Pages</div>
          </div>
          <div className="p-4 text-center">
            <div className="text-2xl font-bold text-foreground">
              {totalSections}
            </div>
            <div className="text-xs text-muted-foreground">Sections</div>
          </div>
          <div className="p-4 text-center">
            <div className="flex items-center justify-center gap-1">
              <Table2 className="w-5 h-5 text-muted-foreground" />
              <span className="text-2xl font-bold text-foreground">
                {contentStructure.table_count}
              </span>
            </div>
            <div className="text-xs text-muted-foreground">Tables</div>
          </div>
        </div>

        {/* Section tree */}
        {contentStructure.sections.length > 0 && (
          <div className="p-4 max-h-80 overflow-y-auto">
            <p className="text-sm font-medium text-muted-foreground mb-3">
              Document Structure
            </p>
            <SectionTree sections={contentStructure.sections} />
          </div>
        )}

        {/* Action button */}
        <div className="p-4 bg-muted/30 border-t border-border">
          <button
            onClick={handleBeginAnalysis}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors"
          >
            Begin Analysis
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
