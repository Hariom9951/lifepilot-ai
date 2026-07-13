"""Analytics service — business logic, scoring formulas and AI insight engine.

Architecture:
- All public methods are class-methods on AnalyticsService.
- Redis is used as an optional cache layer on the expensive dashboard query.
- The rule-based AI engine generates ≥5 insights without any LLM dependency.
- Scoring formulas are documented inline for transparency.
"""

import json
import logging
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.redis import redis_manager
from app.features.analytics.models import GoalStatus
from app.features.analytics.repository import AnalyticsRepository
from app.features.analytics.schemas import (
    AIInsight,
    CategoryAmount,
    DashboardResponse,
    ExpenseAnalyticsResponse,
    GoalAnalyticsResponse,
    GoalSummary,
    HabitAnalyticsResponse,
    HabitHeatmapDay,
    HabitSummary,
    MonthlyTrend,
    TaskAnalyticsResponse,
    WeeklyDataPoint,
)

logger = logging.getLogger("app.analytics.service")

# Redis cache TTL for dashboard queries (seconds)
DASHBOARD_CACHE_TTL = 60

# Day abbreviations for chart labels
DAY_ABBREVS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_ABBREVS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


class AnalyticsService:
    """
    Service layer for all analytics computations.

    Scoring formulas
    ----------------
    productivity_score = 40% task_score + 35% habit_score + 25% goal_score
      where task_score  = completed / max(total, 1) * 100
            habit_score = overall 7-day habit completion rate * 100
            goal_score  = completed_goals / max(total_goals, 1) * 100

    overall_health_score = (productivity_score + habit_score + goal_score) / 3
    """

    # ------------------------------------------------------------------
    # Public API: main composites
    # ------------------------------------------------------------------

    @classmethod
    async def get_dashboard(
        cls, db: AsyncSession, user_id: uuid.UUID
    ) -> DashboardResponse:
        """
        Compute and return the full analytics dashboard payload.
        Result is cached in Redis for DASHBOARD_CACHE_TTL seconds when
        Redis is configured; otherwise computed fresh on every call.
        """
        cache_key = f"analytics:dashboard:{user_id}"

        # Try Redis cache first (skipped when Redis is not configured)
        if redis_manager.is_configured:
            try:
                redis = redis_manager.get_client()
                if redis is not None:
                    cached = await redis.get(cache_key)
                    if cached:
                        data = json.loads(cached)
                        return DashboardResponse(**data)
            except Exception as exc:
                logger.warning("Redis cache read failed — computing fresh: %s", exc)

        result = await cls._compute_dashboard(db, user_id)

        # Write to cache (skipped when Redis is not configured)
        if redis_manager.is_configured:
            try:
                redis = redis_manager.get_client()
                if redis is not None:
                    await redis.setex(
                        cache_key,
                        DASHBOARD_CACHE_TTL,
                        result.model_dump_json(),
                    )
            except Exception as exc:
                logger.warning("Redis cache write failed: %s", exc)

        return result

    @classmethod
    async def get_task_analytics(
        cls, db: AsyncSession, user_id: uuid.UUID
    ) -> TaskAnalyticsResponse:
        counts = await AnalyticsRepository.get_task_counts(db, user_id)
        by_priority = await AnalyticsRepository.get_tasks_by_priority(db, user_id)
        by_category = await AnalyticsRepository.get_tasks_by_category(db, user_id)
        raw_monthly = await AnalyticsRepository.get_tasks_completed_monthly(db, user_id)

        total = counts["total"]
        completed = counts["completed"]
        rate = completed / total if total else 0.0

        monthly_trend = cls._build_monthly_task_trend(raw_monthly)

        return TaskAnalyticsResponse(
            total_tasks=total,
            completed_tasks=completed,
            pending_tasks=counts["pending"],
            overdue_tasks=counts["overdue"],
            cancelled_tasks=counts["cancelled"],
            completed_today=counts["completed_today"],
            completed_this_week=counts["completed_this_week"],
            completed_this_month=counts["completed_this_month"],
            completion_rate=round(rate, 4),
            by_priority=by_priority,
            by_category=by_category,
            monthly_trend=monthly_trend,
        )

    @classmethod
    async def get_habit_analytics(
        cls, db: AsyncSession, user_id: uuid.UUID
    ) -> HabitAnalyticsResponse:
        habits = await AnalyticsRepository.get_all_habits(db, user_id)
        counts = await AnalyticsRepository.get_habit_counts(db, user_id)
        today = datetime.now(UTC).date()

        habit_summaries = [cls._build_habit_summary(h, today) for h in habits]

        # Overall 7-day completion rate
        if habit_summaries:
            overall_rate = sum(h.completion_rate_7d for h in habit_summaries) / len(
                habit_summaries
            )
        else:
            overall_rate = 0.0

        longest = max((h.longest_streak for h in habit_summaries), default=0)
        best = max(habit_summaries, key=lambda h: h.current_streak, default=None)
        weakest = min(habit_summaries, key=lambda h: h.completion_rate_7d, default=None)

        # Missed today = active habits with no completion today
        today_str = today.isoformat()
        missed_today = sum(1 for h in habits if today_str not in (h.completions or []))

        weekly_heatmap = cls._build_weekly_habit_heatmap(habits, today)

        return HabitAnalyticsResponse(
            total_habits=counts["total"],
            active_habits=counts["active"],
            overall_completion_rate=round(overall_rate, 4),
            longest_streak=longest,
            best_habit=best.name if best else None,
            weakest_habit=weakest.name if weakest else None,
            missed_today=missed_today,
            habits=habit_summaries,
            weekly_heatmap=weekly_heatmap,
        )

    @classmethod
    async def get_goal_analytics(
        cls, db: AsyncSession, user_id: uuid.UUID
    ) -> GoalAnalyticsResponse:
        counts = await AnalyticsRepository.get_goal_counts(db, user_id)
        goals = await AnalyticsRepository.get_all_goals(db, user_id)
        today = datetime.now(UTC).date()

        goal_summaries = [cls._build_goal_summary(g, today) for g in goals]

        # Closest active goal to completion
        active_summaries = [g for g in goal_summaries if g.status == GoalStatus.ACTIVE]
        closest = max(active_summaries, key=lambda g: g.progress_pct, default=None)

        total = counts["total"]
        completed = counts["completed"]
        milestone_rate = completed / total if total else 0.0

        return GoalAnalyticsResponse(
            total_goals=total,
            completed_goals=completed,
            active_goals=counts["active"],
            paused_goals=counts["paused"],
            quarterly_goals=counts["quarterly"],
            average_progress_pct=round(counts["avg_progress"], 2),
            closest_to_completion=closest,
            goals=goal_summaries,
            milestone_completion_rate=round(milestone_rate, 4),
        )

    @classmethod
    async def get_expense_analytics(
        cls, db: AsyncSession, user_id: uuid.UUID
    ) -> ExpenseAnalyticsResponse:
        now = datetime.now(UTC)
        year, month = now.year, now.month
        days_in_month = (
            (date(year, month % 12 + 1, 1) - timedelta(days=1)).day
            if month < 12
            else 31
        )

        totals = await AnalyticsRepository.get_expense_totals(db, user_id, year, month)
        cat_rows = await AnalyticsRepository.get_expense_by_category(
            db, user_id, year, month
        )
        monthly_raw = await AnalyticsRepository.get_monthly_spending_trend(db, user_id)
        budget = await AnalyticsRepository.get_monthly_budget(db, user_id, year, month)

        total_spent = totals["total"]
        remaining = max(budget - total_spent, 0.0)
        utilisation = (total_spent / budget) if budget else 0.0
        avg_daily = total_spent / max(days_in_month, 1)

        category_dist = cls._build_category_distribution(cat_rows, total_spent)
        monthly_trend = cls._build_monthly_expense_trend(monthly_raw)
        highest_cat = cat_rows[0]["category"] if cat_rows else None

        return ExpenseAnalyticsResponse(
            total_spending=round(total_spent, 2),
            monthly_budget=round(budget, 2),
            remaining_budget=round(remaining, 2),
            budget_utilisation=round(min(utilisation, 1.0), 4),
            average_daily_spending=round(avg_daily, 2),
            highest_category=highest_cat,
            category_distribution=category_dist,
            monthly_trend=monthly_trend,
            transaction_count=totals["count"],
        )

    # ------------------------------------------------------------------
    # Internal: full dashboard computation
    # ------------------------------------------------------------------

    @classmethod
    async def _compute_dashboard(
        cls, db: AsyncSession, user_id: uuid.UUID
    ) -> DashboardResponse:
        now = datetime.now(UTC)
        year, month = now.year, now.month
        today = now.date()

        # Gather all data in parallel-safe async calls
        task_counts = await AnalyticsRepository.get_task_counts(db, user_id)
        goal_counts = await AnalyticsRepository.get_goal_counts(db, user_id)
        expense_totals = await AnalyticsRepository.get_expense_totals(
            db, user_id, year, month
        )
        expense_cats = await AnalyticsRepository.get_expense_by_category(
            db, user_id, year, month
        )
        budget = await AnalyticsRepository.get_monthly_budget(db, user_id, year, month)
        habits = await AnalyticsRepository.get_all_habits(db, user_id)
        doc_stats = await AnalyticsRepository.get_document_stats(db, user_id)
        memory_count = await AnalyticsRepository.get_memory_count(db, user_id)
        tasks_per_day = await AnalyticsRepository.get_tasks_completed_per_day(
            db, user_id
        )

        # Scores
        task_score = cls._compute_task_score(task_counts)
        habit_score_val = cls._compute_habit_score(habits, today)
        goal_score = cls._compute_goal_score(goal_counts)
        productivity_score = round(
            0.40 * task_score + 0.35 * habit_score_val + 0.25 * goal_score, 1
        )
        overall_health_score = round((task_score + habit_score_val + goal_score) / 3, 1)

        # Habit rate
        habit_summaries = [cls._build_habit_summary(h, today) for h in habits]
        habit_rate = (
            sum(h.completion_rate_7d for h in habit_summaries) / len(habit_summaries)
            if habit_summaries
            else 0.0
        )
        longest_streak = max((h.longest_streak for h in habit_summaries), default=0)
        best_habit_name = (
            max(habit_summaries, key=lambda h: h.current_streak).name
            if habit_summaries
            else None
        )

        # Expense
        total_spent = expense_totals["total"]
        remaining_budget = max(budget - total_spent, 0.0)
        budget_utilisation = (total_spent / budget) if budget else 0.0
        highest_cat = expense_cats[0]["category"] if expense_cats else None

        # Weekly productivity chart
        weekly_productivity = cls._build_weekly_productivity(
            tasks_per_day, habits, today
        )

        # AI Insights
        ai_insights = cls._generate_insights(
            task_counts=task_counts,
            habit_rate=habit_rate,
            longest_streak=longest_streak,
            best_habit=best_habit_name,
            goal_counts=goal_counts,
            budget_utilisation=budget_utilisation,
            total_spent=total_spent,
            highest_cat=highest_cat,
            doc_stats=doc_stats,
            memory_count=memory_count,
            productivity_score=productivity_score,
        )

        return DashboardResponse(
            productivity_score=productivity_score,
            habit_score=round(habit_score_val, 1),
            goal_score=round(goal_score, 1),
            overall_health_score=overall_health_score,
            total_tasks=task_counts["total"],
            completed_tasks=task_counts["completed"],
            pending_tasks=task_counts["pending"],
            overdue_tasks=task_counts["overdue"],
            completed_today=task_counts["completed_today"],
            task_completion_rate=round(
                task_counts["completed"] / max(task_counts["total"], 1), 4
            ),
            total_goals=goal_counts["total"],
            completed_goals=goal_counts["completed"],
            active_goals=goal_counts["active"],
            habit_completion_rate=round(habit_rate, 4),
            longest_streak=longest_streak,
            best_habit=best_habit_name,
            monthly_budget=round(budget, 2),
            monthly_spent=round(total_spent, 2),
            remaining_budget=round(remaining_budget, 2),
            budget_utilisation=round(min(budget_utilisation, 1.0), 4),
            total_documents=doc_stats["total"],
            ready_documents=doc_stats["ready"],
            total_memories=memory_count,
            weekly_productivity=weekly_productivity,
            ai_insights=ai_insights,
            generated_at=now,
        )

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_task_score(counts: dict[str, int]) -> float:
        total = counts["total"]
        if not total:
            return 0.0
        completed = counts["completed"]
        # Penalise overdue tasks by half their weight
        overdue_penalty = counts["overdue"] * 0.5
        adjusted = max(completed - overdue_penalty, 0)
        return min(adjusted / total * 100, 100.0)

    @staticmethod
    def _compute_habit_score(habits: list[Any], today: date) -> float:
        if not habits:
            return 0.0
        rates = []
        for habit in habits:
            completions: list[str] = habit.completions or []
            # Last 7 days completion rate
            days = [(today - timedelta(days=i)).isoformat() for i in range(7)]
            done = sum(1 for d in days if d in completions)
            rates.append(done / 7)
        return min(sum(rates) / len(rates) * 100, 100.0)

    @staticmethod
    def _compute_goal_score(counts: dict[str, Any]) -> float:
        total = counts["total"]
        if not total:
            return 0.0
        completed = counts["completed"]
        avg_progress = counts["avg_progress"]
        # Weight: 60% completion rate + 40% average progress
        completion_part = (completed / total) * 60
        progress_part = (avg_progress / 100) * 40
        return min(completion_part + progress_part, 100.0)

    # ------------------------------------------------------------------
    # Chart-building helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_weekly_productivity(
        tasks_per_day: dict[str, int],
        habits: list[Any],
        today: date,
    ) -> list[WeeklyDataPoint]:
        """Build a 7-day rolling window productivity chart."""
        points: list[WeeklyDataPoint] = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_str = day.isoformat()
            day_label = DAY_ABBREVS[day.weekday()]

            tasks_done = tasks_per_day.get(day_str, 0)
            habit_completions = sum(
                1 for h in habits if day_str in (h.completions or [])
            )
            habit_score = habit_completions / len(habits) if habits else 0.0
            productivity = min((tasks_done * 10 + habit_score * 50), 100.0)

            points.append(
                WeeklyDataPoint(
                    day=day_label,
                    date=day_str,
                    tasks_completed=tasks_done,
                    habit_score=round(habit_score, 3),
                    productivity=round(productivity, 1),
                )
            )
        return points

    @staticmethod
    def _build_monthly_task_trend(
        raw: list[dict[str, Any]],
    ) -> list[MonthlyTrend]:
        return [
            MonthlyTrend(
                month=MONTH_ABBREVS[int(r["month"].split("-")[1]) - 1],
                tasks_completed=r["count"],
            )
            for r in raw
            if r.get("month")
        ]

    @staticmethod
    def _build_monthly_expense_trend(
        raw: list[dict[str, Any]],
    ) -> list[MonthlyTrend]:
        return [
            MonthlyTrend(
                month=MONTH_ABBREVS[int(r["month"].split("-")[1]) - 1],
                amount=r["amount"],
            )
            for r in raw
            if r.get("month")
        ]

    @staticmethod
    def _build_category_distribution(
        cat_rows: list[dict[str, Any]],
        total: float,
    ) -> list[CategoryAmount]:
        if not total:
            return [
                CategoryAmount(
                    category=r["category"], amount=r["amount"], percentage=0.0
                )
                for r in cat_rows
            ]
        return [
            CategoryAmount(
                category=r["category"],
                amount=round(r["amount"], 2),
                percentage=round(r["amount"] / total * 100, 1),
            )
            for r in cat_rows
        ]

    @staticmethod
    def _build_habit_summary(habit: Any, today: date) -> HabitSummary:
        completions: list[str] = habit.completions or []
        last_7 = [(today - timedelta(days=i)).isoformat() for i in range(7)]
        done_7 = sum(1 for d in last_7 if d in completions)
        rate_7d = done_7 / 7

        heatmap = [
            HabitHeatmapDay(
                date=d,
                completed=d in completions,
                day_label=DAY_ABBREVS[(today - timedelta(days=6 - i)).weekday()],
            )
            for i, d in enumerate(reversed(last_7))
        ]

        return HabitSummary(
            id=habit.id,
            name=habit.name,
            current_streak=habit.current_streak,
            longest_streak=habit.longest_streak,
            completion_rate_7d=round(rate_7d, 3),
            frequency=habit.frequency,
            color=habit.color,
            heatmap=heatmap,
        )

    @staticmethod
    def _build_goal_summary(goal: Any, today: date) -> GoalSummary:
        days_remaining: int | None = None
        if goal.deadline:
            delta = (goal.deadline - today).days
            days_remaining = max(delta, 0)

        return GoalSummary(
            id=goal.id,
            title=goal.title,
            progress_pct=round(goal.progress_pct, 1),
            status=goal.status,
            deadline=goal.deadline,
            category=goal.category,
            days_remaining=days_remaining,
        )

    @staticmethod
    def _build_weekly_habit_heatmap(
        habits: list[Any], today: date
    ) -> list[WeeklyDataPoint]:
        """Aggregate habit completion into a weekly data point series."""
        points: list[WeeklyDataPoint] = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_str = day.isoformat()
            done = sum(1 for h in habits if day_str in (h.completions or []))
            habit_score = done / len(habits) if habits else 0.0
            points.append(
                WeeklyDataPoint(
                    day=DAY_ABBREVS[day.weekday()],
                    date=day_str,
                    tasks_completed=0,
                    habit_score=round(habit_score, 3),
                    productivity=round(habit_score * 100, 1),
                )
            )
        return points

    # ------------------------------------------------------------------
    # Rule-based AI Insight Engine
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_insights(
        task_counts: dict[str, int],
        habit_rate: float,
        longest_streak: int,
        best_habit: str | None,
        goal_counts: dict[str, Any],
        budget_utilisation: float,
        total_spent: float,
        highest_cat: str | None,
        doc_stats: dict[str, int],
        memory_count: int,
        productivity_score: float,
    ) -> list[AIInsight]:
        """
        Generate contextual, rule-based insights from aggregated metrics.
        Returns between 3 and 12 AIInsight objects (at least one per domain).
        """
        insights: list[AIInsight] = []
        total_tasks = task_counts["total"]
        completed = task_counts["completed"]
        overdue = task_counts["overdue"]
        pending = task_counts["pending"]

        # --- Productivity ---
        if productivity_score >= 80:
            insights.append(
                AIInsight(
                    emoji="⚡",
                    title="Excellent Productivity",
                    message=f"Your productivity score is {productivity_score:.0f}/100 — you're performing in the top tier.",
                    category="productivity",
                    severity="positive",
                )
            )
        elif productivity_score >= 50:
            insights.append(
                AIInsight(
                    emoji="📈",
                    title="Good Progress",
                    message=f"Productivity at {productivity_score:.0f}/100. Completing overdue tasks will push you higher.",
                    category="productivity",
                    severity="neutral",
                )
            )
        else:
            insights.append(
                AIInsight(
                    emoji="🎯",
                    title="Productivity Needs Attention",
                    message="Your score is below 50. Start with your highest-priority pending task today.",
                    category="productivity",
                    severity="warning",
                )
            )

        # --- Tasks ---
        if total_tasks and completed / max(total_tasks, 1) >= 0.8:
            rate_pct = round(completed / total_tasks * 100)
            insights.append(
                AIInsight(
                    emoji="✅",
                    title="Task Completion Excellent",
                    message=f"You've completed {rate_pct}% of your tasks — outstanding consistency.",
                    category="productivity",
                    severity="positive",
                )
            )

        if overdue > 0:
            insights.append(
                AIInsight(
                    emoji="⏰",
                    title=f"{overdue} Task{'s' if overdue > 1 else ''} Overdue",
                    message=f"Reschedule or complete {overdue} overdue task{'s' if overdue > 1 else ''} to protect your productivity score.",
                    category="productivity",
                    severity="warning",
                )
            )

        if pending > 5:
            insights.append(
                AIInsight(
                    emoji="📋",
                    title="Task Backlog Growing",
                    message=f"You have {pending} pending tasks. Consider blocking 90-minute deep-work sessions.",
                    category="productivity",
                    severity="neutral",
                )
            )

        # --- Habits ---
        if longest_streak >= 14:
            insights.append(
                AIInsight(
                    emoji="🔥",
                    title=f"{longest_streak}-Day Streak!",
                    message=f"Your {'habit' if not best_habit else best_habit} streak has reached {longest_streak} days — incredible discipline.",
                    category="habits",
                    severity="positive",
                )
            )
        elif longest_streak >= 7:
            insights.append(
                AIInsight(
                    emoji="🔥",
                    title=f"{longest_streak}-Day Streak",
                    message=f"{'Habit' if not best_habit else best_habit} streak at {longest_streak} days — keep going to hit two weeks!",
                    category="habits",
                    severity="positive",
                )
            )

        if habit_rate >= 0.9:
            insights.append(
                AIInsight(
                    emoji="🌟",
                    title="Perfect Habit Consistency",
                    message="You completed 90%+ of your habits this week. Your discipline is exceptional.",
                    category="habits",
                    severity="positive",
                )
            )
        elif habit_rate < 0.4 and habit_rate > 0:
            insights.append(
                AIInsight(
                    emoji="⚡",
                    title="Habit Consistency Low",
                    message=f"Only {round(habit_rate * 100)}% habit completion this week. Pick your top 2 habits and protect them.",
                    category="habits",
                    severity="warning",
                )
            )

        # --- Goals ---
        active_goals = goal_counts["active"]
        completed_goals = goal_counts["completed"]

        if completed_goals > 0:
            insights.append(
                AIInsight(
                    emoji="🏆",
                    title=f"{completed_goals} Goal{'s' if completed_goals > 1 else ''} Completed",
                    message=f"You've achieved {completed_goals} goal{'s' if completed_goals > 1 else ''}. Review your next targets and set new milestones.",
                    category="goals",
                    severity="positive",
                )
            )

        if active_goals > 0:
            avg = goal_counts["avg_progress"]
            insights.append(
                AIInsight(
                    emoji="🎯",
                    title=f"{active_goals} Active Goal{'s' if active_goals > 1 else ''}",
                    message=f"Average progress: {avg:.0f}%. Schedule weekly reviews to maintain momentum.",
                    category="goals",
                    severity="neutral",
                )
            )

        # --- Expenses ---
        if budget_utilisation >= 0.9 and total_spent > 0:
            insights.append(
                AIInsight(
                    emoji="💰",
                    title="Budget Almost Exhausted",
                    message=f"Spending is at {budget_utilisation * 100:.0f}% of budget. Review non-essential purchases.",
                    category="expenses",
                    severity="warning",
                )
            )
        elif budget_utilisation >= 0.5 and total_spent > 0:
            insights.append(
                AIInsight(
                    emoji="💳",
                    title="Budget on Track",
                    message=f"You've used {budget_utilisation * 100:.0f}% of your monthly budget — healthy utilisation.",
                    category="expenses",
                    severity="neutral",
                )
            )

        if highest_cat:
            insights.append(
                AIInsight(
                    emoji="📊",
                    title=f"Top Spend: {highest_cat}",
                    message=f"'{highest_cat}' is your largest expense category this month. Consider setting a sub-budget.",
                    category="expenses",
                    severity="neutral",
                )
            )

        # --- Knowledge ---
        ready = doc_stats["ready"]
        total_docs = doc_stats["total"]
        if ready > 0:
            insights.append(
                AIInsight(
                    emoji="🧠",
                    title=f"{ready} Document{'s' if ready > 1 else ''} Ready for AI Search",
                    message=f"{ready} of {total_docs} knowledge documents are indexed and ready for semantic search.",
                    category="knowledge",
                    severity="positive",
                )
            )

        if memory_count > 0:
            insights.append(
                AIInsight(
                    emoji="💡",
                    title=f"{memory_count} Memory Records",
                    message=f"Your AI memory has {memory_count} long-term record{'s' if memory_count > 1 else ''} — a growing personal knowledge graph.",
                    category="knowledge",
                    severity="positive",
                )
            )

        return insights[:12]  # Cap at 12 for UI density
