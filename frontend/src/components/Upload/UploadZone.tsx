/**
 * Drag-and-drop upload zone for PDF files.
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
      const isPdf =
        file.type === "application/pdf" ||
        file.name.toLowerCase().endsWith(".pdf");
      if (!isPdf) return "Only PDF files are accepted.";
      const maxBytes = maxSizeMB * 1024 * 1024;
      if (file.size > maxBytes) {
        const actualSizeMB = (file.size / (1024 * 1024)).toFixed(1);
        return `File exceeds ${maxSizeMB} MB. Your file is ${actualSizeMB} MB.`;
      }
      return null;
    },
    [maxSizeMB]
  );

  const handleFile = useCallback(
    (file: File) => {
      setError(null);
      const err = validateFile(file);
      if (err) { setError(err); return; }
      onUpload(file);
    },
    [validateFile, onUpload]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    if (!disabled) setIsDragOver(true);
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    setIsDragOver(false);
    if (disabled) return;
    const files = Array.from(e.dataTransfer.files);
    if (files.length === 0) return;
    if (files.length > 1) { setError("Please upload one file at a time."); return; }
    handleFile(files[0]);
  }, [disabled, handleFile]);

  const handleClick = useCallback(() => {
    if (!disabled) inputRef.current?.click();
  }, [disabled]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) handleFile(files[0]);
    e.target.value = "";
  }, [handleFile]);

  return (
    <div className="w-full max-w-xl mx-auto">
      <div
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative flex flex-col items-center justify-center p-12 rounded-2xl border-2 border-dashed transition-all duration-200 cursor-pointer",
          disabled && "opacity-50 cursor-not-allowed",
          isDragOver
            ? "border-[#a08060] bg-[#f5ecdb] scale-[1.01]"
            : "border-[#c8a97a] bg-[#fff6e9] hover:border-[#a08060] hover:bg-[#f5ecdb]",
          error && "border-rose-300 bg-rose-50"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleInputChange}
          disabled={disabled}
          className="hidden"
        />

        <div className={cn(
          "w-14 h-14 rounded-full flex items-center justify-center mb-4 transition-colors border",
          isDragOver ? "bg-[#eddfc8] border-slate-200" : "bg-[#f5ecdb] border-slate-100"
        )}>
          <Upload
            className={cn("w-7 h-7 transition-colors", isDragOver ? "text-slate-700" : "text-[#8b7355]")}
          />
        </div>

        <p className="text-base font-semibold text-slate-700 mb-1">
          {isDragOver ? "Drop to upload" : "Drop a sustainability report PDF"}
        </p>
        <p className="text-sm text-[#8b7355] mb-3">or click to browse</p>
        <p className="text-xs text-[#8b7355]">PDF files up to {maxSizeMB} MB</p>
      </div>

      {error && (
        <div className="mt-3 flex items-center gap-2 p-3 rounded-xl bg-rose-50 border border-rose-100 text-rose-600">
          <FileWarning className="w-4 h-4 shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}
