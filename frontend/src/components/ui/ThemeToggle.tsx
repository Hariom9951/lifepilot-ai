"use client";

import React, { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Laptop, Moon, Sun } from "lucide-react";

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch
  useEffect(() => {
    let active = true;
    requestAnimationFrame(() => {
      if (active) {
        setMounted(true);
      }
    });
    return () => {
      active = false;
    };
  }, []);

  if (!mounted) {
    return (
      <div className="h-8.5 w-8.5 rounded-lg border border-slate-200/25 bg-transparent dark:border-slate-800/40" />
    );
  }

  const cycleTheme = () => {
    if (theme === "light") setTheme("dark");
    else if (theme === "dark") setTheme("system");
    else setTheme("light");
  };

  return (
    <button
      onClick={cycleTheme}
      className="h-8.5 w-8.5 rounded-lg border border-slate-200/20 bg-slate-100/10 hover:border-slate-200/40 hover:bg-slate-150/10 dark:border-slate-800/40 dark:bg-slate-950/20 dark:hover:border-slate-700/50 dark:hover:bg-slate-900/40 flex items-center justify-center text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-all active:scale-95 cursor-pointer focus:outline-none focus:ring-1 focus:ring-indigo-500"
      aria-label={`Toggle theme (current: ${theme})`}
    >
      {theme === "light" && <Sun className="h-4.5 w-4.5" />}
      {theme === "dark" && <Moon className="h-4.5 w-4.5" />}
      {theme === "system" && <Laptop className="h-4.5 w-4.5" />}
    </button>
  );
}
