"use client";

import React from "react";
import { motion } from "framer-motion";
import { CalendarCheck, Circle, Sparkles } from "lucide-react";

interface PhaseItem {
  phase: string;
  title: string;
  description: string;
  status: "completed" | "in-progress" | "planned";
}

const roadmapPhases: PhaseItem[] = [
  {
    phase: "Phase 1",
    title: "Project Foundation",
    description:
      "Initialize FastAPI and Next.js, structure quality checkers (Ruff, ESLint), and set up multi-stage Docker Compose.",
    status: "completed",
  },
  {
    phase: "Phase 2",
    title: "Secure Authentication",
    description:
      "Implement JWT validations, cookie session management, user credentials encryption, and signup routines.",
    status: "planned",
  },
  {
    phase: "Phase 3",
    title: "Client Dashboard",
    description:
      "Launch unified page layouts, widgets aggregation, responsive grids, and clean states orchestration.",
    status: "planned",
  },
  {
    phase: "Phase 4",
    title: "Task Scheduler",
    description:
      "Build robust CRUD APIs, prioritization tagging, subtasks aggregation, and calendar synchronizations.",
    status: "planned",
  },
  {
    phase: "Phase 5",
    title: "Goal Planner",
    description:
      "Structure quarterly targets, OKRs, progress timelines, and milestone tracking databases.",
    status: "planned",
  },
  {
    phase: "Phase 6",
    title: "Habits Loops",
    description:
      "Establish habit triggers, streak records, frequency constraints, and grid status updates.",
    status: "planned",
  },
  {
    phase: "Phase 7",
    title: "Wallet Hub",
    description:
      "Develop transaction lists, expense category allocations, budget targets, and monthly ledger balances.",
    status: "planned",
  },
  {
    phase: "Phase 8",
    title: "Holistic Analytics",
    description:
      "Consolidate habits performance, closed tasks metadata, and expenses to display performance insights.",
    status: "planned",
  },
  {
    phase: "Phase 9",
    title: "Conversational Assistant",
    description:
      "Mount local LLMs, chat response streams, scheduling suggestions, and personalized tip builders.",
    status: "planned",
  },
  {
    phase: "Phase 10",
    title: "RAG Context Search",
    description:
      "Index private markdown files, scan documents dynamically, and supply context-aware query responses securely.",
    status: "planned",
  },
  {
    phase: "Phase 11",
    title: "Cloud Deployments",
    description:
      "Establish remote host configs, pipeline triggers, automated testing, and secure staging environments.",
    status: "planned",
  },
];

export default function RoadmapTimeline() {
  return (
    <section id="roadmap" className="py-24 bg-slate-950 border-t border-slate-900 relative">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Section Header */}
        <div className="text-center mb-20">
          <h2 className="text-3xl md:text-5xl font-extrabold text-white tracking-tight mb-4">
            Development Roadmap
          </h2>
          <p className="text-slate-400 text-lg">
            Track our progress from monorepo foundation to local LLM context search and hosting.
          </p>
        </div>

        {/* Timeline container */}
        <div className="relative">
          {/* Vertical central path line */}
          <div className="absolute top-8 bottom-8 left-4 md:left-1/2 -translate-x-1/2 w-0.5 bg-slate-900 pointer-events-none" />

          <div className="space-y-12">
            {roadmapPhases.map((item, index) => {
              const isCompleted = item.status === "completed";
              const isEven = index % 2 === 0;

              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 25 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-50px" }}
                  transition={{ duration: 0.5, delay: index * 0.05 }}
                  className={`relative flex flex-col md:flex-row items-stretch gap-6 md:gap-0 ${
                    isEven ? "" : "md:flex-row-reverse"
                  }`}
                >
                  {/* Card */}
                  <div className="w-full md:w-[45%] pl-10 md:pl-0">
                    <motion.div
                      whileHover={{ scale: 1.01 }}
                      className={`p-5 rounded-2xl border ${
                        isCompleted
                          ? "border-indigo-500/20 bg-indigo-500/5 shadow-indigo-500/5 shadow-md"
                          : "border-slate-900 bg-slate-900/10"
                      } text-left relative overflow-hidden`}
                    >
                      {/* Left timeline indicator for mobile */}
                      <div className="absolute top-0 right-0 p-3 opacity-5 pointer-events-none">
                        <Sparkles className="h-16 w-16 text-indigo-400" />
                      </div>

                      <div className="flex justify-between items-center mb-3">
                        <span className="text-[10px] font-bold font-mono tracking-wider px-2.5 py-0.5 rounded bg-slate-950 border border-slate-850 text-indigo-400 uppercase">
                          {item.phase}
                        </span>

                        {/* Status Badge */}
                        <span
                          className={`text-[9px] font-bold font-mono tracking-wide uppercase px-2 py-0.5 rounded ${
                            isCompleted
                              ? "bg-indigo-500/15 text-indigo-300"
                              : "bg-slate-900 text-slate-500"
                          }`}
                        >
                          {item.status}
                        </span>
                      </div>

                      <h3 className="text-base font-bold text-white mb-2">{item.title}</h3>
                      <p className="text-xs text-slate-500 leading-relaxed">{item.description}</p>
                    </motion.div>
                  </div>

                  {/* Dot Intersection */}
                  <div className="absolute left-4 md:left-1/2 -translate-x-1/2 top-6 h-6.5 w-6.5 rounded-full bg-slate-950 border border-slate-900 flex items-center justify-center z-10 shadow-lg">
                    {isCompleted ? (
                      <CalendarCheck className="h-4.5 w-4.5 text-indigo-400" />
                    ) : (
                      <Circle className="h-3 w-3 text-slate-700 fill-slate-700" />
                    )}
                  </div>

                  {/* Spacer helper */}
                  <div className="w-full md:w-[45%] pointer-events-none hidden md:block" />
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
