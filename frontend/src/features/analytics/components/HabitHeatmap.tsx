"use client";

import React from "react";
import { cn } from "@/lib/utils";
import type { HabitHeatmapDay } from "@/types/analytics";

interface HabitHeatmapProps {
  name: string;
  color: string;
  heatmap: HabitHeatmapDay[];
  currentStreak: number;
  completionRate: number;
}

/**
 * 7-cell micro-heatmap for a single habit showing last 7 days of completions.
 */
export default function HabitHeatmap({
  name,
  color,
  heatmap,
  currentStreak,
  completionRate,
}: HabitHeatmapProps) {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-slate-200/40 dark:border-slate-800/40 bg-white/50 dark:bg-slate-900/20 p-3">
      {/* Colour dot + name */}
      <div className="flex items-center gap-2 min-w-[120px]">
        <span className="h-3 w-3 rounded-full shrink-0" style={{ backgroundColor: color }} />
        <span className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 truncate">
          {name}
        </span>
      </div>

      {/* Heatmap cells */}
      <div className="flex items-center gap-1.5 flex-1">
        {heatmap.map((day) => (
          <div key={day.date} className="flex flex-col items-center gap-0.5">
            <div
              className={cn(
                "h-5 w-5 rounded-md transition-opacity",
                day.completed ? "opacity-100" : "opacity-20 bg-slate-300 dark:bg-slate-700"
              )}
              style={day.completed ? { backgroundColor: color } : undefined}
              title={`${day.date}: ${day.completed ? "✓" : "✗"}`}
            />
            <span className="text-[8px] text-slate-400 dark:text-slate-600">
              {day.day_label[0]}
            </span>
          </div>
        ))}
      </div>

      {/* Streak + rate */}
      <div className="flex items-center gap-3 shrink-0">
        <div className="text-center">
          <p className="text-xs font-black text-slate-900 dark:text-white">🔥{currentStreak}d</p>
          <p className="text-[9px] text-slate-400">streak</p>
        </div>
        <div className="text-center">
          <p className="text-xs font-black text-slate-900 dark:text-white">
            {Math.round(completionRate * 100)}%
          </p>
          <p className="text-[9px] text-slate-400">7-day</p>
        </div>
      </div>
    </div>
  );
}
