"use client";

import React from "react";
import { useAuthStore } from "@/store/authStore";
import { PageWrapper } from "@/layouts/PageWrapper";
import { SectionContainer } from "@/layouts/SectionContainer";
import Navbar from "@/layouts/Navbar";
import LandingFooter from "@/features/landing/components/LandingFooter";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, Shield, User as UserIcon, Calendar, Mail, Compass, Settings } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { user } = useAuthStore();

  if (!user) return null;

  return (
    <PageWrapper className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 font-sans">
      <Navbar />

      <SectionContainer className="max-w-4xl py-12 md:py-16">
        {/* Header Console */}
        <div className="border-b border-slate-200/60 dark:border-slate-900 pb-8 mb-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <span className="text-[9px] font-bold font-mono tracking-widest uppercase text-indigo-500 bg-indigo-500/10 dark:bg-indigo-500/15 px-2 py-0.5 rounded-md">
              WORKSPACE ACTIVE
            </span>
            <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white mt-2">
              Cockpit Console
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Welcome back, pilot. Overviewing active container metrics, database indexes, and user nodes.
            </p>
          </div>
          <Link
            href="/settings"
            className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-500/10 hover:shadow-indigo-500/20 cursor-pointer self-start md:self-center transition-all"
          >
            <Settings className="h-4 w-4" />
            Manage Settings
          </Link>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* User Profile Card */}
          <Card className="p-6 md:col-span-2 space-y-6">
            <div className="flex items-center gap-4 pb-4 border-b border-slate-100 dark:border-slate-900">
              <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-650 flex items-center justify-center text-white font-extrabold text-xl shadow-lg shadow-indigo-500/10 select-none">
                {user.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt={user.full_name}
                    className="h-full w-full object-cover rounded-2xl"
                  />
                ) : (
                  user.full_name.split(" ").map((n) => n[0]).join("")
                )}
              </div>
              <div>
                <h3 className="text-sm font-black text-slate-850 dark:text-white flex items-center gap-2">
                  {user.full_name}
                  <Badge variant="success" className="text-[9px] px-1.5 py-0">
                    Online
                  </Badge>
                </h3>
                <p className="text-[10px] text-slate-450 dark:text-slate-500 font-mono mt-0.5">
                  @{user.username}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="flex items-center gap-3 p-3.5 rounded-xl border border-slate-100 dark:border-slate-900 bg-slate-50/40 dark:bg-slate-900/10">
                <Mail className="h-4.5 w-4.5 text-indigo-500" />
                <div>
                  <h4 className="text-[9px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                    Email Contact
                  </h4>
                  <p className="font-semibold text-slate-750 dark:text-slate-205 truncate">
                    {user.email}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3.5 rounded-xl border border-slate-100 dark:border-slate-900 bg-slate-50/40 dark:bg-slate-900/10">
                <Shield className="h-4.5 w-4.5 text-indigo-500" />
                <div>
                  <h4 className="text-[9px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                    Security Authorization
                  </h4>
                  <p className="font-semibold text-slate-750 dark:text-slate-205 flex items-center gap-1.5">
                    Role: <span className="font-mono text-[10px] bg-slate-150 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-1.5 py-0.5 rounded-md font-bold">{user.role.name}</span>
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3.5 rounded-xl border border-slate-100 dark:border-slate-900 bg-slate-50/40 dark:bg-slate-900/10">
                <Compass className="h-4.5 w-4.5 text-indigo-500" />
                <div>
                  <h4 className="text-[9px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                    Workspace Locale
                  </h4>
                  <p className="font-semibold text-slate-750 dark:text-slate-205">
                    TZ: {user.timezone} ({user.language.toUpperCase()})
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3.5 rounded-xl border border-slate-100 dark:border-slate-900 bg-slate-50/40 dark:bg-slate-900/10">
                <Calendar className="h-4.5 w-4.5 text-indigo-500" />
                <div>
                  <h4 className="text-[9px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                    Register Epoch
                  </h4>
                  <p className="font-semibold text-slate-750 dark:text-slate-205">
                    {new Date(user.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Quick Metrics */}
          <Card className="p-6 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="border-b border-slate-100 dark:border-slate-900 pb-3">
                <h3 className="text-xs font-black text-slate-805 dark:text-slate-200">
                  Node Status
                </h3>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs py-1">
                  <span className="text-slate-500">API Latency</span>
                  <span className="font-mono font-bold text-emerald-500">24ms (Optimal)</span>
                </div>
                <div className="flex items-center justify-between text-xs py-1">
                  <span className="text-slate-500">Secure Database</span>
                  <span className="font-mono font-bold text-emerald-500">Connected</span>
                </div>
                <div className="flex items-center justify-between text-xs py-1">
                  <span className="text-slate-500">Local Cache</span>
                  <span className="font-mono font-bold text-emerald-500">Redis 7 Active</span>
                </div>
              </div>
            </div>

            <div className="p-3.5 rounded-xl border border-dashed border-slate-250 dark:border-slate-800 bg-slate-50/20 dark:bg-slate-950/20 mt-6 flex items-start gap-2.5">
              <Activity className="h-4.5 w-4.5 text-indigo-500 shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <h4 className="text-[10px] font-bold text-slate-800 dark:text-slate-200">
                  Identity Container Clean
                </h4>
                <p className="text-[9px] text-slate-450 dark:text-slate-500 leading-relaxed">
                  Authentication signatures are stored cryptographically and session refresh occurs silently.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </SectionContainer>

      <LandingFooter />
    </PageWrapper>
  );
}
