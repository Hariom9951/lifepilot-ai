"use client";

import React from "react";
import { motion } from "framer-motion";
import { Brain } from "lucide-react";

export default function Loading() {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white dark:bg-slate-950 transition-colors duration-300">
      <div className="flex flex-col items-center gap-4">
        {/* Pulsing and spinning logo wrapper */}
        <motion.div
          animate={{
            scale: [1, 1.1, 1],
            rotate: [0, 360],
          }}
          transition={{
            duration: 2.5,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-xl shadow-indigo-500/25"
        >
          <Brain className="h-8 w-8 text-white" />
        </motion.div>

        {/* Loading text */}
        <div className="flex flex-col items-center gap-1.5 mt-2">
          <span className="text-xs font-extrabold uppercase font-mono tracking-widest text-indigo-500 dark:text-indigo-400">
            LifePilot AI
          </span>
          <span className="text-[10px] text-slate-400 dark:text-slate-550 font-mono tracking-wide animate-pulse">
            Configuring workspace...
          </span>
        </div>
      </div>
    </div>
  );
}
