"use client";

import React from "react";
import { Activity, AlertCircle, Database, Server, Cpu, Layers, HardDrive } from "lucide-react";
import { PageWrapper } from "@/layouts/PageWrapper";
import { SectionContainer } from "@/layouts/SectionContainer";
import Navbar from "@/layouts/Navbar";
import LandingFooter from "@/features/landing/components/LandingFooter";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function StatusPage() {
  const systems = [
    {
      name: "Frontend Services",
      type: "Next.js Dev Server",
      status: "operational",
      desc: "Prerendering routes, Turbopack bundle validation, next-themes active.",
      icon: Layers,
    },
    {
      name: "Backend Framework",
      type: "FastAPI / Python",
      status: "operational",
      desc: "Uvicorn worker running on port 8000, API router context mapped.",
      icon: Server,
    },
    {
      name: "Relational Database",
      type: "PostgreSQL 16",
      status: "mocked",
      desc: "Local PostgreSQL database instance defined; active connection deferred to Phase 2.",
      icon: Database,
    },
    {
      name: "Memory Cache Store",
      type: "Redis Cache",
      status: "mocked",
      desc: "Redis cache configurations defined; session persistent binding deferred to Phase 2.",
      icon: HardDrive,
    },
    {
      name: "Local AI Engine",
      type: "Ollama / Gemini API",
      status: "operational",
      desc: "Dev fallbacks configured. Active search queries simulate RAG indexing logs.",
      icon: Cpu,
    },
    {
      name: "Docker Containerization",
      type: "Docker Compose",
      status: "operational",
      desc: "Compose definitions valid, development container templates loaded.",
      icon: Activity,
    },
  ];

  return (
    <PageWrapper className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 font-sans">
      <Navbar />

      <SectionContainer className="max-w-4xl py-12 md:py-16">
        {/* Page Title */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/60 dark:border-slate-900 pb-8 mb-10">
          <div>
            <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white mb-2">
              System Status
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Live checks and service availability parameters.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-widest font-mono">
              Development Mode Active
            </span>
          </div>
        </div>

        {/* Warning Indicator */}
        <div className="rounded-2xl border border-amber-500/10 bg-amber-500/5 p-4 flex gap-3.5 items-start mb-8">
          <AlertCircle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-xs font-bold text-amber-800 dark:text-amber-400 font-mono uppercase tracking-wider">
              Health Check Notice
            </h4>
            <p className="text-[11px] text-amber-750/80 dark:text-amber-500/85 leading-relaxed">
              These systems are executing under **Development Mode**. Some status metrics represent
              simulated mock states. Real health check endpoints will hook directly into our
              PostgreSQL and Redis servers during Phase 2.
            </p>
          </div>
        </div>

        {/* Grid Systems */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-16">
          {systems.map((s, index) => {
            const isOperational = s.status === "operational";
            const Icon = s.icon;

            return (
              <Card key={index} className="p-5 flex flex-col justify-between min-h-[160px]">
                <div>
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-lg bg-slate-100 dark:bg-slate-950 border border-slate-200/50 dark:border-slate-800/40 text-slate-500 dark:text-slate-400">
                        <Icon className="h-4.5 w-4.5" />
                      </div>
                      <div>
                        <h3 className="text-xs font-black text-slate-850 dark:text-slate-200">
                          {s.name}
                        </h3>
                        <p className="text-[9px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider font-mono">
                          {s.type}
                        </p>
                      </div>
                    </div>

                    <Badge variant={isOperational ? "success" : "warning"} size="sm">
                      {isOperational ? "Operational" : "Simulated"}
                    </Badge>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed font-sans">
                    {s.desc}
                  </p>
                </div>
              </Card>
            );
          })}
        </div>
      </SectionContainer>

      <LandingFooter />
    </PageWrapper>
  );
}
