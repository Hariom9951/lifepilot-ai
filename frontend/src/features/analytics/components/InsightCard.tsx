"use client";

import React from "react";
import { cn } from "@/lib/utils";
import type { AIInsight } from "@/types/analytics";

interface InsightCardProps {
  insight: AIInsight;
  index?: number;
}

const SEVERITY_STYLES = {
  positive: {
    border: "border-emerald-500/25 dark:border-emerald-500/20",
    bg: "bg-emerald-50/60 dark:bg-emerald-950/20",
    dot: "bg-emerald-500",
    title: "text-emerald-700 dark:text-emerald-400",
    glow: "shadow-emerald-500/10",
  },
  neutral: {
    border: "border-indigo-500/20 dark:border-indigo-500/15",
    bg: "bg-indigo-50/40 dark:bg-indigo-950/15",
    dot: "bg-indigo-400",
    title: "text-indigo-700 dark:text-indigo-300",
    glow: "shadow-indigo-500/10",
  },
  warning: {
    border: "border-amber-500/30 dark:border-amber-500/25",
    bg: "bg-amber-50/60 dark:bg-amber-950/20",
    dot: "bg-amber-500",
    title: "text-amber-700 dark:text-amber-400",
    glow: "shadow-amber-500/10",
  },
} as const;

export default function InsightCard({ insight, index = 0 }: InsightCardProps) {
  const styles = SEVERITY_STYLES[insight.severity];

  return (
    <div
      className={cn(
        "group relative rounded-2xl border p-4 transition-all duration-300",
        "hover:shadow-md hover:scale-[1.01] cursor-default",
        styles.border,
        styles.bg,
        styles.glow
      )}
      style={{ animationDelay: `${index * 80}ms` }}
    >
      {/* Severity dot */}
      <span className={cn("absolute top-3.5 right-3.5 h-2 w-2 rounded-full", styles.dot)} />

      <div className="flex items-start gap-3">
        {/* Emoji */}
        <span className="text-2xl shrink-0 leading-none mt-0.5 select-none" role="img" aria-hidden>
          {insight.emoji}
        </span>

        <div className="space-y-1 min-w-0">
          <h4 className={cn("text-xs font-bold leading-snug", styles.title)}>{insight.title}</h4>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
            {insight.message}
          </p>
        </div>
      </div>
    </div>
  );
}
