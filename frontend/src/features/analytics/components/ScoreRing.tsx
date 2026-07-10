"use client";

import React, { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface ScoreRingProps {
  score: number; // 0–100
  size?: number;
  strokeWidth?: number;
  label: string;
  sublabel?: string;
  colorClass?: string; // Tailwind stroke colour class
  className?: string;
  animate?: boolean;
}

/**
 * Animated SVG progress ring for displaying numeric scores (0–100).
 * Uses a CSS animation on stroke-dashoffset for a smooth fill-in effect.
 */
export default function ScoreRing({
  score,
  size = 120,
  strokeWidth = 10,
  label,
  sublabel,
  colorClass = "stroke-indigo-500",
  className,
  animate = true,
}: ScoreRingProps) {
  const [displayed, setDisplayed] = useState(animate ? 0 : score);
  const clampedScore = Math.min(Math.max(score, 0), 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (displayed / 100) * circumference;

  // Count-up animation
  useEffect(() => {
    if (!animate) return;
    let start: number | null = null;
    const duration = 1200;

    const step = (timestamp: number) => {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setDisplayed(Math.round(eased * clampedScore));
      if (progress < 1) requestAnimationFrame(step);
    };
    const id = requestAnimationFrame(step);
    return () => cancelAnimationFrame(id);
  }, [clampedScore, animate]);

  return (
    <div className={cn("flex flex-col items-center justify-center gap-2", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
          {/* Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            className="stroke-slate-200/50 dark:stroke-slate-800/60"
            strokeWidth={strokeWidth}
          />
          {/* Progress */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            className={colorClass}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 0.05s ease-out" }}
          />
        </svg>
        {/* Centre text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-black text-slate-900 dark:text-white leading-none">
            {displayed}
          </span>
          <span className="text-[9px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wide mt-0.5">
            / 100
          </span>
        </div>
      </div>
      <div className="text-center">
        <p className="text-xs font-bold text-slate-700 dark:text-slate-300">{label}</p>
        {sublabel && (
          <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">{sublabel}</p>
        )}
      </div>
    </div>
  );
}
