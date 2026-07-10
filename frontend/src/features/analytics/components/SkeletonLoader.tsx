"use client";

import React from "react";
import { cn } from "@/lib/utils";

// -------------------------------------------------------------------------
// Stat card skeleton
// -------------------------------------------------------------------------

export function StatCardSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-200/50 dark:border-slate-800/40 bg-white dark:bg-slate-900/20 p-6 animate-pulse",
        className
      )}
    >
      <div className="flex justify-between items-center mb-4">
        <div className="h-3 w-20 rounded bg-slate-200 dark:bg-slate-800" />
        <div className="h-8 w-8 rounded-lg bg-slate-200 dark:bg-slate-800" />
      </div>
      <div className="h-8 w-24 rounded bg-slate-200 dark:bg-slate-800 mb-2" />
      <div className="h-3 w-16 rounded bg-slate-200 dark:bg-slate-800" />
    </div>
  );
}

// -------------------------------------------------------------------------
// Chart area skeleton
// -------------------------------------------------------------------------

export function ChartSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-200/50 dark:border-slate-800/40 bg-white dark:bg-slate-900/20 p-6 animate-pulse",
        className
      )}
    >
      <div className="h-4 w-40 rounded bg-slate-200 dark:bg-slate-800 mb-2" />
      <div className="h-3 w-24 rounded bg-slate-200 dark:bg-slate-800 mb-5" />
      <div className="h-44 w-full rounded-xl bg-slate-100 dark:bg-slate-800/50" />
    </div>
  );
}

// -------------------------------------------------------------------------
// Score ring skeleton
// -------------------------------------------------------------------------

export function ScoreRingSkeleton({ size = 120 }: { size?: number }) {
  return (
    <div className="flex flex-col items-center gap-2 animate-pulse">
      <div
        className="rounded-full bg-slate-200 dark:bg-slate-800"
        style={{ width: size, height: size }}
      />
      <div className="h-3 w-20 rounded bg-slate-200 dark:bg-slate-800" />
      <div className="h-2.5 w-14 rounded bg-slate-200 dark:bg-slate-800" />
    </div>
  );
}

// -------------------------------------------------------------------------
// Insight card skeleton
// -------------------------------------------------------------------------

export function InsightCardSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-200/40 dark:border-slate-800/30 bg-white dark:bg-slate-900/20 p-4 animate-pulse",
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div className="h-8 w-8 rounded-lg bg-slate-200 dark:bg-slate-800 shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="h-3 w-28 rounded bg-slate-200 dark:bg-slate-800" />
          <div className="h-2.5 w-full rounded bg-slate-200 dark:bg-slate-800" />
          <div className="h-2.5 w-3/4 rounded bg-slate-200 dark:bg-slate-800" />
        </div>
      </div>
    </div>
  );
}

// -------------------------------------------------------------------------
// Habit row skeleton
// -------------------------------------------------------------------------

export function HabitRowSkeleton() {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-slate-200/40 dark:border-slate-800/40 bg-white/50 dark:bg-slate-900/20 p-3 animate-pulse">
      <div className="h-3 w-28 rounded bg-slate-200 dark:bg-slate-800" />
      <div className="flex gap-1.5 flex-1">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="h-5 w-5 rounded-md bg-slate-200 dark:bg-slate-800" />
        ))}
      </div>
      <div className="flex gap-2 shrink-0">
        <div className="h-4 w-10 rounded bg-slate-200 dark:bg-slate-800" />
        <div className="h-4 w-10 rounded bg-slate-200 dark:bg-slate-800" />
      </div>
    </div>
  );
}

// -------------------------------------------------------------------------
// Goal row skeleton
// -------------------------------------------------------------------------

export function GoalRowSkeleton() {
  return (
    <div className="space-y-2 animate-pulse">
      <div className="flex justify-between">
        <div className="h-3 w-36 rounded bg-slate-200 dark:bg-slate-800" />
        <div className="h-3 w-8 rounded bg-slate-200 dark:bg-slate-800" />
      </div>
      <div className="h-2 w-full rounded-full bg-slate-200 dark:bg-slate-800" />
    </div>
  );
}
