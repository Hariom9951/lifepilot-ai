"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import { useTheme } from "next-themes";
import { Activity, Home, Laptop, Moon, Settings, Sun } from "lucide-react";

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const { setTheme } = useTheme();

  // Listen to keyboard shortcut
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const runCommand = (command: () => void) => {
    command();
    setOpen(false);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm cursor-pointer"
        onClick={() => setOpen(false)}
      />

      {/* Dialog box */}
      <div className="w-full max-w-md rounded-2xl border border-slate-200/60 bg-white dark:border-slate-800/40 dark:bg-slate-900 p-2 shadow-2xl z-10 overflow-hidden relative">
        <Command label="Command Palette" className="flex flex-col h-[320px] overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-100 dark:border-slate-900 px-3 py-2.5">
            <Command.Input
              autoFocus
              placeholder="Type a command or search..."
              className="w-full text-xs text-slate-850 dark:text-slate-100 bg-transparent outline-none placeholder-slate-400"
            />
            <span className="text-[10px] font-bold font-mono tracking-wider px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-950 text-slate-400 dark:text-slate-500 uppercase">
              esc
            </span>
          </div>

          <Command.List className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-thin">
            <Command.Empty className="text-xs text-slate-400 dark:text-slate-555 py-6 text-center font-sans">
              No results found.
            </Command.Empty>

            <Command.Group
              heading="Navigation"
              className="text-[10px] font-bold font-mono uppercase tracking-widest text-slate-400 dark:text-slate-500 px-3 pt-2 pb-1.5"
            >
              <Command.Item
                onSelect={() => runCommand(() => router.push("/"))}
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors cursor-pointer select-none focus:outline-none aria-selected:bg-slate-100 dark:aria-selected:bg-slate-950/60"
              >
                <Home className="h-4.5 w-4.5" />
                <span>Home Page</span>
              </Command.Item>

              <Command.Item
                onSelect={() => runCommand(() => router.push("/status"))}
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors cursor-pointer select-none focus:outline-none aria-selected:bg-slate-100 dark:aria-selected:bg-slate-950/60"
              >
                <Activity className="h-4.5 w-4.5" />
                <span>System Status</span>
              </Command.Item>

              <Command.Item
                onSelect={() => runCommand(() => router.push("/settings"))}
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors cursor-pointer select-none focus:outline-none aria-selected:bg-slate-100 dark:aria-selected:bg-slate-950/60"
              >
                <Settings className="h-4.5 w-4.5" />
                <span>Settings Console</span>
              </Command.Item>
            </Command.Group>

            <Command.Group
              heading="Themes"
              className="text-[10px] font-bold font-mono uppercase tracking-widest text-slate-400 dark:text-slate-500 px-3 pt-4 pb-1.5"
            >
              <Command.Item
                onSelect={() => runCommand(() => setTheme("light"))}
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors cursor-pointer select-none focus:outline-none aria-selected:bg-slate-100 dark:aria-selected:bg-slate-950/60"
              >
                <Sun className="h-4.5 w-4.5 text-yellow-500" />
                <span>Light Theme</span>
              </Command.Item>

              <Command.Item
                onSelect={() => runCommand(() => setTheme("dark"))}
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors cursor-pointer select-none focus:outline-none aria-selected:bg-slate-100 dark:aria-selected:bg-slate-950/60"
              >
                <Moon className="h-4.5 w-4.5 text-indigo-400" />
                <span>Dark Theme</span>
              </Command.Item>

              <Command.Item
                onSelect={() => runCommand(() => setTheme("system"))}
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors cursor-pointer select-none focus:outline-none aria-selected:bg-slate-100 dark:aria-selected:bg-slate-950/60"
              >
                <Laptop className="h-4.5 w-4.5" />
                <span>System Theme</span>
              </Command.Item>
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
