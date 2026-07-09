"use client";

import React, { createContext, useContext, useState } from "react";
import { cn } from "@/lib/utils";

interface TabsContextProps {
  activeValue: string;
  setActiveValue: (value: string) => void;
}

const TabsContext = createContext<TabsContextProps | null>(null);

export interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  defaultValue: string;
  value?: string;
  onValueChange?: (value: string) => void;
}

export function Tabs({
  defaultValue,
  value,
  onValueChange,
  children,
  className,
  ...props
}: TabsProps) {
  const [localValue, setLocalValue] = useState(defaultValue);
  const activeValue = value !== undefined ? value : localValue;

  const setActiveValue = (newValue: string) => {
    if (value === undefined) {
      setLocalValue(newValue);
    }
    if (onValueChange) {
      onValueChange(newValue);
    }
  };

  return (
    <TabsContext.Provider value={{ activeValue, setActiveValue }}>
      <div className={cn("w-full", className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  );
}

export type TabsListProps = React.HTMLAttributes<HTMLDivElement>;

export function TabsList({ children, className, ...props }: TabsListProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center justify-start rounded-xl p-1 bg-slate-100 dark:bg-slate-900 border border-slate-200/50 dark:border-slate-800/40 gap-1",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
}

export function TabsTrigger({ value, children, className, ...props }: TabsTriggerProps) {
  const context = useContext(TabsContext);
  if (!context) throw new Error("TabsTrigger must be used inside Tabs component");
  const isActive = context.activeValue === value;

  return (
    <button
      type="button"
      onClick={() => context.setActiveValue(value)}
      className={cn(
        "px-4 py-1.5 rounded-lg text-xs font-bold transition-all select-none cursor-pointer focus:outline-none",
        isActive
          ? "bg-white text-indigo-600 shadow-sm dark:bg-slate-950 dark:text-indigo-400"
          : "text-slate-500 hover:text-slate-850 dark:hover:text-slate-350",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
}

export function TabsContent({ value, children, className, ...props }: TabsContentProps) {
  const context = useContext(TabsContext);
  if (!context) throw new Error("TabsContent must be used inside Tabs component");
  const isActive = context.activeValue === value;

  if (!isActive) return null;

  return (
    <div className={cn("pt-4 focus:outline-none", className)} {...props}>
      {children}
    </div>
  );
}
