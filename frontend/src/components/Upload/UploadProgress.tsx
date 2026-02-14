/**
 * Multi-step progress indicator for upload and processing.
 *
 * Implements FRD 2 Section 2.3 - UploadProgress.
 */

import { useState, useEffect } from "react";
import {
  Upload,
  FileSearch,
  Database,
  Check,
  AlertCircle,
  Loader2,
} from "lucide-react";
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
  {
    id: 1,
    label: "Uploading",
    description: "Transferring file to server",
    icon: Upload,
  },
  {
    id: 2,
    label: "Parsing",
    description: "Extracting PDF content",
    icon: FileSearch,
  },
  {
    id: 3,
    label: "Embedding",
    description: "Indexing for analysis",
    icon: Database,
  },
];

function getActiveStep(status: ReportStatus): number {
  switch (status) {
    case "uploaded":
      return 1; // Uploading complete, waiting for parsing
    case "parsing":
      return 2;
    case "embedding":
      return 3;
    case "parsed":
      return 4; // All complete
    case "error":
      return -1; // Error state
    default:
      return 1;
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatElapsedTime(startedAt: Date): string {
  const elapsed = Math.floor((Date.now() - startedAt.getTime()) / 1000);
  if (elapsed < 60) return `${elapsed}s`;
  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  return `${minutes}m ${seconds}s`;
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
  const isError = status === "error";
  const isComplete = status === "parsed";

  // Update elapsed time every second
  useEffect(() => {
    if (isComplete || isError) return;

    const interval = setInterval(() => {
      setElapsedTime(formatElapsedTime(startedAt));
    }, 1000);

    // Initial update
    setElapsedTime(formatElapsedTime(startedAt));

    return () => clearInterval(interval);
  }, [startedAt, isComplete, isError]);

  return (
    <div className="w-full max-w-xl mx-auto">
      <div className="bg-card border border-border rounded-xl p-6">
        {/* File info header */}
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <FileSearch className="w-5 h-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-foreground truncate">{filename}</p>
            <p className="text-sm text-muted-foreground">
              {formatFileSize(fileSizeBytes)}
            </p>
          </div>
          {!isComplete && !isError && (
            <div className="text-sm text-muted-foreground">{elapsedTime}</div>
          )}
        </div>

        {/* Progress steps */}
        <div className="space-y-4">
          {STEPS.map((step) => {
            const isActive = activeStep === step.id;
            const isCompleted = activeStep > step.id;
            const Icon = step.icon;

            return (
              <div key={step.id} className="flex items-center gap-4">
                {/* Step indicator */}
                <div
                  className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center transition-all",
                    isCompleted && "bg-green-500/20",
                    isActive && !isError && "bg-primary/20",
                    isError && isActive && "bg-destructive/20",
                    !isCompleted && !isActive && "bg-muted"
                  )}
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5 text-green-500" />
                  ) : isActive && !isError ? (
                    <Loader2 className="w-5 h-5 text-primary animate-spin" />
                  ) : isError && isActive ? (
                    <AlertCircle className="w-5 h-5 text-destructive" />
                  ) : (
                    <Icon className="w-5 h-5 text-muted-foreground" />
                  )}
                </div>

                {/* Step text */}
                <div className="flex-1">
                  <p
                    className={cn(
                      "font-medium transition-colors",
                      isCompleted && "text-green-500",
                      isActive && !isError && "text-primary",
                      isError && isActive && "text-destructive",
                      !isCompleted && !isActive && "text-muted-foreground"
                    )}
                  >
                    {step.label}
                    {isActive && !isError && !isCompleted && "..."}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {step.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Error message */}
        {isError && errorMessage && (
          <div className="mt-6 p-4 rounded-lg bg-destructive/10 border border-destructive/20">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-destructive">Processing failed</p>
                <p className="text-sm text-destructive/80 mt-1">{errorMessage}</p>
              </div>
            </div>
          </div>
        )}

        {/* Success message */}
        {isComplete && (
          <div className="mt-6 p-4 rounded-lg bg-green-500/10 border border-green-500/20">
            <div className="flex items-center gap-3">
              <Check className="w-5 h-5 text-green-500" />
              <p className="font-medium text-green-500">
                Processing complete!
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
