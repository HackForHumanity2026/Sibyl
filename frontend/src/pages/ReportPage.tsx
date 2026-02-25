import { useParams } from "react-router-dom";
import { useReport } from "@/hooks/useReport";
import {
  FilterBar,
  ComplianceSummary,
  PillarSection,
  S1S2MappingSidebar,
} from "@/components/SourceOfTruth";
import type { IFRSPillar } from "@/types/ifrs";
import { Loader2, AlertCircle, FileText, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { listReports, createMockReport } from "@/services/api";

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
    seedMock,
    seedingMock,
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
  const [creatingMock, setCreatingMock] = useState(false);

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

  const handleCreateAndSeedMock = async () => {
    setCreatingMock(true);
    try {
      const { report_id } = await createMockReport();
      // Redirect to the new mock report page (seeding happens via button there)
      window.location.href = `/report/${report_id}`;
    } catch (err) {
      console.error("Failed to create mock report:", err);
    } finally {
      setCreatingMock(false);
    }
  };

  // No report ID — show reports list
  if (!reportId) {
    return (
      <div className="min-h-full overflow-y-auto">
        <div className="page-wrapper">
          <div className="mb-8 flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Compliance Reports</h1>
              <p className="text-sm text-[#6b5344] mt-1">
                IFRS S1/S2 verified claims and disclosure gap analysis
              </p>
            </div>
            {import.meta.env.DEV && (
              <button
                onClick={handleCreateAndSeedMock}
                disabled={creatingMock}
                className="shrink-0 flex items-center gap-1.5 px-4 py-2 bg-[#fff6e9] border border-slate-200 text-[#4a3c2e] rounded-xl text-sm font-medium hover:bg-[#f5ecdb] transition-colors disabled:opacity-50 shadow-sm"
              >
                <Zap size={14} />
                {creatingMock ? "Creating…" : "Create Mock Report"}
              </button>
            )}
          </div>

          {loadingList ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-6 h-6 text-[#8b7355] animate-spin" />
            </div>
          ) : reportsList.filter((r) => r.status !== "error").length === 0 ? (
            <div className="text-center py-16">
              <FileText className="w-10 h-10 text-[#c8a97a] mx-auto mb-3" />
              <p className="text-[#6b5344] text-sm">
                No reports found. Upload a sustainability report to get started.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-[#e0d4bf]">
              {reportsList
                .filter((r) => r.status !== "error")
                .map((r) => (
                  <a
                    key={r.report_id}
                    href={`/report/${r.report_id}`}
                    className="flex items-center justify-between py-4 group"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-[#4a3c2e] group-hover:text-slate-900 truncate transition-colors">
                          {r.filename}
                        </span>
                        {r.status === "analyzing" && (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-600">
                            Analyzing
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-[#8b7355] mt-0.5">
                        <span>{new Date(r.created_at).toLocaleDateString()}</span>
                        {r.page_count && <span>· {r.page_count} pages</span>}
                      </div>
                    </div>
                    <span className="text-xs text-[#8b7355] group-hover:text-[#4a3c2e] transition-colors shrink-0 ml-4">
                      View →
                    </span>
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
      <div className="h-full flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 text-[#8b7355] animate-spin" />
        <p className="text-sm text-[#8b7355]">Loading report…</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-3">
        <AlertCircle className="w-12 h-12 text-rose-300" />
        <h2 className="text-lg font-semibold text-slate-800">Failed to Load Report</h2>
        <p className="text-sm text-[#6b5344] text-center max-w-sm">{error}</p>
        <button
          onClick={refetch}
          className="px-4 py-2 bg-[#fff6e9] border border-slate-200 rounded-xl text-sm font-medium text-slate-700 hover:bg-[#f5ecdb] transition-colors shadow-sm"
        >
          Try Again
        </button>
      </div>
    );
  }

  // Empty report state
  if (!report) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-4">
        <FileText className="w-10 h-10 text-slate-300" />
        <h2 className="text-lg font-semibold text-slate-800">No Report Data</h2>
        <p className="text-sm text-[#6b5344] text-center max-w-sm">
          Analysis hasn't completed yet. Refresh to check, or seed mock data to test.
        </p>
        <div className="flex gap-3">
          <button
            onClick={refetch}
            className="px-4 py-2 bg-[#fff6e9] border border-slate-200 rounded-xl text-sm font-medium text-slate-700 hover:bg-[#f5ecdb] transition-colors shadow-sm"
          >
            Refresh
          </button>
          {import.meta.env.DEV && (
            <button
              onClick={seedMock}
              disabled={seedingMock}
              className="flex items-center gap-1.5 px-4 py-2 bg-[#fff6e9] border border-slate-200 text-[#4a3c2e] rounded-xl text-sm font-medium hover:bg-[#f5ecdb] transition-colors shadow-sm disabled:opacity-50"
            >
              <Zap size={14} />
              {seedingMock ? "Seeding…" : "Seed Mock Data"}
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full flex flex-col">
      {/* Dev banner */}
      {import.meta.env.DEV && (
        <div className="flex items-center justify-between px-6 py-2 bg-amber-50 border-b border-amber-100">
          <span className="flex items-center gap-1.5 text-xs text-amber-600">
            <Zap size={12} />
            Development mode
          </span>
          <button
            onClick={seedMock}
            disabled={seedingMock}
            className="px-3 py-1 bg-[#fff6e9] border border-amber-200 text-amber-600 rounded-lg text-xs font-medium hover:bg-amber-50 transition-colors disabled:opacity-50"
          >
            {seedingMock ? "Seeding…" : "Re-seed Mock Data"}
          </button>
        </div>
      )}

      {/* Sticky Filter Bar */}
      <FilterBar
        filters={filters}
        onFiltersChange={setFilters}
        onClearFilters={clearFilters}
      />

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="page-wrapper space-y-10">
          {/* Page title */}
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Compliance Report</h1>
            <p className="text-sm text-[#6b5344] mt-1">{report.filename}</p>
          </div>

          {/* Summary + pillar coverage */}
          <ComplianceSummary summary={report.summary} />

          {/* Pillar sections */}
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
          <div className="border-t border-slate-100 pt-6 pb-10 text-center">
            <p className="text-xs text-[#8b7355]">
              Compiled{" "}
              {new Date(report.compiled_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
              {" "}· Sibyl IFRS S1/S2 Analysis
            </p>
          </div>
        </div>
      </div>

      {/* S1/S2 Mapping Panel */}
      <S1S2MappingSidebar report={report} />
    </div>
  );
}
