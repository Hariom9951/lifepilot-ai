"use client";

import React from "react";
import { BookOpen, Loader2 } from "lucide-react";
import DocumentCard from "./DocumentCard";
import type { Document } from "@/types/knowledge";

interface DocumentListProps {
  documents: Document[];
  loading: boolean;
  onDeleted: (id: string) => void;
}

/** Skeleton row shown during initial load */
function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-slate-200/60 dark:border-slate-800/50 bg-white/60 dark:bg-slate-900/30 px-4 py-3.5 animate-pulse">
      <div className="h-10 w-10 rounded-lg bg-slate-200 dark:bg-slate-800" />
      <div className="flex-1 space-y-2">
        <div className="h-3 w-48 rounded bg-slate-200 dark:bg-slate-800" />
        <div className="h-2.5 w-32 rounded bg-slate-100 dark:bg-slate-800/60" />
      </div>
      <div className="h-6 w-20 rounded-full bg-slate-100 dark:bg-slate-800/60" />
    </div>
  );
}

export default function DocumentList({ documents, loading, onDeleted }: DocumentListProps) {
  if (loading) {
    return (
      <div className="space-y-2.5" aria-label="Loading documents">
        {Array.from({ length: 3 }).map((_, i) => (
          <SkeletonRow key={i} />
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div
        id="knowledge-empty-state"
        className="flex flex-col items-center gap-4 py-16 text-center"
      >
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50 dark:bg-indigo-950/30">
          <BookOpen className="h-8 w-8 text-indigo-300 dark:text-indigo-600" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">
            No documents yet
          </p>
          <p className="mt-1 text-xs text-slate-400 dark:text-slate-600">
            Upload a PDF, DOCX, TXT, or Markdown file above to get started.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2.5" role="list" aria-label="Knowledge documents">
      <div className="flex items-center justify-between px-1 mb-1">
        <p className="text-xs font-semibold text-slate-400 dark:text-slate-600 uppercase tracking-wide">
          {documents.length} {documents.length === 1 ? "document" : "documents"}
        </p>
        {documents.some((d) => d.status === "processing") && (
          <span className="flex items-center gap-1.5 text-[11px] text-amber-500 dark:text-amber-400 font-medium">
            <Loader2 className="h-3 w-3 animate-spin" />
            Processing…
          </span>
        )}
      </div>
      {documents.map((doc) => (
        <DocumentCard key={doc.id} document={doc} onDeleted={onDeleted} />
      ))}
    </div>
  );
}
