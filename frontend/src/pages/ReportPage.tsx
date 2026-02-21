import { useParams } from "react-router-dom";
import { useReport } from "@/hooks/useReport";
import {
  FilterBar,
  ComplianceSummary,
  PillarSection,
  S1S2MappingSidebar,
} from "@/components/SourceOfTruth";
import type { IFRSPillar } from "@/types/ifrs";
import { Loader2, AlertCircle, FileText, ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import { listReports } from "@/services/api";

const PILLAR_ORDER: IFRSPillar[] = [
  "governance",
  "strategy",
  "risk_management",
  "metrics_targets",
];

export function ReportPage() {
  const { reportId } = useParams<{ reportId?: string }>();
  
  const {
    report,
    loading,
    error,
    filteredClaims,
    filteredGaps,
    filters,
    setFilters,
    clearFilters,
    refetch,
  } = useReport(reportId);

  const [reportsList, setReportsList] = useState<
    Array<{
      report_id: string;
      filename: string;
      status: string;
      file_size_bytes: number;
      page_count: number | null;
      created_at: string;
      updated_at: string;
    }>
  >([]);
  const [loadingList, setLoadingList] = useState(false);

  // Fetch reports list when no reportId is provided
  useEffect(() => {
    if (!reportId) {
      setLoadingList(true);
      listReports()
        .then(setReportsList)
        .catch((err) => console.error("Failed to load reports:", err))
        .finally(() => setLoadingList(false));
    }
  }, [reportId]);

  // No report ID provided - show reports list
  if (!reportId) {
    return (
      <div className="h-full flex flex-col overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-8 w-full">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">
              Source of Truth Reports
            </h1>
            <p className="text-muted-foreground">
              View compliance reports organized by IFRS S1/S2 pillars with verified claims and disclosure gaps.
            </p>
          </div>

          {/* Reports List */}
          {loadingList ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
          ) : reportsList.length === 0 ? (
            <div className="text-center py-12 border border-border rounded-lg bg-muted/30">
              <FileText className="w-12 h-12 text-muted-foreground/50 mx-auto mb-3" />
              <p className="text-muted-foreground">
                No reports found. Upload a sustainability report to get started.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {reportsList.map((r) => (
                <a
                  key={r.report_id}
                  href={`/report/${r.report_id}`}
                  className="block p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors truncate">
                          {r.filename}
                        </h3>
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-medium ${
                            r.status === "completed"
                              ? "bg-green-500/20 text-green-400"
                              : r.status === "analyzing"
                              ? "bg-blue-500/20 text-blue-400"
                              : "bg-yellow-500/20 text-yellow-400"
                          }`}
                        >
                          {r.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>
                          Created: {new Date(r.created_at).toLocaleDateString()}
                        </span>
                        {r.page_count && <span>{r.page_count} pages</span>}
                        {r.status === "completed" && (
                          <span>
                            Updated:{" "}
                            {new Date(r.updated_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                    <ExternalLink className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0 ml-4" />
                  </div>
                </a>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Loading state
  if (loading && !report) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
        <p className="text-muted-foreground">Loading report...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <AlertCircle className="w-16 h-16 text-destructive/50 mb-4" />
        <h2 className="text-xl font-semibold text-foreground mb-2">
          Failed to Load Report
        </h2>
        <p className="text-muted-foreground text-center max-w-md mb-4">
          {error}
        </p>
        <button
          onClick={refetch}
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  // Empty report state
  if (!report) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <FileText className="w-16 h-16 text-muted-foreground/50 mb-4" />
        <h2 className="text-xl font-semibold text-foreground mb-2">
          No Report Data
        </h2>
        <p className="text-muted-foreground text-center max-w-md mb-4">
          This report doesn't have any analyzed claims yet. Please wait for the analysis
          pipeline to complete.
        </p>
        <button
          onClick={refetch}
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted transition-colors"
        >
          Refresh
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Sticky Filter Bar */}
      <FilterBar
        filters={filters}
        onFiltersChange={setFilters}
        onClearFilters={clearFilters}
      />

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-6 space-y-8">
          {/* Compliance Summary */}
          <ComplianceSummary summary={report.summary} />

          {/* Pillar Sections */}
          {PILLAR_ORDER.map((pillar) => (
            <PillarSection
              key={pillar}
              pillar={pillar}
              claims={filteredClaims[pillar]}
              gaps={filteredGaps[pillar]}
              summary={report.pillars[pillar].summary}
              reportId={reportId}
            />
          ))}

          {/* Footer */}
          <div className="border-t border-border pt-6 pb-8 text-center text-sm text-muted-foreground">
            <p>
              Report compiled{" "}
              {new Date(report.compiled_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
            <p className="mt-1">
              Sibyl ESG Compliance Platform • IFRS S1/S2 Analysis
            </p>
          </div>
        </div>
      </div>

      {/* S1/S2 Mapping Sidebar */}
      <S1S2MappingSidebar report={report} />
    </div>
  );
}
