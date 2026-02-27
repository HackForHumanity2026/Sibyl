/**
 * AnalysisListPage - Shows all past analyses (reports that were analysed).
 * Futuristic centered layout with entrance animations.
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
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
        setReports(list.filter((r) => r.status !== "error"));
      })
      .catch((err) => console.error("Failed to load analyses:", err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div
      style={{
        minHeight: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        paddingTop: "clamp(2rem, 5vh, 3.5rem)",
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
        style={{ textAlign: "center", marginBottom: "2.5rem" }}
      >
        <h1
          style={{
            fontSize: "2.75rem",
            fontWeight: 800,
            color: "#4a3c2e",
            margin: 0,
            letterSpacing: "-0.03em",
            lineHeight: 1.1,
          }}
        >
          Analyses
        </h1>
        <p
          style={{
            fontSize: "0.9375rem",
            color: "#8b7355",
            marginTop: "0.6rem",
          }}
        >
          All reports with active or completed analysis runs.
        </p>
      </motion.div>

      {/* List container */}
      <div style={{ width: "100%", maxWidth: "560px", padding: "0 1.5rem" }}>
        {loading ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ display: "flex", alignItems: "center", gap: "0.5rem", justifyContent: "center", padding: "3rem 0", color: "#8b7355", fontSize: "0.875rem" }}
          >
            <div style={{ width: "16px", height: "16px", border: "2px solid #e0d4bf", borderTopColor: "#8b7355", borderRadius: "50%", animation: "spin 0.9s linear infinite" }} />
            Loading…
          </motion.div>
        ) : reports.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            style={{ textAlign: "center", padding: "4rem 0" }}
          >
            <FlaskConical size={36} style={{ margin: "0 auto 0.75rem", color: "#e0d4bf" }} />
            <p style={{ fontSize: "0.875rem", color: "#8b7355" }}>No analyses yet.</p>
            <p style={{ fontSize: "0.75rem", color: "#c8a97a", marginTop: "0.25rem" }}>
              Upload a report on the home page to start an analysis.
            </p>
          </motion.div>
        ) : (
          /* Each item animated individually */
          <div>
            {reports.map((r, i) => (
              <motion.button
                key={r.report_id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.22, ease: "easeOut", delay: i * 0.05 }}
                onClick={() => navigate(`/analysis/${r.report_id}`)}
                className="analysis-list-item"
                style={{
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.85rem 1rem",
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  textAlign: "left",
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.15rem", flexWrap: "wrap" }}>
                    <span
                      className="analysis-list-item__name"
                      style={{
                        fontSize: "0.875rem",
                        fontWeight: 500,
                        color: "#4a3c2e",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        maxWidth: "280px",
                      }}
                    >
                      {r.filename}
                    </span>
                    {r.status === "analyzing" && (
                      <span
                        style={{
                          padding: "1px 8px",
                          borderRadius: "9999px",
                          fontSize: "11px",
                          fontWeight: 600,
                          background: "#dbeafe",
                          color: "#1e40af",
                        }}
                      >
                        Analyzing
                      </span>
                    )}
                    {r.status === "complete" && (
                      <span style={{ fontSize: "11px", fontWeight: 500, color: "#10b981" }}>
                        Complete
                      </span>
                    )}
                  </div>
                  <div style={{ display: "flex", gap: "0.5rem", fontSize: "12px", color: "#8b7355" }}>
                    <span>{new Date(r.created_at).toLocaleDateString()}</span>
                    {r.page_count && <span>· {r.page_count} pages</span>}
                  </div>
                </div>
                <span style={{ fontSize: "12px", color: "#c8a97a", marginLeft: "1rem", flexShrink: 0 }}>
                  Open →
                </span>
              </motion.button>

            ))}
          </div>
        )}
      </div>
    </div>
  );
}
