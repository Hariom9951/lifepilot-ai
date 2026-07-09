"use client";

import React from "react";
import { motion } from "framer-motion";
import { ChevronRight, Sparkles } from "lucide-react";

const GithubIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

export default function HeroSection() {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center pt-28 pb-16 overflow-hidden bg-slate-950">
      {/* Dynamic Animated Gradient Background */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <motion.div
          animate={{
            scale: [1, 1.1, 0.95, 1],
            x: [0, 40, -30, 0],
            y: [0, -30, 50, 0],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute -top-[10%] left-[15%] w-[450px] h-[450px] rounded-full bg-indigo-600/25 blur-[100px]"
        />
        <motion.div
          animate={{
            scale: [1, 0.9, 1.15, 1],
            x: [0, -50, 40, 0],
            y: [0, 40, -30, 0],
          }}
          transition={{
            duration: 18,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute -top-[5%] right-[15%] w-[400px] h-[400px] rounded-full bg-purple-600/20 blur-[90px]"
        />
      </div>

      <div className="container mx-auto px-4 z-10 text-center relative flex flex-col items-center">
        {/* Trusted Badge */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full text-xs font-medium bg-slate-900/60 border border-indigo-500/20 text-indigo-300 backdrop-blur-md shadow-indigo-500/5 shadow-md mb-8 hover:border-indigo-500/40 transition-colors cursor-pointer group"
        >
          <Sparkles className="h-3.5 w-3.5 text-indigo-400 group-hover:rotate-12 transition-transform" />
          <span>Built with FastAPI + Next.js + AI</span>
        </motion.div>

        {/* Title */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="text-4xl sm:text-6xl md:text-7.5xl font-extrabold tracking-tight text-white max-w-5xl leading-[1.1] mb-6"
        >
          Navigate Your Life with <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-500 bg-clip-text text-transparent relative">
            AI-Driven Clarity
            {/* Ambient glow behind text */}
            <span className="absolute -inset-x-6 top-1/2 h-8 bg-indigo-500/15 blur-2xl -z-10 rounded-full" />
          </span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-lg md:text-xl text-slate-400 max-w-3xl mb-12 leading-relaxed font-normal"
        >
          A seamless, personal life operating system that orchestrates your tasks, habits, expenses,
          and notes with secure, local-first artificial intelligence.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-20"
        >
          <a
            href="#preview"
            className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-3.5 rounded-xl text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-500 shadow-xl shadow-indigo-600/20 hover:shadow-indigo-600/35 hover:-translate-y-0.5 transition-all gap-2.5 active:scale-[0.98]"
          >
            Get Started
            <ChevronRight className="h-4.5 w-4.5" />
          </a>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-3.5 rounded-xl text-sm font-semibold bg-slate-900/80 border border-slate-800 text-slate-200 hover:bg-slate-850 hover:text-white hover:border-slate-700 transition-all gap-2.5 hover:-translate-y-0.5 active:scale-[0.98]"
          >
            <GithubIcon className="h-4.5 w-4.5" />
            View GitHub
          </a>
        </motion.div>

        {/* Floating UI Elements */}
        <div className="absolute top-[35%] left-[8%] hidden xl:block z-20">
          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
            className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-md text-xs font-mono text-indigo-400 shadow-lg shadow-black/20"
          >
            <span className="h-2 w-2 rounded-full bg-indigo-500 animate-pulse" />
            <span>Tasks Synchronized</span>
          </motion.div>
        </div>

        <div className="absolute top-[45%] right-[8%] hidden xl:block z-20">
          <motion.div
            animate={{ y: [0, 10, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
            className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-md text-xs font-mono text-emerald-400 shadow-lg shadow-black/20"
          >
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Local AI Ready</span>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
