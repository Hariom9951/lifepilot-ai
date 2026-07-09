"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  Activity,
  Calendar,
  CheckSquare,
  DollarSign,
  FileText,
  Heart,
  LineChart,
  MessageSquare,
  Search,
  Sparkles,
} from "lucide-react";

interface FeatureItem {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  badgeText: string;
  badgeType: "core" | "upcoming" | "ai";
}

const featuresList: FeatureItem[] = [
  {
    icon: Sparkles,
    title: "AI Personal Assistant",
    description:
      "Proactive suggestions checking your schedule, habits, and budgets to recommend optimal daily plans.",
    badgeText: "Phase 9",
    badgeType: "ai",
  },
  {
    icon: Calendar,
    title: "Smart Daily Planner",
    description:
      "Integrated daily schedule timelines, event synchronization, and intelligent task blocking.",
    badgeText: "Core",
    badgeType: "core",
  },
  {
    icon: CheckSquare,
    title: "Goal Management",
    description:
      "Structure quarterly targets, OKRs, and yearly objectives with child-milestone tracking.",
    badgeText: "Phase 5",
    badgeType: "upcoming",
  },
  {
    icon: Activity,
    title: "Habit Tracker",
    description:
      "Streaks, calendars, custom frequencies, reminders, and daily habit compliance widgets.",
    badgeText: "Phase 6",
    badgeType: "upcoming",
  },
  {
    icon: DollarSign,
    title: "Expense Manager",
    description:
      "Budget envelopes, receipt scans, custom ledger categories, and monthly financial summaries.",
    badgeText: "Phase 7",
    badgeType: "upcoming",
  },
  {
    icon: FileText,
    title: "Notes & Knowledge",
    description:
      "Rich text notes, markdown attachments, and structured journal files saved securely.",
    badgeText: "Core",
    badgeType: "core",
  },
  {
    icon: MessageSquare,
    title: "AI Chat Workspace",
    description:
      "Conversational query dashboard referencing logged facts, notes, and habits over time.",
    badgeText: "Phase 9",
    badgeType: "ai",
  },
  {
    icon: Search,
    title: "RAG Semantic Search",
    description:
      "Leverage vectors to fetch information and synthesize answers directly from your private documents.",
    badgeText: "Phase 10",
    badgeType: "ai",
  },
  {
    icon: Heart,
    title: "Health Integration",
    description: "Synchronize sleep patterns, activity logs, water intake, and caloric targets.",
    badgeText: "Phase 12",
    badgeType: "upcoming",
  },
  {
    icon: LineChart,
    title: "Holistic Analytics",
    description:
      "Consolidated performance data tracking habits completed, budgets spent, and tasks closed.",
    badgeText: "Phase 8",
    badgeType: "upcoming",
  },
];

export default function FeaturesGrid() {
  const containerVariants = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6, ease: "easeOut" as const },
    },
  };

  return (
    <section id="features" className="py-24 bg-slate-950 border-t border-slate-900 relative">
      {/* Background radial accent */}
      <div className="absolute top-[20%] left-1/2 -translate-x-1/2 w-[700px] h-[700px] bg-purple-900/5 blur-[120px] rounded-full pointer-events-none -z-10" />

      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-20">
          <h2 className="text-3xl md:text-5xl font-extrabold text-white tracking-tight mb-4">
            Unified Life Management Modules
          </h2>
          <p className="text-slate-400 text-lg">
            Ten deeply integrated features operating under a single user interface, engineered for
            privacy and speed.
          </p>
        </div>

        {/* Features Cards Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6"
        >
          {featuresList.map((item, index) => {
            const IconComponent = item.icon;
            return (
              <motion.div
                key={index}
                variants={cardVariants}
                whileHover={{ y: -6, scale: 1.02 }}
                className="group relative p-6 rounded-2xl border border-slate-900/80 bg-slate-900/10 hover:border-slate-800 hover:bg-slate-900/25 transition-all shadow-lg flex flex-col justify-between min-h-[220px]"
              >
                {/* Visual card glow effect */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500/0 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

                <div>
                  {/* Top Bar inside card */}
                  <div className="flex justify-between items-center mb-5">
                    <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-850 group-hover:border-indigo-500/30 group-hover:bg-indigo-500/5 transition-all">
                      <IconComponent className="h-5.5 w-5.5 text-slate-400 group-hover:text-indigo-400 transition-colors" />
                    </div>

                    {/* Badge */}
                    <span
                      className={`text-[9px] font-bold font-mono tracking-wider uppercase px-2.5 py-0.5 rounded-full border ${
                        item.badgeType === "core"
                          ? "bg-slate-900 border-slate-800 text-slate-400"
                          : item.badgeType === "ai"
                            ? "bg-indigo-500/10 border-indigo-500/20 text-indigo-400 shadow-sm shadow-indigo-500/5"
                            : "bg-purple-500/10 border-purple-500/20 text-purple-400"
                      }`}
                    >
                      {item.badgeText}
                    </span>
                  </div>

                  {/* Title & Desc */}
                  <h3 className="text-base font-bold text-white mb-2 group-hover:text-indigo-300 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-500 group-hover:text-slate-400 transition-colors leading-relaxed">
                    {item.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
