"""Assistant tools layer for context extraction.

Fetches real user data from existing Phase 8 models to feed the context engine
and the rule-based intelligence layer.
"""

import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.analytics.models import (
    AnalyticsBudget,
    AnalyticsExpense,
    AnalyticsGoal,
    AnalyticsHabit,
    AnalyticsTask,
    GoalStatus,
    TaskStatus,
)
from app.features.analytics.service import AnalyticsService


class TaskTool:
    """Tool to retrieve task context."""

    @staticmethod
    async def run(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
        today = datetime.now(UTC).date()

        # Fetch today's completed, pending and overdue tasks
        stmt = select(AnalyticsTask).where(AnalyticsTask.user_id == user_id)
        result = await db.execute(stmt)
        tasks = result.scalars().all()

        completed_today = []
        pending_today = []
        overdue = []

        for t in tasks:
            if t.status == TaskStatus.COMPLETED:
                if t.completed_at and t.completed_at.date() == today:
                    completed_today.append(t)
            elif t.status == TaskStatus.OVERDUE:
                overdue.append(t)
            elif t.status == TaskStatus.PENDING:
                if t.due_date and t.due_date <= today:
                    pending_today.append(t)
                else:
                    # Generic pending task
                    pending_today.append(t)

        return {
            "total_count": len(tasks),
            "completed_today": [t.title for t in completed_today],
            "pending_today": [t.title for t in pending_today if t.due_date == today],
            "all_pending": [
                {"title": t.title, "priority": t.priority, "due_date": t.due_date}
                for t in pending_today
            ],
            "overdue": [{"title": t.title, "due_date": t.due_date} for t in overdue],
        }


class GoalTool:
    """Tool to retrieve goals context."""

    @staticmethod
    async def run(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
        stmt = (
            select(AnalyticsGoal)
            .where(AnalyticsGoal.user_id == user_id)
            .order_by(AnalyticsGoal.progress_pct.desc())
        )
        result = await db.execute(stmt)
        goals = result.scalars().all()

        active = []
        completed = []
        closest = None

        for g in goals:
            if g.status == GoalStatus.COMPLETED or g.progress_pct >= 100.0:
                completed.append(g)
            elif g.status == GoalStatus.ACTIVE:
                active.append(g)
                if closest is None:
                    # Since ordered by progress descending, the first active is closest
                    closest = g

        return {
            "total_count": len(goals),
            "active": [{"title": g.title, "progress": g.progress_pct} for g in active],
            "completed": [g.title for g in completed],
            "closest_to_completion": (
                {"title": closest.title, "progress": closest.progress_pct}
                if closest
                else None
            ),
        }


class HabitTool:
    """Tool to retrieve habits context and streaks."""

    @staticmethod
    async def run(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
        stmt = select(AnalyticsHabit).where(
            and_(
                AnalyticsHabit.user_id == user_id,
                AnalyticsHabit.is_active.is_(True),
            )
        )
        result = await db.execute(stmt)
        habits = result.scalars().all()
        today_str = datetime.now(UTC).date().isoformat()

        streaks = []
        missed = []
        completed_today = []

        for h in habits:
            completions = h.completions or []
            streaks.append(
                {
                    "name": h.name,
                    "streak": h.current_streak,
                    "longest": h.longest_streak,
                }
            )
            if today_str in completions:
                completed_today.append(h.name)
            else:
                missed.append(h.name)

        return {
            "total_count": len(habits),
            "streaks": streaks,
            "completed_today": completed_today,
            "missed_today": missed,
        }


class ExpenseTool:
    """Tool to retrieve expenses and budget context."""

    @staticmethod
    async def run(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
        now = datetime.now(UTC)
        year, month = now.year, now.month
        month_start = date(year, month, 1)

        # Budget limit
        stmt_b = select(AnalyticsBudget.monthly_limit).where(
            and_(
                AnalyticsBudget.user_id == user_id,
                AnalyticsBudget.year == year,
                AnalyticsBudget.month == month,
            )
        )
        res_b = await db.execute(stmt_b)
        budget = res_b.scalar_one_or_none() or 0.0

        # Current month expenses
        stmt_e = select(AnalyticsExpense).where(
            and_(
                AnalyticsExpense.user_id == user_id,
                AnalyticsExpense.expense_date >= month_start,
            )
        )
        res_e = await db.execute(stmt_e)
        expenses = res_e.scalars().all()

        total_spent = sum(e.amount for e in expenses)
        category_sums: dict[str, float] = {}
        for e in expenses:
            category_sums[e.category] = category_sums.get(e.category, 0.0) + float(
                e.amount
            )

        highest_cat = None
        highest_amt = 0.0
        for cat, amt in category_sums.items():
            if amt > highest_amt:
                highest_amt = amt
                highest_cat = cat

        return {
            "monthly_budget": float(budget),
            "total_spent": float(total_spent),
            "remaining_budget": float(max(budget - total_spent, 0.0)),
            "highest_category": highest_cat,
            "highest_category_amount": highest_amt,
            "category_distribution": [
                {"category": cat, "amount": amt} for cat, amt in category_sums.items()
            ],
        }


class AnalyticsTool:
    """Tool to retrieve productivity analytics score summaries."""

    @staticmethod
    async def run(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
        try:
            # Reuses Phase 8 service
            dashboard = await AnalyticsService.get_dashboard(db, user_id)
            return {
                "productivity_score": dashboard.productivity_score,
                "habit_score": dashboard.habit_score,
                "goal_score": dashboard.goal_score,
                "overall_health_score": dashboard.overall_health_score,
                "total_documents": dashboard.total_documents,
                "total_memories": dashboard.total_memories,
                "task_completion_rate": dashboard.task_completion_rate,
            }
        except Exception:
            return {
                "productivity_score": 0.0,
                "habit_score": 0.0,
                "goal_score": 0.0,
                "overall_health_score": 0.0,
                "total_documents": 0,
                "total_memories": 0,
                "task_completion_rate": 0.0,
            }
