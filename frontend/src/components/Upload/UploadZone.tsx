/**
 * Drag-and-drop upload zone for PDF files.
 *
 * Implements FRD 2 Section 2.2 - UploadZone.
 */

import { useState, useRef, useCallback } from "react";
import { Upload, FileWarning } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadZoneProps {
  onUpload: (file: File) => void;
  disabled?: boolean;
  maxSizeMB?: number;
}

const DEFAULT_MAX_SIZE_MB = 50;

export function UploadZone({
  onUpload,
  disabled = false,
  maxSizeMB = DEFAULT_MAX_SIZE_MB,
}: UploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback(
    (file: File): string | null => {
      // Check file type
      const isPdf =
        file.type === "application/pdf" ||
        file.name.toLowerCase().endsWith(".pdf");
      if (!isPdf) {
        return "Only PDF files are accepted.";
      }

      // Check file size
      const maxBytes = maxSizeMB * 1024 * 1024;
      if (file.size > maxBytes) {
        const actualSizeMB = (file.size / (1024 * 1024)).toFixed(1);
        return `File exceeds the ${maxSizeMB}MB size limit. Your file is ${actualSizeMB}MB.`;
      }

      return null;
    },
    [maxSizeMB]
  );

  const handleFile = useCallback(
    (file: File) => {
      setError(null);
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
      onUpload(file);
    },
    [validateFile, onUpload]
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (!disabled) {
        setIsDragOver(true);
      }
    },
    [disabled]
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);

      if (disabled) return;

      const files = Array.from(e.dataTransfer.files);

      if (files.length === 0) {
        return;
      }

      if (files.length > 1) {
        setError("Please upload one file at a time.");
        return;
      }

      handleFile(files[0]);
    },
    [disabled, handleFile]
  );

  const handleClick = useCallback(() => {
    if (!disabled) {
      inputRef.current?.click();
    }
  }, [disabled]);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
      // Reset input so the same file can be selected again
      e.target.value = "";
    },
    [handleFile]
  );

  return (
    <div className="w-full max-w-xl mx-auto">
      <div
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative flex flex-col items-center justify-center p-12 rounded-xl border-2 border-dashed transition-all duration-200 cursor-pointer",
          disabled && "opacity-50 cursor-not-allowed",
          isDragOver
            ? "border-primary bg-primary/5 scale-[1.02]"
            : "border-border hover:border-primary/50 hover:bg-card/80",
          error && "border-destructive"
        )}
      >
        {/* Hidden file input */}
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleInputChange}
          disabled={disabled}
          className="hidden"
        />

        {/* Icon */}
        <div
          className={cn(
            "w-16 h-16 rounded-full flex items-center justify-center mb-4 transition-colors",
            isDragOver ? "bg-primary/20" : "bg-muted"
          )}
        >
          <Upload
            className={cn(
              "w-8 h-8 transition-colors",
              isDragOver ? "text-primary" : "text-muted-foreground"
            )}
          />
        </div>

        {/* Text */}
        <p className="text-lg font-medium text-foreground mb-1">
          {isDragOver ? "Drop to upload" : "Drop a sustainability report PDF here"}
        </p>
        <p className="text-sm text-muted-foreground mb-4">or click to browse</p>

        {/* File size note */}
        <p className="text-xs text-muted-foreground">
          PDF files up to {maxSizeMB}MB
        </p>
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-4 flex items-center gap-2 p-3 rounded-lg bg-destructive/10 text-destructive">
          <FileWarning className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}
