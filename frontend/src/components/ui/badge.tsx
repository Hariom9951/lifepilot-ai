"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "success" | "danger" | "warning" | "info" | "outline";
  size?: "sm" | "md" | "lg";
}

export function Badge({
  children,
  variant = "default",
  size = "md",
  className,
  ...props
}: BadgeProps) {
  const variantStyles = {
    default: "bg-indigo-500/10 border-indigo-500/20 text-indigo-500 dark:text-indigo-400",
    secondary: "bg-purple-500/10 border-purple-500/20 text-purple-500 dark:text-purple-400",
    success: "bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400",
    danger: "bg-rose-500/10 border-rose-500/20 text-rose-600 dark:text-rose-400",
    warning: "bg-amber-500/10 border-amber-500/20 text-amber-600 dark:text-amber-400",
    info: "bg-sky-500/10 border-sky-500/20 text-sky-600 dark:text-sky-400",
    outline: "border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-[9px] font-bold font-mono tracking-wider uppercase",
    md: "px-2.5 py-0.5 text-[10px] font-bold font-mono tracking-wide",
    lg: "px-3 py-1 text-xs font-semibold",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border transition-colors select-none",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
