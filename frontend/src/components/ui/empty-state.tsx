"use client";

import React from "react";
import { Info } from "lucide-react";
import { cn } from "@/lib/utils";

export interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon: IconComp = Info,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 text-center rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 bg-slate-50/30 dark:bg-slate-900/5 max-w-md mx-auto",
        className
      )}
    >
      <div className="p-3.5 rounded-2xl bg-slate-100 dark:bg-slate-900 text-slate-400 mb-4 border border-slate-200/50 dark:border-slate-800/40">
        <IconComp className="h-6 w-6" />
      </div>
      <h4 className="text-sm font-bold text-slate-900 dark:text-white mb-1.5">{title}</h4>
      <p className="text-xs text-slate-500 dark:text-slate-500 max-w-xs mb-5 leading-normal">
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  );
}
