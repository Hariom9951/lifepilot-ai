"use client";

import React from "react";
import { motion } from "framer-motion";
import { Check, Info, ShieldAlert, Sparkles, X } from "lucide-react";

export default function WhyLifePilot() {
  return (
    <section className="py-24 bg-slate-950 border-t border-slate-900 relative">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Section Header */}
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-3xl md:text-5xl font-extrabold text-white tracking-tight mb-4">
              Why LifePilot AI?
            </h2>
            <p className="text-slate-400 text-lg">
              Stop juggling isolated apps. LifePilot joins your tasks, finances, habits, and
              knowledge base into a single, cohesive engine.
            </p>
          </motion.div>
        </div>

        {/* Comparison Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative">
          {/* Traditional Apps Column */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="rounded-2xl border border-slate-900 bg-slate-950 p-6 md:p-8 space-y-6 relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 p-3 opacity-5 pointer-events-none">
              <ShieldAlert className="h-24 w-24 text-red-500" />
            </div>

            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-red-500/10 flex items-center justify-center text-red-400 border border-red-500/20">
                <X className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-200">Traditional Setup</h3>
                <p className="text-xs text-slate-500 font-mono mt-0.5">Shattered Productivity</p>
              </div>
            </div>

            <div className="space-y-4 pt-4 border-t border-slate-900">
              {[
                {
                  title: "Multiple Scattered Apps",
                  desc: "Forcing you to jump between checklists, budgeting sheets, calendar blocks, and note apps.",
                },
                {
                  title: "Manual Planning Overhead",
                  desc: "No intelligence schedules your blocks; you must waste hours cataloging items manually.",
                },
                {
                  title: "No Local AI Integration",
                  desc: "Third-party extensions leak data to external servers or cost heavy monthly API subscriptions.",
                },
                {
                  title: "Zero Domain Memory",
                  desc: "Budget tools don't talk to task apps, habits loops don't check your calendar, zero context overlap.",
                },
              ].map((item, idx) => (
                <div key={idx} className="flex gap-3">
                  <div className="h-5 w-5 rounded-full bg-red-950/40 border border-red-900/60 flex items-center justify-center flex-shrink-0 text-red-500 mt-0.5">
                    <X className="h-3 w-3" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-300">{item.title}</h4>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* LifePilot AI Column */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="rounded-2xl border border-indigo-500/25 bg-slate-900/40 p-6 md:p-8 space-y-6 relative overflow-hidden shadow-2xl"
          >
            {/* Background spotlight */}
            <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/5 via-transparent to-transparent pointer-events-none -z-10" />
            <div className="absolute top-0 right-0 p-3 opacity-5 pointer-events-none">
              <Sparkles className="h-24 w-24 text-indigo-400" />
            </div>

            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/30 shadow-indigo-500/10 shadow-md">
                <Check className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-1.5">
                  LifePilot AI
                  <span className="text-[10px] font-bold font-mono tracking-wider px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 uppercase">
                    Unified
                  </span>
                </h3>
                <p className="text-xs text-indigo-400 font-mono mt-0.5">AI-Powered Life OS</p>
              </div>
            </div>

            <div className="space-y-4 pt-4 border-t border-slate-900">
              {[
                {
                  title: "One Unified Platform",
                  desc: "A singular, responsive workspace coordinating tasks, calendar items, budgets, and habit tracking.",
                },
                {
                  title: "Intelligent AI Planning",
                  desc: "Your background assistant scans timelines and habits to propose daily blocks automatically.",
                },
                {
                  title: "Secure Context Memory",
                  desc: "Retrieves context using local vectors, keeping your habits, budgets, and files private.",
                },
                {
                  title: "Cross-Domain Optimization",
                  desc: "Budget allocations prompt schedule reviews, tasks completed trigger habit updates automatically.",
                },
              ].map((item, idx) => (
                <div key={idx} className="flex gap-3">
                  <div className="h-5 w-5 rounded-full bg-indigo-950/40 border border-indigo-800/60 flex items-center justify-center flex-shrink-0 text-indigo-400 mt-0.5 shadow-sm shadow-indigo-500/5">
                    <Check className="h-3 w-3" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">{item.title}</h4>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Ambient notice */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mt-12 p-4 rounded-xl border border-slate-900 bg-slate-950/60 text-slate-500 text-xs flex gap-2.5 items-center justify-center"
        >
          <Info className="h-4.5 w-4.5 text-slate-600 flex-shrink-0" />
          <span>
            LifePilot AI acts as a secure container: data resides in your system, not in third-party
            marketing databases.
          </span>
        </motion.div>
      </div>
    </section>
  );
}
