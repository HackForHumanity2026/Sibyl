/**
 * AnalysisListPage - Shows all past analyses (reports that were analysed).
 * Mirrors the ReportPage list view but navigates to /analysis/:reportId.
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listReports } from "@/services/api";
import { FlaskConical } from "lucide-react";

interface ReportListItem {
  report_id: string;
  filename: string;
  status: string;
  file_size_bytes: number;
  page_count: number | null;
  created_at: string;
  updated_at: string;
}

export function AnalysisListPage() {
  const navigate = useNavigate();
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listReports()
      .then((list) => {
        // Only show reports that have been (or are being) analysed — exclude pure uploads
        setReports(list.filter((r) => r.status !== "error"));
      })
      .catch((err) => console.error("Failed to load analyses:", err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-full overflow-y-auto">
      <div className="max-w-2xl mx-auto px-6 py-10">
        {/* Page header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-1">
            <FlaskConical size={18} className="text-[#6b5344]" />
            <h1 className="text-xl font-semibold text-slate-900">Analyses</h1>
          </div>
          <p className="text-sm text-[#8b7355]">
            All uploaded reports with active or completed analysis runs.
          </p>
        </div>

        {/* List */}
        {loading ? (
          <div className="flex items-center gap-2 py-8 text-[#8b7355] text-sm">
            <div className="w-4 h-4 border-2 border-[#e0d4bf] border-t-[#8b7355] rounded-full animate-spin" />
            Loading…
          </div>
        ) : reports.length === 0 ? (
          <div className="py-16 text-center">
            <FlaskConical size={32} className="mx-auto mb-3 text-[#e0d4bf]" />
            <p className="text-sm text-[#8b7355]">No analyses yet.</p>
            <p className="text-xs text-[#c8a97a] mt-1">
              Upload a report on the home page to start an analysis.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-[#e0d4bf] border-y border-[#e0d4bf]">
            {reports.map((r) => (
              <button
                key={r.report_id}
                onClick={() => navigate(`/analysis/${r.report_id}`)}
                className="w-full flex items-center justify-between py-3 px-4 hover:bg-[#f5ecdb] transition-colors text-left group"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-0.5">
                    <span className="text-sm font-medium text-slate-800 group-hover:text-slate-900 truncate">
                      {r.filename}
                    </span>
                    {r.status === "analyzing" && (
                      <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-100">
                        Analyzing
                      </span>
                    )}
                    {r.status === "complete" && (
                      <span className="text-xs text-emerald-600 font-medium">Complete</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-[#8b7355]">
                    <span>{new Date(r.created_at).toLocaleDateString()}</span>
                    {r.page_count && <span>· {r.page_count} pages</span>}
                  </div>
                </div>
                <span className="text-xs text-[#c8a97a] group-hover:text-[#8b7355] transition-colors ml-4 shrink-0">
                  Open →
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
