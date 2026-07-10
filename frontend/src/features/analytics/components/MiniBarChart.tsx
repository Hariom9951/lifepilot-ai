"use client";

import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { WeeklyDataPoint } from "@/types/analytics";

interface MiniBarChartProps {
  data: WeeklyDataPoint[];
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-xl border border-slate-200/60 dark:border-slate-700/50 bg-white/95 dark:bg-slate-900/95 shadow-xl px-3 py-2 backdrop-blur-sm">
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1">{label}</p>
        <p className="text-sm font-black text-emerald-500">
          {payload[0].value}
          <span className="text-[10px] font-normal text-slate-400 ml-1">tasks done</span>
        </p>
      </div>
    );
  }
  return null;
};

export default function MiniBarChart({ data }: MiniBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} margin={{ top: 5, right: 5, left: -30, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" vertical={false} />
        <XAxis
          dataKey="day"
          tick={{ fontSize: 10, fill: "#94a3b8" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fontSize: 10, fill: "#94a3b8" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(99,102,241,0.06)" }} />
        <Bar dataKey="tasks_completed" fill="#10b981" radius={[4, 4, 0, 0]} maxBarSize={28} />
      </BarChart>
    </ResponsiveContainer>
  );
}
