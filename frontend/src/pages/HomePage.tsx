/**
 * Home page with hero section and PDF upload.
 *
 * Implements FRD 2 Section 1 - Home Page UI.
 */

import { useUpload } from "@/hooks/useUpload";
import { UploadZone, UploadProgress, ContentPreview } from "@/components/Upload";
import { RefreshCw, ArrowLeft } from "lucide-react";

export function HomePage() {
  const {
    uploadState,
    report,
    error,
    file,
    startedAt,
    uploadFile,
    retry,
    reset,
  } = useUpload();

  const renderContent = () => {
    switch (uploadState) {
      case "idle":
        return <UploadZone onUpload={uploadFile} />;

      case "uploading":
      case "processing":
        return (
          <UploadProgress
            filename={file?.name || "Unknown file"}
            fileSizeBytes={file?.size || 0}
            status={report?.status || "uploaded"}
            startedAt={startedAt || new Date()}
          />
        );

      case "complete":
        if (report?.content_structure) {
          return (
            <div className="space-y-4">
              <ContentPreview
                reportId={report.report_id}
                filename={report.filename}
                contentStructure={report.content_structure}
                pageCount={report.page_count || 0}
              />
              <div className="flex justify-center">
                <button
                  onClick={reset}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Upload another report
                </button>
              </div>
            </div>
          );
        }
        // Fallback if no content structure
        return <UploadZone onUpload={uploadFile} />;

      case "error":
        return (
          <div className="w-full max-w-xl mx-auto">
            <UploadProgress
              filename={file?.name || "Unknown file"}
              fileSizeBytes={file?.size || 0}
              status="error"
              errorMessage={error}
              startedAt={startedAt || new Date()}
            />
            <div className="mt-6 flex justify-center gap-4">
              <button
                onClick={retry}
                className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Retry
              </button>
              <button
                onClick={reset}
                className="flex items-center gap-2 px-6 py-2.5 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Start over
              </button>
            </div>
          </div>
        );

      default:
        return <UploadZone onUpload={uploadFile} />;
    }
  };

  return (
    <div className="flex flex-col items-center min-h-full py-12 px-4">
      {/* Hero Section */}
      <div className="text-center max-w-3xl mb-12">
        <h1 className="text-5xl font-bold text-foreground mb-4 tracking-tight">
          Sibyl
        </h1>
        <p className="text-xl text-primary mb-6">
          AI-Powered Sustainability Report Verification
        </p>
        <p className="text-muted-foreground leading-relaxed">
          Upload a sustainability report PDF and let our multi-agent AI system verify
          its claims against real-world evidence. Sibyl extracts verifiable claims,
          dispatches investigative agents across satellite imagery, regulatory databases,
          news archives, and academic research, then produces a comprehensive IFRS S1/S2
          compliance mapping with a disclosure gap analysis.
        </p>
      </div>

      {/* Upload Section */}
      <div className="w-full max-w-2xl">{renderContent()}</div>

      {/* Feature highlights (only show in idle state) */}
      {uploadState === "idle" && (
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl">
          <div className="text-center">
            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-primary"
              >
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
              </svg>
            </div>
            <h3 className="font-semibold text-foreground mb-2">Claim Extraction</h3>
            <p className="text-sm text-muted-foreground">
              Automatically identifies verifiable sustainability claims from your report
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-primary"
              >
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.3-4.3" />
              </svg>
            </div>
            <h3 className="font-semibold text-foreground mb-2">Multi-Agent Investigation</h3>
            <p className="text-sm text-muted-foreground">
              Specialized AI agents verify claims against diverse real-world sources
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-primary"
              >
                <path d="M9 11a3 3 0 1 0 6 0a3 3 0 0 0 -6 0" />
                <path d="M17.2 20.4l-1.9 -3.2a9 9 0 1 1 -6.6 0l-1.9 3.2" />
              </svg>
            </div>
            <h3 className="font-semibold text-foreground mb-2">IFRS Compliance Mapping</h3>
            <p className="text-sm text-muted-foreground">
              Paragraph-level mapping to IFRS S1/S2 with disclosure gap analysis
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
