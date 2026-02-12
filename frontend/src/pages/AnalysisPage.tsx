import { useParams } from "react-router-dom";

export function AnalysisPage() {
  const { reportId } = useParams<{ reportId?: string }>();

  return (
    <div className="h-full flex gap-4">
      {/* Left Panel - PDF Viewer */}
      <div className="flex-1 bg-card rounded-lg border border-border p-4">
        <h3 className="text-lg font-semibold text-foreground mb-4">
          PDF Viewer
        </h3>
        <div className="h-full flex items-center justify-center text-muted-foreground">
          {reportId ? (
            <p>PDF viewer for report {reportId} coming in FRD 4</p>
          ) : (
            <p>Upload a report to view PDF</p>
          )}
        </div>
      </div>

      {/* Center Panel - Detective Dashboard */}
      <div className="flex-1 bg-card rounded-lg border border-border p-4">
        <h3 className="text-lg font-semibold text-foreground mb-4">
          Detective Dashboard
        </h3>
        <div className="h-full flex items-center justify-center text-muted-foreground">
          <p>Agent network graph coming in FRD 12</p>
        </div>
      </div>

      {/* Right Panel - Agent Reasoning */}
      <div className="flex-1 bg-card rounded-lg border border-border p-4">
        <h3 className="text-lg font-semibold text-foreground mb-4">
          Agent Reasoning
        </h3>
        <div className="h-full flex items-center justify-center text-muted-foreground">
          <p>Live agent reasoning stream coming in FRD 5</p>
        </div>
      </div>
    </div>
  );
}
