/**
 * Multi-step progress indicator for upload and processing.
 * Implements FRD 2 Section 2.3 - UploadProgress.
 */

import { useState, useEffect } from "react";
import { Upload, FileSearch, Database, Check, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ReportStatus } from "@/types/report";

interface UploadProgressProps {
  filename: string;
  fileSizeBytes: number;
  status: ReportStatus;
  errorMessage?: string | null;
  startedAt: Date;
}

interface Step {
  id: number;
  label: string;
  description: string;
  icon: typeof Upload;
}

const STEPS: Step[] = [
  { id: 1, label: "Uploading",  description: "Transferring file to server", icon: Upload     },
  { id: 2, label: "Parsing",   description: "Extracting PDF content",      icon: FileSearch  },
  { id: 3, label: "Embedding", description: "Indexing for analysis",       icon: Database    },
];

function getActiveStep(status: ReportStatus): number {
  switch (status) {
    case "uploaded":   return 1;
    case "parsing":    return 2;
    case "embedding":  return 3;
    case "parsed":     return 4;
    case "error":      return -1;
    default:           return 1;
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024)        return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatElapsedTime(startedAt: Date): string {
  const elapsed = Math.floor((Date.now() - startedAt.getTime()) / 1000);
  if (elapsed < 60) return `${elapsed}s`;
  return `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`;
}

export function UploadProgress({
  filename,
  fileSizeBytes,
  status,
  errorMessage,
  startedAt,
}: UploadProgressProps) {
  const [elapsedTime, setElapsedTime] = useState("0s");
  const activeStep = getActiveStep(status);
  const isError    = status === "error";
  const isComplete = status === "parsed";

  useEffect(() => {
    if (isComplete || isError) return;
    const interval = setInterval(() => setElapsedTime(formatElapsedTime(startedAt)), 1000);
    setElapsedTime(formatElapsedTime(startedAt));
    return () => clearInterval(interval);
  }, [startedAt, isComplete, isError]);

  return (
    <div className="w-full max-w-xl mx-auto">
      <div className="glass-card p-6">
        {/* File header */}
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[#e0d4bf]">
          <div className="w-10 h-10 rounded-xl bg-[#f5ecdb] border border-[#eddfc8] flex items-center justify-center">
            <FileSearch className="w-5 h-5 text-[#6b5344]" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-[#4a3c2e] truncate">{filename}</p>
            <p className="text-xs text-[#8b7355]">{formatFileSize(fileSizeBytes)}</p>
          </div>
          {!isComplete && !isError && (
            <span className="text-xs text-[#8b7355]">{elapsedTime}</span>
          )}
        </div>

        {/* Steps */}
        <div className="space-y-4">
          {STEPS.map((step) => {
            const isActive    = activeStep === step.id;
            const isCompleted = activeStep > step.id;
            const Icon        = step.icon;

            return (
              <div key={step.id} className="flex items-center gap-4">
                <div className={cn(
                  "w-9 h-9 rounded-full flex items-center justify-center transition-all border",
                  isCompleted                 && "bg-emerald-50 border-emerald-100",
                  isActive && !isError        && "bg-[#f5ecdb] border-[#e0d4bf]",
                  isError  && isActive        && "bg-rose-50 border-rose-100",
                  !isCompleted && !isActive   && "bg-[#f5ecdb] border-[#eddfc8]"
                )}>
                  {isCompleted ? (
                    <Check className="w-4 h-4 text-emerald-600" />
                  ) : isActive && !isError ? (
                    <Loader2 className="w-4 h-4 text-[#4a3c2e] animate-spin" />
                  ) : isError && isActive ? (
                    <AlertCircle className="w-4 h-4 text-rose-500" />
                  ) : (
                    <Icon className="w-4 h-4 text-[#c8a97a]" />
                  )}
                </div>

                <div className="flex-1">
                  <p className={cn(
                    "text-sm font-medium transition-colors",
                    isCompleted             && "text-emerald-600",
                    isActive && !isError    && "text-[#4a3c2e]",
                    isError  && isActive    && "text-rose-600",
                    !isCompleted && !isActive && "text-[#c8a97a]"
                  )}>
                    {step.label}{isActive && !isError && "…"}
                  </p>
                  <p className="text-xs text-[#8b7355]">{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Error */}
        {isError && errorMessage && (
          <div className="mt-5 p-4 rounded-xl bg-rose-50 border border-rose-100">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-rose-700">Processing failed</p>
                <p className="text-xs text-rose-500 mt-0.5">{errorMessage}</p>
              </div>
            </div>
          </div>
        )}

        {/* Success */}
        {isComplete && (
          <div className="mt-5 p-3 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-600" />
            <p className="text-sm font-medium text-emerald-700">Processing complete</p>
          </div>
        )}
      </div>
    </div>
  );
}
