"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { AlertOctagon, RefreshCw, Home } from "lucide-react";
import { PageWrapper } from "@/layouts/PageWrapper";
import { SectionContainer } from "@/layouts/SectionContainer";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <PageWrapper className="min-h-screen flex items-center justify-center bg-white dark:bg-slate-950">
      <SectionContainer className="text-center flex flex-col items-center max-w-md">
        {/* Animated Error Emblem */}
        <div className="h-16 w-16 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-500 mb-6 shadow-md shadow-rose-500/5">
          <AlertOctagon className="h-8 w-8 animate-pulse" />
        </div>

        <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight mb-3">
          500 - System Error
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-8 leading-relaxed max-w-xs font-sans">
          An unexpected error has disrupted your flight system. Your local copilot is attempting
          recovery diagnostics.
        </p>

        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={() => reset()}
            className="inline-flex items-center gap-2.5 px-5 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/35 transition-all hover:-translate-y-0.5 active:scale-[0.98] cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          >
            <RefreshCw className="h-4 w-4" />
            Retry System
          </button>
          <Link
            href="/"
            className="inline-flex items-center gap-2.5 px-5 py-2.5 rounded-xl text-xs font-bold bg-slate-100 border border-slate-200/50 hover:bg-slate-200 text-slate-700 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-350 dark:hover:bg-slate-850 dark:hover:text-white transition-all hover:-translate-y-0.5 active:scale-[0.98] cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500/10"
          >
            <Home className="h-4 w-4" />
            Go Home
          </Link>
        </div>
      </SectionContainer>
    </PageWrapper>
  );
}
