"""Analytics Pydantic v2 schemas — request/response models for all endpoints."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.features.analytics.models import GoalStatus, HabitFrequency, TaskStatus

# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------


class WeeklyDataPoint(BaseModel):
    """A single day's productivity data for the weekly trend chart."""

    day: str  # "Mon", "Tue", …
    date: str  # ISO date "2025-07-04"
    tasks_completed: int = 0
    habit_score: float = 0.0  # 0.0–1.0 (fraction of habits completed that day)
    productivity: float = 0.0  # composite 0–100


class AIInsight(BaseModel):
    """A single rule-based AI recommendation card."""

    emoji: str
    title: str
    message: str
    category: Literal["productivity", "habits", "goals", "expenses", "knowledge"]
    severity: Literal["positive", "neutral", "warning"] = "neutral"


class CategoryAmount(BaseModel):
    """Expense amount per category."""

    category: str
    amount: float
    percentage: float


class MonthlyTrend(BaseModel):
    """Monthly spending or completion data point."""

    month: str  # "Jan", "Feb", …
    amount: float = 0.0
    tasks_completed: int = 0


class HabitHeatmapDay(BaseModel):
    """A single day cell in a habit completion heatmap."""

    date: str  # ISO date
    completed: bool
    day_label: str  # "Mon", "Tue", …


class GoalSummary(BaseModel):
    """Summarised goal for the goals analytics section."""

    id: uuid.UUID
    title: str
    progress_pct: float
    status: GoalStatus
    deadline: date | None = None
    category: str | None = None
    days_remaining: int | None = None


class HabitSummary(BaseModel):
    """Summarised habit for the habits analytics section."""

    id: uuid.UUID
    name: str
    current_streak: int
    longest_streak: int
    completion_rate_7d: float  # fraction of last 7 days completed
    frequency: HabitFrequency
    color: str
    heatmap: list[HabitHeatmapDay] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class DashboardResponse(BaseModel):
    """Full composite response for GET /analytics/dashboard."""

    # Scores (0–100)
    productivity_score: float
    habit_score: float
    goal_score: float
    overall_health_score: float

    # Task summary
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    completed_today: int
    task_completion_rate: float  # 0.0–1.0

    # Goal summary
    total_goals: int
    completed_goals: int
    active_goals: int

    # Habit summary
    habit_completion_rate: float  # 0.0–1.0
    longest_streak: int
    best_habit: str | None = None

    # Expense / budget summary
    monthly_budget: float
    monthly_spent: float
    remaining_budget: float
    budget_utilisation: float  # 0.0–1.0

    # Knowledge
    total_documents: int
    ready_documents: int
    total_memories: int

    # Trend data
    weekly_productivity: list[WeeklyDataPoint] = Field(default_factory=list)

    # AI insights
    ai_insights: list[AIInsight] = Field(default_factory=list)

    generated_at: datetime


# ---------------------------------------------------------------------------
# Task Analytics
# ---------------------------------------------------------------------------


class TaskAnalyticsResponse(BaseModel):
    """Detailed task breakdown for GET /analytics/tasks."""

    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    cancelled_tasks: int
    completed_today: int
    completed_this_week: int
    completed_this_month: int
    completion_rate: float  # 0.0–1.0
    average_completion_days: float | None = None
    by_priority: dict[str, int] = Field(default_factory=dict)  # high/medium/low counts
    by_category: dict[str, int] = Field(default_factory=dict)
    monthly_trend: list[MonthlyTrend] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Habit Analytics
# ---------------------------------------------------------------------------


class HabitAnalyticsResponse(BaseModel):
    """Detailed habit breakdown for GET /analytics/habits."""

    total_habits: int
    active_habits: int
    overall_completion_rate: float  # last 7 days
    longest_streak: int
    best_habit: str | None = None
    weakest_habit: str | None = None
    missed_today: int
    habits: list[HabitSummary] = Field(default_factory=list)
    weekly_heatmap: list[WeeklyDataPoint] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Goal Analytics
# ---------------------------------------------------------------------------


class GoalAnalyticsResponse(BaseModel):
    """Detailed goal breakdown for GET /analytics/goals."""

    total_goals: int
    completed_goals: int
    active_goals: int
    paused_goals: int
    quarterly_goals: int
    average_progress_pct: float
    closest_to_completion: GoalSummary | None = None
    goals: list[GoalSummary] = Field(default_factory=list)
    milestone_completion_rate: float  # alias for completion rate


# ---------------------------------------------------------------------------
# Expense Analytics
# ---------------------------------------------------------------------------


class ExpenseAnalyticsResponse(BaseModel):
    """Detailed expense breakdown for GET /analytics/expenses."""

    total_spending: float
    monthly_budget: float
    remaining_budget: float
    budget_utilisation: float  # 0.0–1.0
    average_daily_spending: float
    highest_category: str | None = None
    category_distribution: list[CategoryAmount] = Field(default_factory=list)
    monthly_trend: list[MonthlyTrend] = Field(default_factory=list)
    transaction_count: int


# ---------------------------------------------------------------------------
# Create Schemas (for seeding / future CRUD)
# ---------------------------------------------------------------------------


class AnalyticsTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: int = Field(2, ge=1, le=3)
    due_date: date | None = None
    category: str | None = None


class AnalyticsHabitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    frequency: HabitFrequency = HabitFrequency.DAILY
    color: str = "#6366f1"


class AnalyticsGoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    deadline: date | None = None
    category: str | None = None
    is_quarterly: bool = False


class AnalyticsExpenseCreate(BaseModel):
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    expense_date: date
    is_recurring: bool = False


class AnalyticsBudgetCreate(BaseModel):
    monthly_limit: float = Field(..., gt=0)
    year: int
    month: int = Field(..., ge=1, le=12)
