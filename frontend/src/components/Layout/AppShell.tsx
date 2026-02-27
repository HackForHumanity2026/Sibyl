import { useState, useCallback } from "react";
import { Outlet, useParams, useNavigate } from "react-router-dom";
import { Header } from "./Header";
import { ChatPanel, ChatFab } from "@/components/Chatbot";
import type { Citation } from "@/types/chat";

export function AppShell() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const { reportId } = useParams<{ reportId?: string }>();
  const navigate = useNavigate();

  // Handle citation click - navigate to appropriate page/section
  const handleCitationClick = useCallback(
    (citation: Citation) => {
      const { navigation_target, source_id } = citation;

      switch (navigation_target) {
        case "pdf_viewer":
          if (reportId) {
            navigate(`/analysis/${reportId}?highlight=${source_id}`);
          }
          break;
        case "finding_panel":
          if (reportId) {
            navigate(`/analysis/${reportId}?finding=${source_id}`);
          }
          break;
        case "source_of_truth":
          if (reportId) {
            navigate(`/report/${reportId}?claim=${source_id}`);
          }
          break;
        case "disclosure_gaps":
          if (reportId) {
            navigate(`/report/${reportId}?section=gaps`);
          }
          break;
        case "ifrs_viewer":
          console.log("IFRS citation clicked:", citation);
          break;
      }
    },
    [reportId, navigate]
  );

  // Determine if chat should be shown (only when a report is selected)
  const showChat = Boolean(reportId);

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Horizontal top navigation */}
      <Header />

      {/* Page content — scrolls by default; AnalysisPage pins its own height */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>

      {/* Chat FAB - only show when report is selected */}
      {showChat && (
        <ChatFab
          isOpen={isChatOpen}
          onClick={() => setIsChatOpen(!isChatOpen)}
        />
      )}

      {/* Chat Panel */}
      <ChatPanel
        reportId={reportId}
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        onCitationClick={handleCitationClick}
      />
    </div>
  );
}
