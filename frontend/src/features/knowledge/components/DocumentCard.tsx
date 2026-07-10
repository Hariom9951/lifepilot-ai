"use client";

import React, { useState } from "react";
import {
  FileText,
  FileType2,
  File,
  Trash2,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Clock,
} from "lucide-react";
import { apiClient } from "@/config/axios";
import { useToast } from "@/components/ui/toast";
import type { Document, DocumentStatus } from "@/types/knowledge";

interface DocumentCardProps {
  document: Document;
  onDeleted: (id: string) => void;
}

const STATUS_CONFIG: Record<
  DocumentStatus,
  { label: string; color: string; icon: React.ReactNode }
> = {
  uploaded: {
    label: "Uploaded",
    color: "text-sky-600 dark:text-sky-400 bg-sky-50 dark:bg-sky-950/30 border-sky-200/60 dark:border-sky-800/40",
    icon: <Clock className="h-3 w-3" />,
  },
  processing: {
    label: "Processing",
    color: "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/30 border-amber-200/60 dark:border-amber-800/40",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  ready: {
    label: "Ready",
    color: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200/60 dark:border-emerald-800/40",
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  failed: {
    label: "Failed",
    color: "text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/30 border-rose-200/60 dark:border-rose-800/40",
    icon: <AlertTriangle className="h-3 w-3" />,
  },
};

const MIME_ICONS: Record<string, React.ReactNode> = {
  "application/pdf": <FileType2 className="h-5 w-5 text-rose-400" />,
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
    <FileText className="h-5 w-5 text-sky-400" />
  ),
  "text/plain": <File className="h-5 w-5 text-slate-400" />,
  "text/markdown": <File className="h-5 w-5 text-indigo-400" />,
  "text/x-markdown": <File className="h-5 w-5 text-indigo-400" />,
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function DocumentCard({ document: doc, onDeleted }: DocumentCardProps) {
  const [deleting, setDeleting] = useState(false);
  const { toast } = useToast();
  const status = STATUS_CONFIG[doc.status];

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Delete "${doc.original_filename}"? This cannot be undone.`)) return;

    setDeleting(true);
    try {
      await apiClient.delete(`/knowledge/${doc.id}`);
      onDeleted(doc.id);
      toast(`"${doc.original_filename}" deleted.`, "info");
    } catch {
      toast("Failed to delete document.", "error");
      setDeleting(false);
    }
  };

  return (
    <div
      id={`document-card-${doc.id}`}
      className="group flex items-center gap-4 rounded-xl border border-slate-200/60 dark:border-slate-800/50 bg-white/60 dark:bg-slate-900/40 px-4 py-3.5 hover:bg-white dark:hover:bg-slate-900/70 hover:border-slate-300/70 dark:hover:border-slate-700/60 hover:shadow-sm transition-all duration-150"
    >
      {/* File icon */}
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100/80 dark:bg-slate-800/60">
        {MIME_ICONS[doc.mime_type] ?? <File className="h-5 w-5 text-slate-400" />}
      </div>

      {/* Name & meta */}
      <div className="min-w-0 flex-1">
        <p
          className="truncate text-sm font-semibold text-slate-800 dark:text-slate-200"
          title={doc.original_filename}
        >
          {doc.original_filename}
        </p>
        <div className="mt-0.5 flex items-center gap-2 text-[11px] text-slate-400 dark:text-slate-500">
          <span>{formatBytes(doc.file_size)}</span>
          <span className="opacity-40">·</span>
          {doc.chunk_count != null && (
            <>
              <span>{doc.chunk_count} chunks</span>
              <span className="opacity-40">·</span>
            </>
          )}
          <span>{formatDate(doc.created_at)}</span>
        </div>
        {doc.status === "failed" && doc.error_message && (
          <p className="mt-1 text-[11px] text-rose-500 dark:text-rose-400 truncate" title={doc.error_message}>
            {doc.error_message}
          </p>
        )}
      </div>

      {/* Status badge */}
      <div
        className={`flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-bold ${status.color}`}
      >
        {status.icon}
        {status.label}
      </div>

      {/* Delete button */}
      <button
        id={`delete-doc-${doc.id}`}
        onClick={handleDelete}
        disabled={deleting}
        aria-label={`Delete ${doc.original_filename}`}
        className="ml-1 shrink-0 flex h-8 w-8 items-center justify-center rounded-lg border border-transparent text-slate-400 opacity-0 group-hover:opacity-100 hover:border-rose-200 dark:hover:border-rose-800/40 hover:bg-rose-50 dark:hover:bg-rose-950/20 hover:text-rose-500 transition-all duration-150 cursor-pointer disabled:cursor-not-allowed"
      >
        {deleting ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <Trash2 className="h-3.5 w-3.5" />
        )}
      </button>
    </div>
  );
}
