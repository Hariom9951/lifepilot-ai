"use client";

/**
 * /knowledge — AI Memory & Personal Knowledge page.
 * Authenticated users can upload documents (PDF, DOCX, TXT, MD),
 * view their processing status, and delete them.
 *
 * Phase 5 will add semantic search via FAISS RAG query.
 */

import React, { useCallback, useEffect, useState } from "react";
import { Brain, Search, BookOpen, Sparkles } from "lucide-react";
import { apiClient } from "@/config/axios";
import { useToast } from "@/components/ui/toast";
import DropZone from "@/features/knowledge/components/DropZone";
import DocumentList from "@/features/knowledge/components/DocumentList";
import type { Document, DocumentListResponse } from "@/types/knowledge";

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  // Poll processing docs every 5 s so status updates live
  const fetchDocuments = useCallback(async () => {
    try {
      const res = await apiClient.get<{ data: DocumentListResponse }>("/knowledge/documents");
      setDocuments(res.data.data.documents);
    } catch {
      toast("Could not load documents.", "error");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Auto-poll while any document is processing
  useEffect(() => {
    const hasProcessing = documents.some(
      (d) => d.status === "uploaded" || d.status === "processing"
    );
    if (!hasProcessing) return;

    const interval = setInterval(fetchDocuments, 5000);
    return () => clearInterval(interval);
  }, [documents, fetchDocuments]);

  const handleUploadSuccess = (newDoc: Document) => {
    setDocuments((prev) => [newDoc, ...prev]);
  };

  const handleDeleted = (id: string) => {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  };

  const readyCount = documents.filter((d) => d.status === "ready").length;

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 dark:from-slate-950 dark:via-slate-950 dark:to-indigo-950/20 transition-colors duration-300">
      <div className="container mx-auto max-w-3xl px-4 py-12 space-y-10">
        {/* Header */}
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/25">
              <Brain className="h-5.5 w-5.5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
                Knowledge Engine
              </h1>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Personal AI memory powered by RAG
              </p>
            </div>
          </div>

          {/* Stats row */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <div className="flex items-center gap-1.5 rounded-lg border border-slate-200/60 dark:border-slate-800/50 bg-white/60 dark:bg-slate-900/40 px-3 py-1.5 text-xs font-semibold text-slate-600 dark:text-slate-400">
              <BookOpen className="h-3.5 w-3.5 text-indigo-400" />
              {documents.length} document{documents.length !== 1 ? "s" : ""}
            </div>
            {readyCount > 0 && (
              <div className="flex items-center gap-1.5 rounded-lg border border-emerald-200/60 dark:border-emerald-800/40 bg-emerald-50/60 dark:bg-emerald-950/20 px-3 py-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                <Sparkles className="h-3.5 w-3.5" />
                {readyCount} ready for AI search
              </div>
            )}
          </div>
        </div>

        {/* Upload section */}
        <section aria-labelledby="upload-heading" className="space-y-3">
          <h2
            id="upload-heading"
            className="text-xs font-bold uppercase tracking-widest text-slate-400 dark:text-slate-600"
          >
            Upload Document
          </h2>
          <DropZone onUploadSuccess={handleUploadSuccess} />
        </section>

        {/* Placeholder Search bar — Phase 5 */}
        <section aria-labelledby="search-heading" className="space-y-3">
          <h2
            id="search-heading"
            className="text-xs font-bold uppercase tracking-widest text-slate-400 dark:text-slate-600"
          >
            AI Search
            <span className="ml-2 rounded-md border border-indigo-200 dark:border-indigo-800/60 bg-indigo-50 dark:bg-indigo-950/30 px-1.5 py-0.5 text-[10px] font-bold text-indigo-500 dark:text-indigo-400 normal-case tracking-normal align-middle">
              Coming in Phase 5
            </span>
          </h2>
          <div
            id="knowledge-search-placeholder"
            className="flex items-center gap-3 rounded-xl border border-slate-200/60 dark:border-slate-700/40 bg-white/60 dark:bg-slate-900/30 px-4 py-3.5 cursor-not-allowed opacity-60"
          >
            <Search className="h-4 w-4 text-slate-400 shrink-0" />
            <span className="text-sm text-slate-400 dark:text-slate-600 select-none">
              Ask a question about your documents…
            </span>
          </div>
        </section>

        {/* Document list */}
        <section aria-labelledby="docs-heading" className="space-y-3">
          <h2
            id="docs-heading"
            className="text-xs font-bold uppercase tracking-widest text-slate-400 dark:text-slate-600"
          >
            Your Documents
          </h2>
          <DocumentList
            documents={documents}
            loading={loading}
            onDeleted={handleDeleted}
          />
        </section>
      </div>
    </main>
  );
}
