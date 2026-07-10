"use client";

import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";

// 1. Reusable Card
export interface CardProps extends Omit<
  React.HTMLAttributes<HTMLDivElement>,
  "onDrag" | "onDragStart" | "onDragEnd" | "onAnimationStart"
> {
  hoverEffect?: boolean;
}

export function Card({ children, className, hoverEffect = false, ...props }: CardProps) {
  const baseClasses = cn(
    "rounded-2xl border border-slate-200/50 bg-white p-5 shadow-sm transition-colors dark:border-slate-800/40 dark:bg-slate-900/20 relative overflow-hidden",
    hoverEffect &&
      "hover:border-slate-350 dark:hover:border-slate-700/60 shadow-md hover:shadow-lg",
    className
  );

  if (hoverEffect) {
    return (
      <motion.div
        className={baseClasses}
        whileHover={{ y: -4, scale: 1.01 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        {...props}
      >
        {children}
      </motion.div>
    );
  }

  return (
    <div className={baseClasses} {...props}>
      {children}
    </div>
  );
}

// 2. Stat Card
export interface StatCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  value: string | number;
  change?: number;
  timeframe?: string;
  icon?: React.ComponentType<{ className?: string }>;
}

export function StatCard({
  title,
  value,
  change,
  timeframe = "from last week",
  icon: IconComp,
  className,
  ...props
}: StatCardProps) {
  const isPositive = change && change >= 0;

  return (
    <Card className={cn("p-6", className)} {...props}>
      <div className="flex justify-between items-center mb-4">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
          {title}
        </span>
        {IconComp && (
          <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <IconComp className="h-4.5 w-4.5" />
          </div>
        )}
      </div>

      <div className="space-y-2">
        <h4 className="text-2xl font-black text-slate-950 dark:text-white tracking-tight">
          {value}
        </h4>
        {change !== undefined && (
          <div className="flex items-center gap-1.5 text-xs">
            <span
              className={cn(
                "inline-flex items-center gap-0.5 font-bold font-mono px-1.5 py-0.5 rounded",
                isPositive ? "bg-emerald-500/15 text-emerald-400" : "bg-red-500/15 text-red-400"
              )}
            >
              {isPositive ? (
                <ArrowUpRight className="h-3 w-3" />
              ) : (
                <ArrowDownRight className="h-3 w-3" />
              )}
              {isPositive ? "+" : ""}
              {change}%
            </span>
            <span className="text-slate-400 dark:text-slate-500">{timeframe}</span>
          </div>
        )}
      </div>
    </Card>
  );
}

// 3. Metric Card (Interactive or chart container)
export function MetricCard({ children, className, ...props }: CardProps) {
  return (
    <Card className={cn("bg-slate-50/50 dark:bg-slate-950/20 p-6 space-y-4", className)} {...props}>
      {children}
    </Card>
  );
}

// 4. Feature Card (Animated card with glows)
export interface FeatureCardProps extends CardProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  badge?: string;
}

export function FeatureCard({
  icon: IconComp,
  title,
  description,
  badge,
  className,
  ...props
}: FeatureCardProps) {
  return (
    <motion.div
      whileHover={{ y: -6, scale: 1.02 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={cn(
        "group relative p-6 rounded-2xl border border-slate-200/50 bg-white dark:border-slate-800/40 dark:bg-slate-900/10 hover:border-slate-350 dark:hover:border-slate-700/60 hover:bg-slate-50/30 dark:hover:bg-slate-900/25 transition-all shadow-md hover:shadow-xl flex flex-col justify-between min-h-[220px] overflow-hidden",
        className
      )}
      {...props}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/0 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
      <div>
        <div className="flex justify-between items-center mb-5">
          <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-950 border border-slate-200/60 dark:border-slate-850 group-hover:border-indigo-500/30 group-hover:bg-indigo-500/5 transition-all">
            <IconComp className="h-5.5 w-5.5 text-slate-500 dark:text-slate-400 group-hover:text-indigo-400 transition-colors" />
          </div>
          {badge && (
            <span className="text-[9px] font-bold font-mono tracking-wider uppercase px-2.5 py-0.5 rounded-full border border-slate-200 dark:border-slate-800 bg-slate-100/50 dark:bg-slate-950 text-slate-500 dark:text-slate-400">
              {badge}
            </span>
          )}
        </div>
        <h3 className="text-base font-bold text-slate-900 dark:text-white mb-2 group-hover:text-indigo-500 dark:group-hover:text-indigo-300 transition-colors">
          {title}
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-500 group-hover:text-slate-700 dark:group-hover:text-slate-400 transition-colors leading-relaxed">
          {description}
        </p>
      </div>
    </motion.div>
  );
}

// 5. Section Card (Large details wrapper)
export function SectionCard({ children, className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-3xl border border-slate-200/50 bg-white/40 p-6 md:p-8 shadow-md dark:border-slate-800/40 dark:bg-slate-900/20 backdrop-blur-sm relative",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
