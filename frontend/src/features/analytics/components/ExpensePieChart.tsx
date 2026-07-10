"use client";

import React from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { CategoryAmount } from "@/types/analytics";

interface ExpensePieChartProps {
  data: CategoryAmount[];
}

const COLOURS = [
  "#6366f1",
  "#8b5cf6",
  "#ec4899",
  "#f59e0b",
  "#10b981",
  "#3b82f6",
  "#ef4444",
  "#14b8a6",
];

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; payload: CategoryAmount }>;
}) => {
  if (active && payload && payload.length) {
    const d = payload[0].payload;
    return (
      <div className="rounded-xl border border-slate-200/60 dark:border-slate-700/50 bg-white/95 dark:bg-slate-900/95 shadow-xl px-3 py-2 backdrop-blur-sm">
        <p className="text-xs font-bold text-slate-700 dark:text-slate-200">{d.category}</p>
        <p className="text-sm font-black text-indigo-500 mt-0.5">
          ${d.amount.toFixed(2)}
          <span className="text-[10px] font-normal text-slate-400 ml-1">
            ({d.percentage.toFixed(1)}%)
          </span>
        </p>
      </div>
    );
  }
  return null;
};

const renderLegend = (props: { payload?: Array<{ value: string; color: string }> }) => {
  if (!props.payload) return null;
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1.5 justify-center mt-2">
      {props.payload.map((entry, i) => (
        <li key={i} className="flex items-center gap-1.5">
          <span
            className="inline-block h-2 w-2 rounded-full shrink-0"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-[10px] text-slate-500 dark:text-slate-400">{entry.value}</span>
        </li>
      ))}
    </ul>
  );
};

export default function ExpensePieChart({ data }: ExpensePieChartProps) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-slate-400 dark:text-slate-600">
        No expense data this month
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="45%"
          innerRadius={55}
          outerRadius={85}
          paddingAngle={3}
          dataKey="amount"
          nameKey="category"
          stroke="none"
        >
          {data.map((_, index) => (
            <Cell key={index} fill={COLOURS[index % COLOURS.length]} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend content={renderLegend} />
      </PieChart>
    </ResponsiveContainer>
  );
}
