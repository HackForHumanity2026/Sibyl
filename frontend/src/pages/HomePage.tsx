/**
 * Home page with hero section and PDF upload.
 * Implements FRD 2 Section 1 - Home Page UI.
 */

import { useUpload } from "@/hooks/useUpload";
import { UploadZone, UploadProgress, ContentPreview } from "@/components/Upload";
import { LeafBackground } from "@/components/LeafBackground";
import { AgentVillage } from "@/components/AgentVillage";
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
            filename={file?.name ?? "Unknown file"}
            fileSizeBytes={file?.size ?? 0}
            status={report?.status ?? "uploaded"}
            startedAt={startedAt ?? new Date()}
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
                pageCount={report.page_count ?? 0}
              />
              <div className="flex justify-center">
                <button
                  onClick={reset}
                  className="flex items-center gap-1.5 text-sm text-[#8b7355] hover:text-slate-700 transition-colors"
                >
                  <ArrowLeft size={14} />
                  Upload another
                </button>
              </div>
            </div>
          );
        }
        return <UploadZone onUpload={uploadFile} />;

      case "error":
        return (
          <div className="w-full max-w-xl mx-auto">
            <UploadProgress
              filename={file?.name ?? "Unknown file"}
              fileSizeBytes={file?.size ?? 0}
              status="error"
              errorMessage={error}
              startedAt={startedAt ?? new Date()}
            />
            <div className="mt-5 flex justify-center gap-3">
              <button
                onClick={retry}
                className="flex items-center gap-1.5 px-5 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-700 transition-colors"
              >
                <RefreshCw size={14} />
                Retry
              </button>
              <button
                onClick={reset}
                className="flex items-center gap-1.5 px-5 py-2.5 bg-[#fff6e9] border border-slate-200 text-[#4a3c2e] rounded-xl text-sm font-medium hover:bg-[#f5ecdb] transition-colors"
              >
                <ArrowLeft size={14} />
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
    <div className="relative flex flex-col items-center min-h-full py-14 px-4 overflow-hidden">
      <LeafBackground />
      {/* Hero */}
      <div className="relative z-10 text-center max-w-3xl mb-12 pt-6">
        <h1 className="text-6xl font-bold text-slate-900 mb-5 tracking-tight leading-tight">
          The Agent Village
          <br />
          <span className="text-[#8b7355] font-light">for Sustainability</span>
        </h1>
        <p className="text-lg text-[#4a3c2e] leading-relaxed max-w-xl mx-auto">
          A village of specialised AI agents — each an expert — verify every claim in your
          sustainability report against IFRS S1/S2.
        </p>
      </div>

      {/* Upload widget */}
      <div className="relative z-10 w-full max-w-2xl">{renderContent()}</div>

      {/* Agent Village — only on idle state */}
      {uploadState === "idle" && <AgentVillage />}

    </div>
  );
}
