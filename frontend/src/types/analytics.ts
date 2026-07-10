/**
 * Analytics feature TypeScript types.
 * Mirrors the backend Pydantic schemas in app/features/analytics/schemas.py
 */

// -------------------------------------------------------------------------
// Shared building blocks
// -------------------------------------------------------------------------

export interface WeeklyDataPoint {
  day: string; // "Mon", "Tue", ...
  date: string; // ISO date "2025-07-04"
  tasks_completed: number;
  habit_score: number; // 0.0–1.0
  productivity: number; // 0–100
}

export interface AIInsight {
  emoji: string;
  title: string;
  message: string;
  category: "productivity" | "habits" | "goals" | "expenses" | "knowledge";
  severity: "positive" | "neutral" | "warning";
}

export interface CategoryAmount {
  category: string;
  amount: number;
  percentage: number;
}

export interface MonthlyTrend {
  month: string; // "Jan", "Feb", ...
  amount: number;
  tasks_completed: number;
}

export interface HabitHeatmapDay {
  date: string;
  completed: boolean;
  day_label: string;
}

export interface GoalSummary {
  id: string;
  title: string;
  progress_pct: number;
  status: "active" | "completed" | "paused" | "abandoned";
  deadline: string | null;
  category: string | null;
  days_remaining: number | null;
}

export interface HabitSummary {
  id: string;
  name: string;
  current_streak: number;
  longest_streak: number;
  completion_rate_7d: number;
  frequency: "daily" | "weekly";
  color: string;
  heatmap: HabitHeatmapDay[];
}

// -------------------------------------------------------------------------
// Dashboard
// -------------------------------------------------------------------------

export interface DashboardResponse {
  productivity_score: number;
  habit_score: number;
  goal_score: number;
  overall_health_score: number;

  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  overdue_tasks: number;
  completed_today: number;
  task_completion_rate: number;

  total_goals: number;
  completed_goals: number;
  active_goals: number;

  habit_completion_rate: number;
  longest_streak: number;
  best_habit: string | null;

  monthly_budget: number;
  monthly_spent: number;
  remaining_budget: number;
  budget_utilisation: number;

  total_documents: number;
  ready_documents: number;
  total_memories: number;

  weekly_productivity: WeeklyDataPoint[];
  ai_insights: AIInsight[];
  generated_at: string;
}

// -------------------------------------------------------------------------
// Task Analytics
// -------------------------------------------------------------------------

export interface TaskAnalyticsResponse {
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  overdue_tasks: number;
  cancelled_tasks: number;
  completed_today: number;
  completed_this_week: number;
  completed_this_month: number;
  completion_rate: number;
  average_completion_days: number | null;
  by_priority: Record<string, number>;
  by_category: Record<string, number>;
  monthly_trend: MonthlyTrend[];
}

// -------------------------------------------------------------------------
// Habit Analytics
// -------------------------------------------------------------------------

export interface HabitAnalyticsResponse {
  total_habits: number;
  active_habits: number;
  overall_completion_rate: number;
  longest_streak: number;
  best_habit: string | null;
  weakest_habit: string | null;
  missed_today: number;
  habits: HabitSummary[];
  weekly_heatmap: WeeklyDataPoint[];
}

// -------------------------------------------------------------------------
// Goal Analytics
// -------------------------------------------------------------------------

export interface GoalAnalyticsResponse {
  total_goals: number;
  completed_goals: number;
  active_goals: number;
  paused_goals: number;
  quarterly_goals: number;
  average_progress_pct: number;
  closest_to_completion: GoalSummary | null;
  goals: GoalSummary[];
  milestone_completion_rate: number;
}

// -------------------------------------------------------------------------
// Expense Analytics
// -------------------------------------------------------------------------

export interface ExpenseAnalyticsResponse {
  total_spending: number;
  monthly_budget: number;
  remaining_budget: number;
  budget_utilisation: number;
  average_daily_spending: number;
  highest_category: string | null;
  category_distribution: CategoryAmount[];
  monthly_trend: MonthlyTrend[];
  transaction_count: number;
}
