"use client";

import React, { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { Brain } from "lucide-react";

interface RouteGuardProps {
  children: React.ReactNode;
}

// List of public route prefixes that do not require authentication
const PUBLIC_PATHS = ["/login", "/register", "/forgot-password", "/status"];

export default function RouteGuard({ children }: RouteGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, initializeAuth } = useAuthStore();

  useEffect(() => {
    // Attempt silent sign-in on first mount
    if (!isAuthenticated) {
      initializeAuth();
    }
  }, [isAuthenticated, initializeAuth]);

  useEffect(() => {
    if (!isLoading) {
      const isPublicPath = PUBLIC_PATHS.some((path) => pathname === path || pathname === "/");

      if (!isAuthenticated && !isPublicPath) {
        // Redirect to login if user is unauthenticated on private route
        router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
      }
    }
  }, [isAuthenticated, isLoading, pathname, router]);

  const isPublicPath = PUBLIC_PATHS.some((path) => pathname === path || pathname === "/");

  // Show a premium, custom glassmorphic loading screen during auth status resolution
  if (isLoading && !isPublicPath) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center justify-center font-sans">
        <div className="relative p-8 rounded-3xl border border-slate-200/50 bg-white/40 dark:border-slate-800/40 dark:bg-slate-950/40 backdrop-blur-xl shadow-2xl flex flex-col items-center gap-4">
          <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/20 animate-pulse">
            <Brain className="h-7 w-7 text-white" />
          </div>
          <div className="space-y-1 text-center">
            <h3 className="text-sm font-black tracking-tight text-slate-850 dark:text-white">
              Securing Workspace
            </h3>
            <p className="text-[10px] text-slate-450 dark:text-slate-500 font-mono tracking-wider animate-bounce">
              AUTHENTICATING...
            </p>
          </div>
        </div>
      </div>
    );
  }

  // If unauthenticated and on a private page, render nothing while redirect runs
  if (!isLoading && !isAuthenticated && !isPublicPath) {
    return null;
  }

  return <>{children}</>;
}
