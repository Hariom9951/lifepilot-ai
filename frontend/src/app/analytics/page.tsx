"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/config/axios";
import {
  BarChart2,
  CheckCircle,
  AlertCircle,
  Clock,
  Target,
  TrendingUp,
  Zap,
  BookOpen,
  Brain,
  DollarSign,
  Calendar,
  Award,
  Flame,
} from "lucide-react";

import Navbar from "@/layouts/Navbar";
import LandingFooter from "@/features/landing/components/LandingFooter";
import { PageWrapper } from "@/layouts/PageWrapper";
import { SectionContainer } from "@/layouts/SectionContainer";
import { Card, StatCard } from "@/components/ui/card";
import ScoreRing from "@/features/analytics/components/ScoreRing";
import WeeklyAreaChart from "@/features/analytics/components/WeeklyAreaChart";
import MiniBarChart from "@/features/analytics/components/MiniBarChart";
import ExpensePieChart from "@/features/analytics/components/ExpensePieChart";
import HabitHeatmap from "@/features/analytics/components/HabitHeatmap";
import InsightCard from "@/features/analytics/components/InsightCard";
import {
  StatCardSkeleton,
  ChartSkeleton,
  ScoreRingSkeleton,
  InsightCardSkeleton,
  HabitRowSkeleton,
  GoalRowSkeleton,
} from "@/features/analytics/components/SkeletonLoader";

import type {
  DashboardResponse,
  HabitAnalyticsResponse,
  GoalAnalyticsResponse,
  ExpenseAnalyticsResponse,
} from "@/types/analytics";

// -------------------------------------------------------------------------
// API fetcher helpers
// -------------------------------------------------------------------------

const fetchDashboard = async (): Promise<DashboardResponse> => {
  const res = await apiClient.get("/analytics/dashboard");
  return res.data.data;
};

const fetchHabits = async (): Promise<HabitAnalyticsResponse> => {
  const res = await apiClient.get("/analytics/habits");
  return res.data.data;
};

const fetchGoals = async (): Promise<GoalAnalyticsResponse> => {
  const res = await apiClient.get("/analytics/goals");
  return res.data.data;
};

const fetchExpenses = async (): Promise<ExpenseAnalyticsResponse> => {
  const res = await apiClient.get("/analytics/expenses");
  return res.data.data;
};

// -------------------------------------------------------------------------
// Status badge helper
// -------------------------------------------------------------------------

function GoalStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    active: "bg-indigo-500/15 text-indigo-600 dark:text-indigo-300",
    completed: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-300",
    paused: "bg-amber-500/15 text-amber-600 dark:text-amber-300",
    abandoned: "bg-red-500/15 text-red-500",
  };
  return (
    <span
      className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wide ${
        styles[status] ?? styles.paused
      }`}
    >
      {status}
    </span>
  );
}

// -------------------------------------------------------------------------
// Section header
// -------------------------------------------------------------------------

function SectionHeader({
  icon: Icon,
  title,
  subtitle,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-500">
        <Icon className="h-4 w-4" />
      </div>
      <div>
        <h2 className="text-base font-black text-slate-900 dark:text-white">{title}</h2>
        {subtitle && (
          <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">{subtitle}</p>
        )}
      </div>
    </div>
  );
}

// -------------------------------------------------------------------------
// Main page
// -------------------------------------------------------------------------

export default function AnalyticsPage() {
  const { data: dashboard, isLoading: dashLoading } = useQuery({
    queryKey: ["analytics", "dashboard"],
    queryFn: fetchDashboard,
    staleTime: 60_000, // Mirror backend cache TTL
    retry: 1,
  });

  const { data: habits, isLoading: habitsLoading } = useQuery({
    queryKey: ["analytics", "habits"],
    queryFn: fetchHabits,
    staleTime: 60_000,
    retry: 1,
  });

  const { data: goals, isLoading: goalsLoading } = useQuery({
    queryKey: ["analytics", "goals"],
    queryFn: fetchGoals,
    staleTime: 60_000,
    retry: 1,
  });

  const { data: expenses, isLoading: expensesLoading } = useQuery({
    queryKey: ["analytics", "expenses"],
    queryFn: fetchExpenses,
    staleTime: 60_000,
    retry: 1,
  });

  return (
    <>
      <Navbar />
      <PageWrapper>
        <SectionContainer className="py-10 space-y-10 max-w-5xl mx-auto px-4">
          {/* ============================================================
              HERO HEADER
          ============================================================ */}
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="p-2 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-md shadow-indigo-500/20">
                  <BarChart2 className="h-5 w-5 text-white" />
                </div>
                <span className="text-[10px] font-bold font-mono uppercase tracking-widest text-indigo-500 dark:text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full">
                  Phase 8 · Analytics
                </span>
              </div>
              <h1 className="text-3xl font-black tracking-tight text-slate-900 dark:text-white">
                Holistic Dashboard
              </h1>
              <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">
                Aggregated insights across tasks, habits, goals and expenses
              </p>
            </div>

            {dashboard && (
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-white/60 dark:bg-slate-900/30 backdrop-blur-sm">
                <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400">
                  Live · cached 60s
                </span>
              </div>
            )}
          </div>

          {/* ============================================================
              SCORE RINGS
          ============================================================ */}
          <Card className="p-6 md:p-8">
            <h2 className="text-sm font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-6">
              Performance Scores
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 place-items-center">
              {dashLoading ? (
                Array.from({ length: 4 }).map((_, i) => <ScoreRingSkeleton key={i} size={110} />)
              ) : (
                <>
                  <ScoreRing
                    score={dashboard?.productivity_score ?? 0}
                    size={110}
                    label="Productivity"
                    sublabel="Tasks + Goals"
                    colorClass="stroke-indigo-500"
                  />
                  <ScoreRing
                    score={dashboard?.habit_score ?? 0}
                    size={110}
                    label="Habit Health"
                    sublabel="7-day avg"
                    colorClass="stroke-violet-500"
                  />
                  <ScoreRing
                    score={dashboard?.goal_score ?? 0}
                    size={110}
                    label="Goal Progress"
                    sublabel="Active goals"
                    colorClass="stroke-emerald-500"
                  />
                  <ScoreRing
                    score={dashboard?.overall_health_score ?? 0}
                    size={110}
                    label="Overall Health"
                    sublabel="Composite"
                    colorClass="stroke-amber-500"
                  />
                </>
              )}
            </div>
          </Card>

          {/* ============================================================
              STAT CARDS
          ============================================================ */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {dashLoading ? (
              Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)
            ) : (
              <>
                <StatCard
                  id="stat-tasks-completed"
                  title="Tasks Done"
                  value={dashboard?.completed_tasks ?? 0}
                  icon={CheckCircle}
                />
                <StatCard
                  id="stat-tasks-overdue"
                  title="Overdue"
                  value={dashboard?.overdue_tasks ?? 0}
                  icon={AlertCircle}
                />
                <StatCard
                  id="stat-streak"
                  title="Longest Streak"
                  value={`${dashboard?.longest_streak ?? 0}d`}
                  icon={Flame}
                />
                <StatCard
                  id="stat-goals-active"
                  title="Active Goals"
                  value={dashboard?.active_goals ?? 0}
                  icon={Target}
                />
              </>
            )}
          </div>

          {/* ============================================================
              WEEKLY CHARTS
          ============================================================ */}
          <div className="grid md:grid-cols-2 gap-6">
            {dashLoading ? (
              <>
                <ChartSkeleton />
                <ChartSkeleton />
              </>
            ) : (
              <>
                <Card className="p-5">
                  <SectionHeader
                    icon={TrendingUp}
                    title="Weekly Productivity"
                    subtitle="7-day rolling composite score"
                  />
                  <WeeklyAreaChart data={dashboard?.weekly_productivity ?? []} />
                </Card>
                <Card className="p-5">
                  <SectionHeader
                    icon={CheckCircle}
                    title="Daily Task Completions"
                    subtitle="Tasks completed per day"
                  />
                  <MiniBarChart data={dashboard?.weekly_productivity ?? []} />
                </Card>
              </>
            )}
          </div>

          {/* ============================================================
              HABITS SECTION
          ============================================================ */}
          <Card className="p-5 space-y-4">
            <SectionHeader
              icon={Flame}
              title="Habit Tracker"
              subtitle="7-day completion history per habit"
            />

            {/* Summary row */}
            {!habitsLoading && habits && (
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="rounded-xl border border-violet-500/20 bg-violet-50/40 dark:bg-violet-950/15 p-3 text-center">
                  <p className="text-xl font-black text-violet-600 dark:text-violet-300">
                    {habits.active_habits}
                  </p>
                  <p className="text-[10px] text-slate-400 uppercase tracking-wide">Active</p>
                </div>
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-50/40 dark:bg-emerald-950/15 p-3 text-center">
                  <p className="text-xl font-black text-emerald-600 dark:text-emerald-300">
                    {Math.round(habits.overall_completion_rate * 100)}%
                  </p>
                  <p className="text-[10px] text-slate-400 uppercase tracking-wide">7-day Rate</p>
                </div>
                <div className="rounded-xl border border-amber-500/20 bg-amber-50/40 dark:bg-amber-950/15 p-3 text-center">
                  <p className="text-xl font-black text-amber-600 dark:text-amber-300">
                    🔥{habits.longest_streak}d
                  </p>
                  <p className="text-[10px] text-slate-400 uppercase tracking-wide">Best Streak</p>
                </div>
              </div>
            )}

            {/* Habit heatmap rows */}
            <div className="space-y-3">
              {habitsLoading ? (
                Array.from({ length: 3 }).map((_, i) => <HabitRowSkeleton key={i} />)
              ) : habits?.habits.length === 0 ? (
                <div className="text-center py-8 text-sm text-slate-400 dark:text-slate-600">
                  No habits tracked yet. Add habits to see completion heatmaps.
                </div>
              ) : (
                habits?.habits.map((habit) => (
                  <HabitHeatmap
                    key={habit.id}
                    name={habit.name}
                    color={habit.color}
                    heatmap={habit.heatmap}
                    currentStreak={habit.current_streak}
                    completionRate={habit.completion_rate_7d}
                  />
                ))
              )}
            </div>
          </Card>

          {/* ============================================================
              GOALS SECTION
          ============================================================ */}
          <Card className="p-5 space-y-4">
            <SectionHeader
              icon={Target}
              title="Goal Progress"
              subtitle="Milestones and completion status"
            />

            {/* Stats row */}
            {!goalsLoading && goals && (
              <div className="flex flex-wrap gap-3 mb-4">
                <span className="flex items-center gap-1.5 text-xs font-bold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-900 px-3 py-1.5 rounded-lg">
                  <Award className="h-3.5 w-3.5 text-emerald-500" />
                  {goals.completed_goals} Completed
                </span>
                <span className="flex items-center gap-1.5 text-xs font-bold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-900 px-3 py-1.5 rounded-lg">
                  <Zap className="h-3.5 w-3.5 text-indigo-400" />
                  {goals.active_goals} Active
                </span>
                <span className="flex items-center gap-1.5 text-xs font-bold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-900 px-3 py-1.5 rounded-lg">
                  <BarChart2 className="h-3.5 w-3.5 text-violet-400" />
                  Avg {goals.average_progress_pct.toFixed(0)}% complete
                </span>
              </div>
            )}

            {/* Goal progress bars */}
            <div className="space-y-4">
              {goalsLoading ? (
                Array.from({ length: 3 }).map((_, i) => <GoalRowSkeleton key={i} />)
              ) : goals?.goals.length === 0 ? (
                <div className="text-center py-8 text-sm text-slate-400 dark:text-slate-600">
                  No goals set yet. Add goals to track your progress here.
                </div>
              ) : (
                goals?.goals.map((goal) => (
                  <div key={goal.id} className="space-y-1.5">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 truncate">
                          {goal.title}
                        </span>
                        <GoalStatusBadge status={goal.status} />
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {goal.days_remaining !== null && (
                          <span className="flex items-center gap-1 text-[10px] text-slate-400">
                            <Calendar className="h-3 w-3" />
                            {goal.days_remaining}d left
                          </span>
                        )}
                        <span className="text-xs font-black text-slate-900 dark:text-white font-mono">
                          {goal.progress_pct.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-100 dark:bg-slate-800/60 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-700"
                        style={{ width: `${Math.min(goal.progress_pct, 100)}%` }}
                      />
                    </div>
                    {goal.category && <p className="text-[10px] text-slate-400">{goal.category}</p>}
                  </div>
                ))
              )}
            </div>
          </Card>

          {/* ============================================================
              EXPENSES SECTION
          ============================================================ */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card className="p-5">
              <SectionHeader
                icon={DollarSign}
                title="Expense Distribution"
                subtitle="Current month by category"
              />
              {expensesLoading ? (
                <div className="h-52 rounded-xl bg-slate-100 dark:bg-slate-800/50 animate-pulse" />
              ) : (
                <ExpensePieChart data={expenses?.category_distribution ?? []} />
              )}
            </Card>

            <Card className="p-5">
              <SectionHeader
                icon={TrendingUp}
                title="Budget Overview"
                subtitle="Monthly spending vs budget"
              />
              {expensesLoading ? (
                <div className="space-y-4 animate-pulse">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="h-4 w-full rounded bg-slate-200 dark:bg-slate-800" />
                  ))}
                </div>
              ) : (
                <div className="space-y-5 mt-2">
                  {/* Budget bar */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400">
                      <span className="font-semibold">Budget utilisation</span>
                      <span className="font-black text-slate-700 dark:text-slate-200">
                        {Math.round((expenses?.budget_utilisation ?? 0) * 100)}%
                      </span>
                    </div>
                    <div className="h-3 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${
                          (expenses?.budget_utilisation ?? 0) > 0.9
                            ? "bg-red-500"
                            : (expenses?.budget_utilisation ?? 0) > 0.7
                              ? "bg-amber-500"
                              : "bg-emerald-500"
                        }`}
                        style={{
                          width: `${Math.min((expenses?.budget_utilisation ?? 0) * 100, 100)}%`,
                        }}
                      />
                    </div>
                  </div>

                  {/* Key numbers */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-xl border border-slate-200/40 dark:border-slate-800/40 bg-slate-50 dark:bg-slate-900/30 p-3">
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                        Spent
                      </p>
                      <p className="text-lg font-black text-slate-900 dark:text-white mt-1">
                        ${expenses?.total_spending.toFixed(2) ?? "0.00"}
                      </p>
                    </div>
                    <div className="rounded-xl border border-slate-200/40 dark:border-slate-800/40 bg-slate-50 dark:bg-slate-900/30 p-3">
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                        Remaining
                      </p>
                      <p
                        className={`text-lg font-black mt-1 ${
                          (expenses?.remaining_budget ?? 0) > 0
                            ? "text-emerald-600 dark:text-emerald-400"
                            : "text-red-500"
                        }`}
                      >
                        ${expenses?.remaining_budget.toFixed(2) ?? "0.00"}
                      </p>
                    </div>
                    <div className="rounded-xl border border-slate-200/40 dark:border-slate-800/40 bg-slate-50 dark:bg-slate-900/30 p-3">
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                        Daily Avg
                      </p>
                      <p className="text-lg font-black text-slate-900 dark:text-white mt-1">
                        ${expenses?.average_daily_spending.toFixed(2) ?? "0.00"}
                      </p>
                    </div>
                    <div className="rounded-xl border border-slate-200/40 dark:border-slate-800/40 bg-slate-50 dark:bg-slate-900/30 p-3">
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                        Transactions
                      </p>
                      <p className="text-lg font-black text-slate-900 dark:text-white mt-1">
                        {expenses?.transaction_count ?? 0}
                      </p>
                    </div>
                  </div>

                  {expenses?.highest_category && (
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      📊 Highest category:{" "}
                      <span className="font-bold text-slate-700 dark:text-slate-200">
                        {expenses.highest_category}
                      </span>
                    </p>
                  )}
                </div>
              )}
            </Card>
          </div>

          {/* ============================================================
              KNOWLEDGE & MEMORY SUMMARY
          ============================================================ */}
          {!dashLoading && dashboard && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="p-5 flex items-center gap-3">
                <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-500">
                  <BookOpen className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-xl font-black text-slate-900 dark:text-white">
                    {dashboard.total_documents}
                  </p>
                  <p className="text-[10px] text-slate-400">Documents</p>
                </div>
              </Card>
              <Card className="p-5 flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
                  <CheckCircle className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-xl font-black text-slate-900 dark:text-white">
                    {dashboard.ready_documents}
                  </p>
                  <p className="text-[10px] text-slate-400">Indexed</p>
                </div>
              </Card>
              <Card className="p-5 flex items-center gap-3">
                <div className="p-2 rounded-lg bg-violet-500/10 text-violet-500">
                  <Brain className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-xl font-black text-slate-900 dark:text-white">
                    {dashboard.total_memories}
                  </p>
                  <p className="text-[10px] text-slate-400">Memories</p>
                </div>
              </Card>
              <Card className="p-5 flex items-center gap-3">
                <div className="p-2 rounded-lg bg-amber-500/10 text-amber-500">
                  <Clock className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-xl font-black text-slate-900 dark:text-white">
                    {dashboard.completed_today}
                  </p>
                  <p className="text-[10px] text-slate-400">Done Today</p>
                </div>
              </Card>
            </div>
          )}

          {/* ============================================================
              AI INSIGHTS GRID
          ============================================================ */}
          <div>
            <div className="flex items-center gap-3 mb-5">
              <div className="p-2 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/20 text-indigo-500">
                <Zap className="h-4 w-4" />
              </div>
              <div>
                <h2 className="text-base font-black text-slate-900 dark:text-white">
                  AI Insight Engine
                </h2>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Rule-based recommendations · no LLM required
                </p>
              </div>
              <span className="ml-auto text-[9px] font-bold font-mono uppercase tracking-widest text-violet-500 bg-violet-500/10 px-2 py-0.5 rounded-full border border-violet-500/20">
                Pure Analytics
              </span>
            </div>

            {dashLoading ? (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <InsightCardSkeleton key={i} />
                ))}
              </div>
            ) : dashboard?.ai_insights.length === 0 ? (
              <Card className="p-8 text-center">
                <p className="text-slate-400 text-sm">
                  Add tasks, habits, goals or expenses to generate AI insights.
                </p>
              </Card>
            ) : (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {dashboard?.ai_insights.map((insight, i) => (
                  <InsightCard key={i} insight={insight} index={i} />
                ))}
              </div>
            )}
          </div>

          {/* Footer spacer */}
          <div className="pb-4" />
        </SectionContainer>
      </PageWrapper>
      <LandingFooter />
    </>
  );
}
