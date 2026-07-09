"use client";

import React from "react";
import { motion } from "framer-motion";
import { ArrowDown, Brain, Database, Layers, Network, Server } from "lucide-react";

interface NodeItem {
  id: string;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  subtitle: string;
  color: string;
  details: string[];
}

const architectureNodes: NodeItem[] = [
  {
    id: "frontend",
    icon: Layers,
    title: "Client Application",
    subtitle: "Next.js 15 Client",
    color: "from-indigo-500 to-indigo-650",
    details: ["SSR / ISR App Router", "Zustand Global State", "Tailwind CSS + shadcn/ui"],
  },
  {
    id: "backend",
    icon: Server,
    title: "Core Service API",
    subtitle: "FastAPI REST Server",
    color: "from-purple-500 to-purple-650",
    details: ["Pydantic v2 Type Check", "CORS Middleware validation", "Clean Architecture layer"],
  },
  {
    id: "ai",
    icon: Brain,
    title: "AI & RAG Engine",
    subtitle: "Local LLM Orchestration",
    color: "from-pink-500 to-pink-650",
    details: ["Vector Embeddings database", "Private context retrieval", "Agent planning hooks"],
  },
  {
    id: "database",
    icon: Database,
    title: "Storage Engine",
    subtitle: "Postgres + Redis Layer",
    color: "from-emerald-500 to-emerald-650",
    details: ["SQLAlchemy transaction DB", "Redis background cache", "Data volumes isolation"],
  },
  {
    id: "deployment",
    icon: Network,
    title: "Containerization",
    subtitle: "Docker & Compose Stack",
    color: "from-amber-500 to-amber-650",
    details: ["Multi-stage Docker builds", "Isolated bridge network", "Compose container health"],
  },
];

export default function ArchitectureFlow() {
  return (
    <section id="architecture" className="py-24 bg-slate-950 border-t border-slate-900 relative">
      <div className="container mx-auto px-4 max-w-5xl">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-20">
          <h2 className="text-3xl md:text-5xl font-extrabold text-white tracking-tight mb-4">
            System Architecture Flow
          </h2>
          <p className="text-slate-400 text-lg">
            LifePilot AI operates a highly secure, containerized multi-tier framework, built to
            scale from local boxes to private staging setups.
          </p>
        </div>

        {/* Dynamic Nodes Container */}
        <div className="relative flex flex-col items-center gap-12">
          {/* Vertical flow connector line */}
          <div className="absolute top-10 bottom-10 left-1/2 -translate-x-1/2 w-0.5 bg-slate-900 pointer-events-none hidden md:block">
            <motion.div
              animate={{
                top: ["0%", "100%"],
                opacity: [0, 1, 0],
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: "linear",
              }}
              className="absolute left-0 w-full h-1/5 bg-gradient-to-b from-transparent via-indigo-500 to-transparent"
            />
          </div>

          {architectureNodes.map((node, index) => {
            const IconComponent = node.icon;
            const isEven = index % 2 === 0;

            return (
              <motion.div
                key={node.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className={`relative w-full flex flex-col md:flex-row items-center justify-between gap-6 md:gap-0 ${
                  isEven ? "" : "md:flex-row-reverse"
                }`}
              >
                {/* 1. Node Card */}
                <div className="w-full md:w-[42%] z-10">
                  <motion.div
                    whileHover={{ y: -4 }}
                    className="p-6 rounded-2xl border border-slate-900 bg-slate-900/10 hover:border-slate-800 hover:bg-slate-900/25 transition-all shadow-xl group relative overflow-hidden"
                  >
                    {/* Glowing highlight border */}
                    <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/0 via-transparent to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

                    <div className="flex gap-4">
                      {/* Node Circle */}
                      <div
                        className={`h-11 w-11 rounded-xl bg-gradient-to-br ${node.color} flex items-center justify-center flex-shrink-0 shadow-lg`}
                      >
                        <IconComponent className="h-5.5 w-5.5 text-white" />
                      </div>
                      <div className="space-y-1">
                        <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors">
                          {node.title}
                        </h3>
                        <p className="text-xs text-slate-500 font-mono">{node.subtitle}</p>
                      </div>
                    </div>

                    <ul className="mt-4 pt-4 border-t border-slate-950 text-xs text-slate-400 space-y-2 text-left leading-relaxed">
                      {node.details.map((detail, idx) => (
                        <li key={idx} className="flex items-center gap-2">
                          <span className="h-1 w-1 bg-indigo-500 rounded-full" />
                          <span>{detail}</span>
                        </li>
                      ))}
                    </ul>
                  </motion.div>
                </div>

                {/* 2. Middle Intersection Anchor (Vertical connector anchor) */}
                <div className="absolute left-1/2 -translate-x-1/2 h-8 w-8 rounded-full bg-slate-950 border border-slate-900 flex items-center justify-center z-20 hidden md:flex shadow-xl shadow-slate-950">
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                    className="h-2 w-2 rounded-full bg-indigo-500"
                  />
                </div>

                {/* 3. Empty slot side to maintain center alignment */}
                <div className="w-full md:w-[42%] pointer-events-none hidden md:block" />

                {/* Downwards arrow for mobile view */}
                {index < architectureNodes.length - 1 && (
                  <div className="block md:hidden text-slate-800">
                    <ArrowDown className="h-5 w-5" />
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
