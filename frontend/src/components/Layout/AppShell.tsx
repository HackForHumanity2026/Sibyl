import { useState, useCallback } from "react";
import { Outlet, useParams, useNavigate } from "react-router-dom";
import { Sidebar } from "./Sidebar";
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
          // Navigate to analysis page with claim highlight
          if (reportId) {
            navigate(`/analysis/${reportId}?highlight=${source_id}`);
          }
          break;
        case "finding_panel":
          // Navigate to analysis page findings section
          if (reportId) {
            navigate(`/analysis/${reportId}?finding=${source_id}`);
          }
          break;
        case "source_of_truth":
          // Navigate to report page
          if (reportId) {
            navigate(`/report/${reportId}?claim=${source_id}`);
          }
          break;
        case "disclosure_gaps":
          // Navigate to report page gaps section
          if (reportId) {
            navigate(`/report/${reportId}?section=gaps`);
          }
          break;
        case "ifrs_viewer":
          // For IFRS, could open a modal or link to external docs
          // For now, just log
          console.log("IFRS citation clicked:", citation);
          break;
      }
    },
    [reportId, navigate]
  );

  // Determine if chat should be shown (only when a report is selected)
  const showChat = Boolean(reportId);

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>

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
