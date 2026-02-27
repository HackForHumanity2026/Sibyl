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
import { motion } from "framer-motion";
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
    const filteredList = reportsList.filter((r) => r.status !== "error");
    return (
      <div
        style={{
          minHeight: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "flex-start",
          paddingTop: "clamp(4rem, 15vh, 8rem)",
          paddingBottom: "4rem",
          background: "#fff6e9",
          overflowY: "auto",
        }}
      >
        {/* Page heading */}
        <motion.div
          initial={{ opacity: 0, y: -14, filter: "blur(6px)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          style={{ textAlign: "center", marginBottom: "2.5rem", width: "100%", maxWidth: "560px", padding: "0 1.5rem" }}
        >
          <div style={{ display: "flex", justifyContent: "center", alignItems: "flex-start", gap: "1rem" }}>
            <div>
              <h1 style={{ fontSize: "2.75rem", fontWeight: 800, color: "#4a3c2e", margin: 0, letterSpacing: "-0.03em", lineHeight: 1.1 }}>
                Reports
              </h1>
              <p style={{ fontSize: "0.9375rem", color: "#8b7355", marginTop: "0.6rem" }}>
                IFRS S1/S2 verified claims and disclosure gap analysis.
              </p>
            </div>
            {import.meta.env.DEV && (
              <button
                onClick={handleCreateAndSeedMock}
                disabled={creatingMock}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.375rem",
                  padding: "0.4rem 0.875rem",
                  background: "#f5ecdb",
                  border: "1px solid #e0d4bf",
                  color: "#4a3c2e",
                  borderRadius: "8px",
                  fontSize: "12px",
                  fontWeight: 500,
                  cursor: "pointer",
                  flexShrink: 0,
                  marginTop: "0.25rem",
                  opacity: creatingMock ? 0.5 : 1,
                }}
              >
                <Zap size={12} />
                {creatingMock ? "Creating…" : "Mock Report"}
              </button>
            )}
          </div>
        </motion.div>

        {/* List */}
        <div style={{ width: "100%", maxWidth: "560px", padding: "0 1.5rem" }}>
          {loadingList ? (
            <div style={{ display: "flex", justifyContent: "center", padding: "4rem 0" }}>
              <Loader2 style={{ width: "24px", height: "24px", color: "#8b7355", animation: "spin 1s linear infinite" }} />
            </div>
          ) : filteredList.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              style={{ textAlign: "center", padding: "4rem 0" }}
            >
              <FileText style={{ width: "36px", height: "36px", color: "#c8a97a", margin: "0 auto 0.75rem" }} />
              <p style={{ fontSize: "0.875rem", color: "#8b7355" }}>
                No reports found. Upload a sustainability report to get started.
              </p>
            </motion.div>
          ) : (
            /* Each item animated individually */
            <div>
              {filteredList.map((r, i) => (
                <motion.a
                  key={r.report_id}
                  href={`/report/${r.report_id}`}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.22, ease: "easeOut", delay: i * 0.05 }}
                  className="report-list-item"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0.85rem 1rem",
                    textDecoration: "none",
                    cursor: "pointer",
                  }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.15rem", flexWrap: "wrap" }}>
                      <span className="report-list-item__name" style={{ fontSize: "0.875rem", fontWeight: 500, color: "#4a3c2e", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "280px" }}>
                        {r.filename}
                      </span>
                      {r.status === "analyzing" && (
                        <span style={{ padding: "1px 8px", borderRadius: "9999px", fontSize: "11px", fontWeight: 600, background: "#dbeafe", color: "#1e40af" }}>
                          Analyzing
                        </span>
                      )}
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem", fontSize: "12px", color: "#8b7355" }}>
                      <span>{new Date(r.created_at).toLocaleDateString()}</span>
                      {r.page_count && <span>· {r.page_count} pages</span>}
                    </div>
                  </div>
                  <span style={{ fontSize: "12px", color: "#c8a97a", marginLeft: "1rem", flexShrink: 0 }}>
                    View →
                  </span>
                </motion.a>
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
        <h2 className="text-lg font-semibold text-[#4a3c2e]">Failed to Load Report</h2>
        <p className="text-sm text-[#6b5344] text-center max-w-sm">{error}</p>
        <button
          onClick={refetch}
          className="px-4 py-2 bg-[#fff6e9] border border-[#e0d4bf] rounded-xl text-sm font-medium text-[#4a3c2e] hover:bg-[#f5ecdb] transition-colors shadow-sm"
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
        <FileText className="w-10 h-10 text-[#c8a97a]" />
        <h2 className="text-lg font-semibold text-[#4a3c2e]">No Report Data</h2>
        <p className="text-sm text-[#6b5344] text-center max-w-sm">
          Analysis hasn't completed yet. Refresh to check, or seed mock data to test.
        </p>
        <div className="flex gap-3">
          <button
            onClick={refetch}
            className="px-4 py-2 bg-[#fff6e9] border border-[#e0d4bf] rounded-xl text-sm font-medium text-[#4a3c2e] hover:bg-[#f5ecdb] transition-colors shadow-sm"
          >
            Refresh
          </button>
          {import.meta.env.DEV && (
            <button
              onClick={seedMock}
              disabled={seedingMock}
              className="flex items-center gap-1.5 px-4 py-2 bg-[#fff6e9] border border-[#e0d4bf] text-[#4a3c2e] rounded-xl text-sm font-medium hover:bg-[#f5ecdb] transition-colors shadow-sm disabled:opacity-50"
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
            <h1 className="text-2xl font-bold text-[#4a3c2e]">Compliance Report</h1>
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

          {/* Footer — no dividers */}
          <div className="pt-6 pb-10 text-center">
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
