"use client";

import React from "react";
import { motion } from "framer-motion";
import { Brain, Database, Layers, Network, Server } from "lucide-react";

interface TechItem {
  name: string;
  purpose: string;
}

interface TechCardProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  techs: TechItem[];
  colorClass: string;
}

const techStackData: TechCardProps[] = [
  {
    icon: Layers,
    title: "Frontend Core",
    colorClass: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20",
    techs: [
      { name: "Next.js 15", purpose: "Client framework & Standalone builds" },
      { name: "TypeScript", purpose: "Strict type verification compiler" },
      { name: "Tailwind CSS", purpose: "Highly optimized utility styling" },
      { name: "shadcn/ui", purpose: "Modular layout UI components" },
    ],
  },
  {
    icon: Server,
    title: "Backend Core",
    colorClass: "text-purple-400 bg-purple-500/10 border-purple-500/20",
    techs: [
      { name: "FastAPI", purpose: "Asynchronous Python routing framework" },
      { name: "Poetry", purpose: "Strict package lock and dependency tool" },
      { name: "Uvicorn", purpose: "ASGI high-performance server" },
      { name: "Pydantic v2", purpose: "Strict runtime configuration validation" },
    ],
  },
  {
    icon: Database,
    title: "Database & Cache",
    colorClass: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    techs: [
      { name: "PostgreSQL 16", purpose: "Relational storage for app domains" },
      { name: "Redis 7", purpose: "Key-value backend memory cache" },
      { name: "Docker Volumes", purpose: "Isolated file system persistent layers" },
    ],
  },
  {
    icon: Brain,
    title: "Local AI & RAG",
    colorClass: "text-pink-400 bg-pink-500/10 border-pink-500/20",
    techs: [
      { name: "LlamaIndex", purpose: "Structure file data context ingestion" },
      { name: "VectorDB", purpose: "Secure embedding lookup collections" },
      { name: "Local LLM", purpose: "In-network text generation query parsing" },
    ],
  },
  {
    icon: Network,
    title: "DevOps & Quality",
    colorClass: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    techs: [
      { name: "Docker Compose", purpose: "Multi-container developer workspace" },
      { name: "GitHub Actions", purpose: "Auto-lint check validation triggers" },
      { name: "Ruff / Black", purpose: "Fast Python linter and code formatter" },
      { name: "ESLint / Prettier", purpose: "Clean frontend quality integration" },
    ],
  },
];

export default function TechStackSection() {
  const containerVariants = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6 },
    },
  };

  return (
    <section id="tech-stack" className="py-24 bg-slate-950 border-t border-slate-900">
      <div className="container mx-auto px-4 max-w-5xl">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-20">
          <h2 className="text-3xl md:text-5xl font-extrabold text-white tracking-tight mb-4">
            Production Technology Stack
          </h2>
          <p className="text-slate-400 text-lg">
            Strictly selected libraries chosen for high performance, reliability, and security
            compliance.
          </p>
        </div>

        {/* Tech Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6"
        >
          {techStackData.map((card, index) => {
            const IconComponent = card.icon;
            return (
              <motion.div
                key={index}
                variants={itemVariants}
                whileHover={{ y: -4 }}
                className="group p-5 rounded-2xl border border-slate-900 bg-slate-900/10 hover:border-slate-800 hover:bg-slate-900/25 transition-all shadow-lg flex flex-col justify-between"
              >
                <div>
                  {/* Card Header Icon & Title */}
                  <div className="flex items-center gap-2.5 mb-5 border-b border-slate-950 pb-3">
                    <div className={`p-2 rounded-lg border ${card.colorClass}`}>
                      <IconComponent className="h-5 w-5" />
                    </div>
                    <h3 className="text-xs font-extrabold text-slate-300 uppercase tracking-wider">
                      {card.title}
                    </h3>
                  </div>

                  {/* Tech item lists */}
                  <ul className="space-y-4 text-left">
                    {card.techs.map((tech, idx) => (
                      <li key={idx} className="space-y-0.5 font-sans">
                        <span className="block text-xs font-bold text-slate-200 group-hover:text-indigo-300 transition-colors">
                          {tech.name}
                        </span>
                        <span className="block text-[10px] text-slate-500 leading-normal">
                          {tech.purpose}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
