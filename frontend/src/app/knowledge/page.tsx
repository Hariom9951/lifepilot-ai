"use client";

/**
 * /knowledge — AI Memory & Personal Knowledge page.
 * Authenticated users can upload documents (PDF, DOCX, TXT, MD),
 * view their processing status, re-index content, search notes,
 * and view matched similarity context results.
 */

import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  BookOpen,
  Brain,
  CheckCircle2,
  FileText,
  RotateCw,
  Search,
  Sparkles,
} from "lucide-react";

import { useToast } from "@/components/ui/toast";
import { apiClient } from "@/config/axios";
import DocumentList from "@/features/knowledge/components/DocumentList";
import DropZone from "@/features/knowledge/components/DropZone";
import type { Document, DocumentListResponse } from "@/types/knowledge";

interface RAGSearchMatch {
  content: string;
  score: number;
  document: string;
  metadata: {
    category?: string;
    importance_score?: number;
    chunk_index?: number;
    timestamp?: string;
    document_id?: string;
    memory_id?: string;
  };
}

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [pollTick, setPollTick] = useState(0);

  // Search Workspace states
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<RAGSearchMatch[] | null>(null);

  // Re-indexing state
  const [reindexing, setReindexing] = useState(false);
  const { toast } = useToast();

  // Fetch on mount and whenever pollTick increments
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await apiClient.get<{ data: DocumentListResponse }>("/knowledge/documents");
        if (!cancelled) setDocuments(res.data.data.documents);
      } catch {
        if (!cancelled) toast("Could not load documents.", "error");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pollTick]);

  // Auto-poll every 5 s while any document is still processing
  useEffect(() => {
    const hasProcessing = documents.some(
      (d) => d.status === "uploaded" || d.status === "processing"
    );
    if (!hasProcessing) return;
    const interval = setInterval(() => setPollTick((t) => t + 1), 5000);
    return () => clearInterval(interval);
  }, [documents]);

  const handleUploadSuccess = (newDoc: Document) => {
    setDocuments((prev) => [newDoc, ...prev]);
    // Automatically trigger incremental indexing
    void triggerIncrementalIndex();
  };

  const handleDeleted = (id: string) => {
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  };

  const triggerIncrementalIndex = async () => {
    try {
      await apiClient.post("/rag/index", { notes: true, journals: true });
      setPollTick((t) => t + 1);
    } catch {
      // Ignored: Background incremental indexing
    }
  };

  const handleReindex = async () => {
    setReindexing(true);
    try {
      const res = await apiClient.post<{ indexed_count: number; message: string }>(
        "/rag/index?reindex=true"
      );
      toast(`Index rebuilt successfully! Processed ${res.data.indexed_count} chunks.`, "success");
      setPollTick((t) => t + 1);
    } catch {
      toast("Re-indexing failed.", "error");
    } finally {
      setReindexing(false);
    }
  };

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    try {
      const res = await apiClient.post<{ matches: RAGSearchMatch[] }>("/rag/search", {
        query: searchQuery,
        limit: 5,
        score_threshold: 0.2,
      });
      setSearchResults(res.data.matches);
    } catch {
      toast("Search query failed.", "error");
    } finally {
      setSearching(false);
    }
  };

  const runSuggestedSearch = (queryText: string) => {
    setSearchQuery(queryText);
    setSearching(true);
    apiClient
      .post<{ matches: RAGSearchMatch[] }>("/rag/search", {
        query: queryText,
        limit: 5,
        score_threshold: 0.2,
      })
      .then((res) => {
        setSearchResults(res.data.matches);
      })
      .catch(() => {
        toast("Suggested search failed.", "error");
      })
      .finally(() => {
        setSearching(false);
      });
  };

  const highlightTerm = (text: string, term: string) => {
    if (!term.trim()) return <span>{text}</span>;
    const words = term.split(/\s+/).filter(Boolean);
    const regex = new RegExp(`(${words.join("|")})`, "gi");
    const parts = text.split(regex);
    return (
      <>
        {parts.map((part, i) =>
          regex.test(part) ? (
            <mark
              key={i}
              className="bg-yellow-100 dark:bg-yellow-950/60 text-yellow-900 dark:text-yellow-100 px-0.5 rounded font-semibold"
            >
              {part}
            </mark>
          ) : (
            part
          )
        )}
      </>
    );
  };

  const readyCount = documents.filter((d) => d.status === "ready").length;

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 dark:from-slate-950 dark:via-slate-950 dark:to-indigo-950/20 transition-colors duration-300">
      <div className="container mx-auto max-w-3xl px-4 py-12 space-y-10">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
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
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  {readyCount} ready for AI search
                </div>
              )}
            </div>
          </div>

          <button
            onClick={handleReindex}
            disabled={reindexing}
            className="flex items-center justify-center gap-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/60 active:scale-98 text-slate-700 dark:text-slate-300 font-semibold px-4 py-2.5 text-sm shadow-sm transition-all duration-200 disabled:opacity-50"
          >
            <RotateCw className={`h-4 w-4 text-slate-500 ${reindexing ? "animate-spin" : ""}`} />
            {reindexing ? "Re-indexing..." : "Re-index All"}
          </button>
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

        {/* Search Workspace */}
        <section aria-labelledby="search-heading" className="space-y-4">
          <h2
            id="search-heading"
            className="text-xs font-bold uppercase tracking-widest text-slate-400 dark:text-slate-600"
          >
            AI Search Workspace
          </h2>

          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search notes, journals, project documentations..."
                className="w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 pl-10 pr-4 py-3 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all shadow-sm"
              />
            </div>
            <button
              type="submit"
              disabled={searching || !searchQuery.trim()}
              className="rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 active:scale-98 text-white font-semibold px-5 py-3 text-sm shadow-md shadow-indigo-500/20 hover:shadow-lg hover:shadow-indigo-500/30 transition-all duration-200 disabled:opacity-50"
            >
              {searching ? "Searching..." : "Search"}
            </button>
          </form>

          {/* Suggested Prompts */}
          <div className="flex flex-wrap gap-2 items-center">
            <span className="text-xs text-slate-400 mr-1 select-none">Quick Prompts:</span>
            <button
              onClick={() => runSuggestedSearch("Search my notes")}
              className="text-xs px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-all"
            >
              Search my notes
            </button>
            <button
              onClick={() => runSuggestedSearch("Search my journal")}
              className="text-xs px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-all"
            >
              Search my journal
            </button>
            <button
              onClick={() => runSuggestedSearch("Find project documentation")}
              className="text-xs px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-all"
            >
              Find project documentation
            </button>
            <button
              onClick={() => runSuggestedSearch("Find AI ideas")}
              className="text-xs px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-all"
            >
              Find AI ideas
            </button>
          </div>

          {/* Results display */}
          {searchResults !== null && (
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-bold text-slate-500 dark:text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
                Retrieved Context Results
              </h3>

              {searchResults.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-8 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/10 text-slate-400 space-y-2">
                  <AlertCircle className="h-6 w-6 text-slate-300" />
                  <p className="text-sm font-medium">No matches found above threshold.</p>
                  <p className="text-xs text-slate-400 font-medium">
                    Try re-indexing or searching with simpler terms.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {searchResults.map((match, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-slate-900/60 shadow-sm space-y-2.5 transition-all hover:border-slate-300 dark:hover:border-slate-700 hover:shadow-md"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400">
                            <FileText className="h-4 w-4" />
                          </div>
                          <span className="text-xs font-bold text-slate-700 dark:text-slate-300 max-w-[200px] truncate">
                            {match.document}
                          </span>
                          {match.metadata.category && (
                            <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-[10px] font-bold text-slate-500 dark:text-slate-400">
                              {match.metadata.category}
                            </span>
                          )}
                        </div>
                        <span className="rounded-xl bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-100 dark:border-indigo-900/40 px-2.5 py-1 text-xs font-bold text-indigo-600 dark:text-indigo-400">
                          {Math.round(match.score * 100)}% Match
                        </span>
                      </div>

                      <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300 font-normal bg-slate-50/50 dark:bg-slate-950/20 p-3 rounded-xl border border-slate-100 dark:border-slate-900/30 whitespace-pre-wrap">
                        {highlightTerm(match.content, searchQuery)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>

        {/* Document list */}
        <section aria-labelledby="docs-heading" className="space-y-3">
          <h2
            id="docs-heading"
            className="text-xs font-bold uppercase tracking-widest text-slate-400 dark:text-slate-600"
          >
            Your Documents
          </h2>
          <DocumentList documents={documents} loading={loading} onDeleted={handleDeleted} />
        </section>
      </div>
    </main>
  );
}
