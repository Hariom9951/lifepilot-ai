"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Brain, Command, Menu, X, Activity, Settings } from "lucide-react";
import ThemeToggle from "@/components/ui/ThemeToggle";

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200/50 bg-white/80 dark:border-slate-800/40 dark:bg-slate-950/80 backdrop-blur-md transition-colors duration-300">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between max-w-5xl">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-md shadow-indigo-500/15 group-hover:scale-105 transition-transform">
            <Brain className="h-5 w-5 text-white" />
          </div>
          <span className="text-sm font-black tracking-tight text-slate-900 dark:text-white">
            LifePilot <span className="text-indigo-500 dark:text-indigo-400">AI</span>
          </span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-6 text-xs font-bold text-slate-500 dark:text-slate-450">
          <Link
            href="/#preview"
            className="hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
          >
            Dashboard
          </Link>
          <Link
            href="/#features"
            className="hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
          >
            Features
          </Link>
          <Link
            href="/#architecture"
            className="hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
          >
            Architecture
          </Link>
          <Link
            href="/status"
            className="hover:text-slate-800 dark:hover:text-slate-200 transition-colors flex items-center gap-1.5"
          >
            <Activity className="h-3.5 w-3.5" />
            Status
          </Link>
          <Link
            href="/settings"
            className="hover:text-slate-800 dark:hover:text-slate-200 transition-colors flex items-center gap-1.5"
          >
            <Settings className="h-3.5 w-3.5" />
            Settings
          </Link>
        </nav>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          {/* Ctrl+K Indicator */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200/60 bg-slate-100/50 text-[10px] font-bold text-slate-400 dark:border-slate-800/40 dark:bg-slate-950/40 select-none">
            <Command className="h-3 w-3" />
            <span>K</span>
          </div>

          <ThemeToggle />

          {/* Mobile Menu Toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden h-8.5 w-8.5 rounded-lg border border-slate-200/25 bg-slate-100/10 hover:border-slate-200/40 flex items-center justify-center text-slate-500 hover:text-slate-900 dark:border-slate-800/40 dark:bg-slate-950/20 dark:text-slate-450 dark:hover:text-slate-100 transition-colors cursor-pointer focus:outline-none"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X className="h-4.5 w-4.5" /> : <Menu className="h-4.5 w-4.5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-200/50 bg-white/95 dark:border-slate-800/40 dark:bg-slate-950/95 backdrop-blur-md py-4 px-4 space-y-3 transition-colors duration-300">
          <Link
            href="/#preview"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-xs font-bold text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
          >
            Dashboard
          </Link>
          <Link
            href="/#features"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-xs font-bold text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
          >
            Features
          </Link>
          <Link
            href="/#architecture"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-xs font-bold text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
          >
            Architecture
          </Link>
          <Link
            href="/status"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-xs font-bold text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
          >
            System Status
          </Link>
          <Link
            href="/settings"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-xs font-bold text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
          >
            Settings Console
          </Link>
        </div>
      )}
    </header>
  );
}
