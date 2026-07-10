"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Brain, Command, Menu, X, Activity, Settings, LogOut, LayoutDashboard } from "lucide-react";
import ThemeToggle from "@/components/ui/ThemeToggle";
import { useAuthStore } from "@/store/authStore";
import { apiClient } from "@/config/axios";
import { useToast } from "@/components/ui/toast";
import Image from "next/image";

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { isAuthenticated, user, logout } = useAuthStore();
  const router = useRouter();
  const { toast } = useToast();

  const handleLogout = async () => {
    try {
      await apiClient.post("/auth/logout");
    } catch {
      // Fail silently
    }
    logout();
    toast("Logged out successfully.", "info");
    router.push("/login");
  };

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
            href={isAuthenticated ? "/dashboard" : "/#preview"}
            className="hover:text-slate-800 dark:hover:text-slate-200 transition-colors flex items-center gap-1.5"
          >
            {isAuthenticated && <LayoutDashboard className="h-3.5 w-3.5 text-indigo-550" />}
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
          {isAuthenticated && (
            <Link
              href="/settings"
              className="hover:text-slate-800 dark:hover:text-slate-200 transition-colors flex items-center gap-1.5"
            >
              <Settings className="h-3.5 w-3.5" />
              Settings
            </Link>
          )}
        </nav>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          {/* Ctrl+K Indicator */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200/60 bg-slate-100/50 text-[10px] font-bold text-slate-400 dark:border-slate-800/40 dark:bg-slate-950/40 select-none">
            <Command className="h-3 w-3" />
            <span>K</span>
          </div>

          <ThemeToggle />

          {/* Authentication Actions */}
          <div className="hidden md:flex items-center gap-2">
            {isAuthenticated && user ? (
              <div className="flex items-center gap-3">
                <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-indigo-550 to-purple-600 flex items-center justify-center text-white text-[10px] font-black uppercase overflow-hidden">
                  {user.avatar_url ? (
                    <Image
                      src={user.avatar_url}
                      alt="Profile"
                      width={28}
                      height={28}
                      unoptimized
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    user.full_name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")
                  )}
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1 px-3 py-1.5 border border-slate-200 hover:border-slate-300 dark:border-slate-800 dark:hover:border-slate-700 bg-white/40 dark:bg-slate-900/40 hover:text-slate-800 dark:hover:text-white rounded-lg text-[10px] font-bold text-slate-500 transition-colors cursor-pointer"
                >
                  <LogOut className="h-3 w-3" />
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-1.5">
                <Link
                  href="/login"
                  className="px-3 py-1.5 text-[10px] font-bold text-slate-550 dark:text-slate-400 hover:text-slate-850 dark:hover:text-slate-200 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-[10px] font-bold shadow-md shadow-indigo-500/10 hover:shadow-indigo-500/20 transition-all"
                >
                  Register
                </Link>
              </div>
            )}
          </div>

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
            href={isAuthenticated ? "/dashboard" : "/#preview"}
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
          {isAuthenticated ? (
            <>
              <Link
                href="/settings"
                onClick={() => setMobileMenuOpen(false)}
                className="block text-xs font-bold text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
              >
                Settings Console
              </Link>
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  handleLogout();
                }}
                className="w-full text-left block text-xs font-bold text-rose-500 hover:text-rose-600 transition-colors cursor-pointer"
              >
                Sign Out
              </button>
            </>
          ) : (
            <div className="flex flex-col gap-2 pt-2 border-t border-slate-100 dark:border-slate-900">
              <Link
                href="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="block text-center text-xs font-bold text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 py-1.5"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                onClick={() => setMobileMenuOpen(false)}
                className="block text-center text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg py-2"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
}
