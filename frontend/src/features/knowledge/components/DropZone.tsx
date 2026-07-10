"use client";

import React, { useCallback, useRef, useState } from "react";
import { Upload, FileText, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { apiClient } from "@/config/axios";
import { useToast } from "@/components/ui/toast";
import type { Document } from "@/types/knowledge";

interface DropZoneProps {
  onUploadSuccess: (doc: Document) => void;
}

const ACCEPTED_TYPES: Record<string, string> = {
  "application/pdf": "PDF",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
  "text/plain": "TXT",
  "text/markdown": "MD",
  "text/x-markdown": "MD",
};

const MAX_SIZE_MB = 25;

type DropState = "idle" | "hover" | "uploading" | "success" | "error";

export default function DropZone({ onUploadSuccess }: DropZoneProps) {
  const [dropState, setDropState] = useState<DropState>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const validateFile = (file: File): string | null => {
    if (!ACCEPTED_TYPES[file.type]) {
      return `Unsupported file type. Please upload PDF, DOCX, TXT, or Markdown.`;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File exceeds the ${MAX_SIZE_MB}MB limit.`;
    }
    return null;
  };

  const uploadFile = useCallback(
    async (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        setDropState("error");
        setErrorMsg(validationError);
        return;
      }

      setDropState("uploading");
      setErrorMsg(null);
      setProgress(0);

      const formData = new FormData();
      formData.append("file", file);

      try {
        // Simulate incremental progress
        const progressInterval = setInterval(() => {
          setProgress((p) => Math.min(p + 8, 85));
        }, 200);

        const res = await apiClient.post<{ message: string; data: Document }>(
          "/knowledge/upload",
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        );

        clearInterval(progressInterval);
        setProgress(100);
        setDropState("success");
        toast(`"${file.name}" queued for processing.`, "success");
        onUploadSuccess(res.data.data);

        // Reset after 2.5 s
        setTimeout(() => {
          setDropState("idle");
          setProgress(0);
        }, 2500);
      } catch (err: unknown) {
        setDropState("error");
        const message = err instanceof Error ? err.message : "Upload failed. Please try again.";
        setErrorMsg(message);
      }
    },
    [onUploadSuccess, toast]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file) uploadFile(file);
    },
    [uploadFile]
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
    // Reset input so same file can be re-uploaded
    if (inputRef.current) inputRef.current.value = "";
  };

  const borderColor =
    dropState === "hover"
      ? "border-indigo-500"
      : dropState === "error"
        ? "border-rose-500/70"
        : dropState === "success"
          ? "border-emerald-500/70"
          : "border-slate-200/60 dark:border-slate-700/60";

  const bgColor =
    dropState === "hover"
      ? "bg-indigo-50/60 dark:bg-indigo-950/20"
      : dropState === "error"
        ? "bg-rose-50/40 dark:bg-rose-950/10"
        : dropState === "success"
          ? "bg-emerald-50/40 dark:bg-emerald-950/10"
          : "bg-slate-50/40 dark:bg-slate-900/20";

  return (
    <div
      id="knowledge-dropzone"
      onDragOver={(e) => {
        e.preventDefault();
        if (dropState === "idle") setDropState("hover");
      }}
      onDragLeave={() => {
        if (dropState === "hover") setDropState("idle");
      }}
      onDrop={handleDrop}
      onClick={() => dropState === "idle" && inputRef.current?.click()}
      className={`relative flex flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed p-10 transition-all duration-200 cursor-pointer select-none ${borderColor} ${bgColor}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.txt,.md,.markdown"
        onChange={handleFileChange}
        className="hidden"
        aria-label="Upload document"
      />

      {/* Icon */}
      <div
        className={`flex h-14 w-14 items-center justify-center rounded-2xl transition-all duration-200 ${
          dropState === "success"
            ? "bg-emerald-100 dark:bg-emerald-900/30"
            : dropState === "error"
              ? "bg-rose-100 dark:bg-rose-900/30"
              : dropState === "uploading"
                ? "bg-indigo-100 dark:bg-indigo-900/30"
                : "bg-indigo-50 dark:bg-indigo-950/30 group-hover:scale-110"
        }`}
      >
        {dropState === "uploading" && <Loader2 className="h-7 w-7 text-indigo-500 animate-spin" />}
        {dropState === "success" && <CheckCircle2 className="h-7 w-7 text-emerald-500" />}
        {dropState === "error" && <AlertCircle className="h-7 w-7 text-rose-500" />}
        {(dropState === "idle" || dropState === "hover") && (
          <Upload
            className={`h-7 w-7 transition-transform duration-200 ${
              dropState === "hover" ? "scale-110 text-indigo-500" : "text-indigo-400"
            }`}
          />
        )}
      </div>

      {/* Text */}
      {dropState === "idle" && (
        <div className="text-center">
          <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            Drag & drop a file or{" "}
            <span className="text-indigo-500 dark:text-indigo-400 underline underline-offset-2">
              browse
            </span>
          </p>
          <p className="mt-1.5 text-xs text-slate-400 dark:text-slate-500">
            PDF, DOCX, TXT, Markdown · up to {MAX_SIZE_MB}MB
          </p>
        </div>
      )}
      {dropState === "hover" && (
        <p className="text-sm font-semibold text-indigo-600 dark:text-indigo-400">
          Release to upload
        </p>
      )}
      {dropState === "uploading" && (
        <div className="w-full max-w-xs text-center">
          <p className="mb-2 text-sm font-semibold text-slate-600 dark:text-slate-400">
            Uploading…
          </p>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-200"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
      {dropState === "success" && (
        <p className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
          Uploaded! Processing queued.
        </p>
      )}
      {dropState === "error" && (
        <div className="text-center">
          <p className="text-sm font-semibold text-rose-600 dark:text-rose-400">
            {errorMsg ?? "Upload failed"}
          </p>
          <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">Click to try again</p>
        </div>
      )}

      {/* Accepted formats badge row */}
      {dropState === "idle" && (
        <div className="flex items-center gap-1.5 flex-wrap justify-center">
          {Object.values(ACCEPTED_TYPES)
            .filter((v, i, arr) => arr.indexOf(v) === i)
            .map((ext) => (
              <span
                key={ext}
                className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100/80 dark:bg-slate-800/60 text-[10px] font-bold text-slate-500 dark:text-slate-400"
              >
                <FileText className="h-2.5 w-2.5" />
                {ext}
              </span>
            ))}
        </div>
      )}
    </div>
  );
}
