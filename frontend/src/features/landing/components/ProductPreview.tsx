"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  Brain,
  Calendar,
  CheckCircle2,
  CheckSquare,
  Clock,
  Compass,
  DollarSign,
  FileText,
  Home,
  Send,
  Settings,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";

export default function ProductPreview() {
  const [activeTab, setActiveTab] = useState("Dashboard");
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([
    {
      sender: "AI",
      text: "Good morning! Based on your goals today, I suggest starting with the monorepo deployment config, as it unblocks your CI workflow.",
      time: "9:00 AM",
    },
    {
      sender: "User",
      text: "Thanks! What is my habit streak looking like?",
      time: "9:02 AM",
    },
    {
      sender: "AI",
      text: "You are on a 5-day streak for Coding Practice and a 12-day streak for Morning Standup. Keep it up!",
      time: "9:02 AM",
    },
  ]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg = { sender: "User", text: chatInput, time: "Just now" };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput("");

    setTimeout(() => {
      const aiResponse = {
        sender: "AI",
        text: "I am scanning your vector database... Your notes show you planned to review budget details this afternoon.",
        time: "Just now",
      };
      setChatMessages((prev) => [...prev, aiResponse]);
    }, 1000);
  };

  return (
    <section id="preview" className="py-20 bg-slate-950 border-t border-slate-900 relative">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-3xl md:text-5xl font-extrabold text-white tracking-tight mb-4">
              Your Unified Personal Space
            </h2>
            <p className="text-slate-400 text-lg">
              Experience the clarity of a fully integrated interface where planning, habits, and
              budgets work in perfect harmony.
            </p>
          </motion.div>
        </div>

        {/* Realistic Dashboard Mockup Window */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="w-full max-w-6xl mx-auto rounded-2xl border border-slate-800 bg-slate-900/35 backdrop-blur-md shadow-3xl overflow-hidden relative"
        >
          {/* Glassmorphic border glow */}
          <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/5 via-transparent to-purple-500/5 rounded-2xl pointer-events-none -z-10" />

          {/* Top Window Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-900 bg-slate-950/60">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-red-500/70" />
              <div className="h-3 w-3 rounded-full bg-yellow-500/70" />
              <div className="h-3 w-3 rounded-full bg-green-500/70" />
              <div className="h-2.5 w-px bg-slate-800 mx-2" />
              <span className="text-xs text-slate-500 font-mono">dashboard.lifepilot.ai</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-mono">
                <Sparkles className="h-3 w-3" />
                AI Sync Active
              </div>
            </div>
          </div>

          <div className="flex flex-col lg:flex-row min-h-[680px]">
            {/* 1. Left Sidebar */}
            <aside className="w-full lg:w-60 border-r border-slate-900 bg-slate-950/50 p-4 flex flex-col justify-between">
              <div className="space-y-6">
                <div className="flex items-center gap-2.5 px-2">
                  <div className="h-7 w-7 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center">
                    <Brain className="h-4 w-4 text-white" />
                  </div>
                  <span className="text-sm font-bold text-slate-200">LifePilot OS</span>
                </div>

                <nav className="space-y-1">
                  {[
                    { name: "Dashboard", icon: Home },
                    { name: "Tasks", icon: CheckSquare },
                    { name: "Goals", icon: Target },
                    { name: "Habits", icon: Activity },
                    { name: "Expenses", icon: DollarSign },
                    { name: "AI Assistant", icon: Sparkles },
                    { name: "Notes", icon: FileText },
                  ].map((item) => {
                    const IconComp = item.icon;
                    const isActive = activeTab === item.name;
                    return (
                      <button
                        key={item.name}
                        onClick={() => setActiveTab(item.name)}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                          isActive
                            ? "bg-indigo-500/10 text-indigo-300 border-l-2 border-indigo-500 pl-2.5"
                            : "text-slate-500 hover:bg-slate-900 hover:text-slate-300"
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          <IconComp className="h-4 w-4" />
                          <span>{item.name}</span>
                        </div>
                        {item.name === "Tasks" && (
                          <span className="bg-slate-800 text-slate-400 font-mono px-1.5 py-0.5 rounded text-[10px]">
                            3
                          </span>
                        )}
                      </button>
                    );
                  })}
                </nav>
              </div>

              {/* Sidebar bottom */}
              <div className="pt-4 border-t border-slate-900/60">
                <button className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold text-slate-500 hover:bg-slate-900 hover:text-slate-300 transition-colors">
                  <Settings className="h-4 w-4" />
                  <span>Settings</span>
                </button>
              </div>
            </aside>

            {/* 2. Main Dashboard Area */}
            <main className="flex-1 p-6 space-y-6 bg-slate-950/20">
              {/* Top Summary Banner */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-900 pb-5">
                <div>
                  <h3 className="text-xl font-bold text-white">Daily Pilot</h3>
                  <p className="text-xs text-slate-500 font-mono mt-0.5">July 9, 2026</p>
                </div>
                <div className="flex items-center gap-2 text-xs font-semibold bg-indigo-500/10 border border-indigo-500/20 rounded-xl px-4 py-2 text-indigo-300 shadow-sm">
                  <Clock className="h-4 w-4 animate-spin-slow" />
                  <span>Next block: Project review (2:00 PM)</span>
                </div>
              </div>

              {/* Widgets Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 2a. Today's Schedule */}
                <div className="rounded-xl border border-slate-900 bg-slate-950/40 p-5 space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">
                      Today&apos;s Schedule
                    </span>
                    <Calendar className="h-4 w-4 text-slate-500" />
                  </div>
                  <div className="space-y-3 font-sans">
                    <div className="flex items-start gap-3 p-2.5 rounded-lg bg-indigo-500/5 border border-indigo-500/10">
                      <span className="text-xs font-mono text-indigo-400 mt-0.5">09:00</span>
                      <div>
                        <p className="text-xs font-semibold text-slate-200">Morning Standup</p>
                        <p className="text-[10px] text-slate-500">Synced to habits loop</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3 p-2.5 rounded-lg bg-slate-900/40 border border-slate-900">
                      <span className="text-xs font-mono text-slate-500 mt-0.5">11:00</span>
                      <div>
                        <p className="text-xs font-semibold text-slate-200">Coding Practice</p>
                        <p className="text-[10px] text-slate-500">Target: 2 hours</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3 p-2.5 rounded-lg bg-slate-900/40 border border-slate-900">
                      <span className="text-xs font-mono text-slate-500 mt-0.5">14:00</span>
                      <div>
                        <p className="text-xs font-semibold text-slate-200">Monorepo Review</p>
                        <p className="text-[10px] text-slate-400 font-medium">
                          Prioritized by AI Assistant
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 2b. Habit Streaks */}
                <div className="rounded-xl border border-slate-900 bg-slate-950/40 p-5 space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">
                      Habit Streaks
                    </span>
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  </div>
                  <div className="space-y-4">
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-300">Morning Standup</span>
                        <span className="text-emerald-400 font-mono">12 days 🔥</span>
                      </div>
                      <div className="flex gap-1.5">
                        {[1, 1, 1, 1, 1, 1, 1].map((val, idx) => (
                          <div
                            key={idx}
                            className="flex-1 h-3 rounded bg-emerald-500/25 border border-emerald-500/30"
                          />
                        ))}
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-300">Coding Practice</span>
                        <span className="text-purple-400 font-mono">5 days 🔥</span>
                      </div>
                      <div className="flex gap-1.5">
                        {[1, 1, 1, 1, 1, 0, 0].map((val, idx) => (
                          <div
                            key={idx}
                            className={`flex-1 h-3 rounded border ${
                              val
                                ? "bg-purple-500/25 border-purple-500/30"
                                : "bg-slate-900 border-slate-800"
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 2c. Budget & Expenses */}
                <div className="rounded-xl border border-slate-900 bg-slate-950/40 p-5 space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">
                      Budget Hub
                    </span>
                    <TrendingUp className="h-4 w-4 text-emerald-400" />
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-400">Total Spent</span>
                      <span className="font-mono text-slate-200 font-bold">$620.45 / $2,500</span>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-emerald-500 to-indigo-500 h-2 rounded-full"
                        style={{ width: "24.8%" }}
                      />
                    </div>
                    <div className="grid grid-cols-3 gap-2 pt-1.5 text-center text-[10px] font-mono">
                      <div className="bg-slate-900/60 p-1.5 rounded border border-slate-900 text-slate-400">
                        <span className="block font-sans text-slate-500">Food</span>
                        <span>$120</span>
                      </div>
                      <div className="bg-slate-900/60 p-1.5 rounded border border-slate-900 text-slate-400">
                        <span className="block font-sans text-slate-500">Software</span>
                        <span>$350</span>
                      </div>
                      <div className="bg-slate-900/60 p-1.5 rounded border border-slate-900 text-slate-400">
                        <span className="block font-sans text-slate-500">Utilities</span>
                        <span>$150</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 2d. Goals Progress */}
                <div className="rounded-xl border border-slate-900 bg-slate-950/40 p-5 space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">
                      Goals & Objectives
                    </span>
                    <Target className="h-4 w-4 text-indigo-400" />
                  </div>
                  <div className="space-y-3">
                    <div className="p-2.5 rounded-lg border border-slate-900 bg-slate-950/20 flex items-center justify-between">
                      <div>
                        <span className="text-xs font-semibold text-slate-200">
                          Deploy SaaS beta
                        </span>
                        <span className="block text-[9px] font-mono text-indigo-400 uppercase tracking-wider mt-0.5">
                          Q3 Goal
                        </span>
                      </div>
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300">
                        80%
                      </span>
                    </div>
                    <div className="p-2.5 rounded-lg border border-slate-900 bg-slate-950/20 flex items-center justify-between">
                      <div>
                        <span className="text-xs font-semibold text-slate-200">Read 12 books</span>
                        <span className="block text-[9px] font-mono text-purple-400 uppercase tracking-wider mt-0.5">
                          Annual
                        </span>
                      </div>
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-300">
                        50%
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick AI Suggestion Card */}
              <div className="rounded-xl border border-indigo-500/10 bg-indigo-500/5 p-4 flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-indigo-500/10 flex items-center justify-center flex-shrink-0 text-indigo-400">
                  <Compass className="h-4.5 w-4.5" />
                </div>
                <div className="text-xs leading-relaxed text-indigo-300">
                  <span className="font-semibold text-white">Assistant Recommendation:</span> You
                  have a budget overview scheduled with zero logged expenses under groceries this
                  week. Would you like me to auto-scan your receipts?
                </div>
              </div>
            </main>

            {/* 3. Right Sidebar AI Assistant Chat */}
            <aside className="w-full lg:w-76 border-t lg:border-t-0 lg:border-l border-slate-900 bg-slate-950/70 p-4 flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-slate-900 pb-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-indigo-400" />
                    <span className="text-xs font-bold text-slate-300">Copilot Chat</span>
                  </div>
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                </div>

                {/* Messages scroll box */}
                <div className="space-y-3 h-[420px] overflow-y-auto pr-1 text-xs scrollbar-thin">
                  {chatMessages.map((msg, idx) => {
                    const isAI = msg.sender === "AI";
                    return (
                      <div
                        key={idx}
                        className={`flex flex-col gap-1 ${isAI ? "items-start" : "items-end"}`}
                      >
                        <div
                          className={`px-3 py-2 rounded-xl max-w-[90%] leading-relaxed ${
                            isAI
                              ? "bg-slate-900 border border-slate-800 text-slate-300"
                              : "bg-indigo-600 text-white"
                          }`}
                        >
                          {msg.text}
                        </div>
                        <span className="text-[9px] text-slate-600 px-1 font-mono">{msg.time}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Chat Input form */}
              <form
                onSubmit={handleSendMessage}
                className="pt-4 border-t border-slate-900/60 flex items-center gap-2"
              >
                <input
                  type="text"
                  placeholder="Ask LifePilot assistant..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  className="flex-1 bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
                <button
                  type="submit"
                  className="bg-indigo-600 text-white p-2 rounded-lg hover:bg-indigo-500 transition-colors focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  aria-label="Send message"
                >
                  <Send className="h-3.5 w-3.5" />
                </button>
              </form>
            </aside>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
