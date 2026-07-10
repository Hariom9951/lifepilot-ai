"""Analytics repository — all aggregation queries live here.

Design principles:
- All methods are static to match the project-wide repository pattern.
- Batch aggregation with func.count() + case() avoids N+1 queries.
- Raw SQL CTEs are avoided; SQLAlchemy Core expressions are used throughout.
- Each method returns plain Python primitives or lightweight dicts; the
  service layer is responsible for transforming them into Pydantic models.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import String, and_, case, cast, func, select
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
from app.features.knowledge.models import Document, DocumentStatus
from app.features.memory.models import UserMemory


class AnalyticsRepository:
    """
    Asynchronous repository for cross-feature analytics aggregation.
    All reads are optimised single-round-trip queries.
    """

    # ------------------------------------------------------------------
    # Task aggregation
    # ------------------------------------------------------------------

    @staticmethod
    async def get_task_counts(db: AsyncSession, user_id: uuid.UUID) -> dict[str, int]:
        """
        Return per-status task counts for a user in a single query using
        conditional aggregation (no N+1).
        """
        now_utc = datetime.now(UTC)
        today = now_utc.date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        stmt = select(
            func.count().label("total"),
            func.sum(
                case((AnalyticsTask.status == TaskStatus.COMPLETED, 1), else_=0)
            ).label("completed"),
            func.sum(
                case((AnalyticsTask.status == TaskStatus.PENDING, 1), else_=0)
            ).label("pending"),
            func.sum(
                case((AnalyticsTask.status == TaskStatus.OVERDUE, 1), else_=0)
            ).label("overdue"),
            func.sum(
                case((AnalyticsTask.status == TaskStatus.CANCELLED, 1), else_=0)
            ).label("cancelled"),
            # Completed today
            func.sum(
                case(
                    (
                        and_(
                            AnalyticsTask.status == TaskStatus.COMPLETED,
                            func.date(AnalyticsTask.completed_at) == today,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("completed_today"),
            # Completed this week
            func.sum(
                case(
                    (
                        and_(
                            AnalyticsTask.status == TaskStatus.COMPLETED,
                            func.date(AnalyticsTask.completed_at) >= week_start,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("completed_this_week"),
            # Completed this month
            func.sum(
                case(
                    (
                        and_(
                            AnalyticsTask.status == TaskStatus.COMPLETED,
                            func.date(AnalyticsTask.completed_at) >= month_start,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("completed_this_month"),
        ).where(AnalyticsTask.user_id == user_id)

        result = await db.execute(stmt)
        row = result.one()
        return {
            "total": row.total or 0,
            "completed": row.completed or 0,
            "pending": row.pending or 0,
            "overdue": row.overdue or 0,
            "cancelled": row.cancelled or 0,
            "completed_today": row.completed_today or 0,
            "completed_this_week": row.completed_this_week or 0,
            "completed_this_month": row.completed_this_month or 0,
        }

    @staticmethod
    async def get_tasks_by_priority(
        db: AsyncSession, user_id: uuid.UUID
    ) -> dict[str, int]:
        """Return count of tasks grouped by priority level."""
        stmt = (
            select(AnalyticsTask.priority, func.count().label("cnt"))
            .where(AnalyticsTask.user_id == user_id)
            .group_by(AnalyticsTask.priority)
        )
        result = await db.execute(stmt)
        mapping = {1: "low", 2: "medium", 3: "high"}
        return {
            mapping.get(row.priority, str(row.priority)): row.cnt
            for row in result.all()
        }

    @staticmethod
    async def get_tasks_by_category(
        db: AsyncSession, user_id: uuid.UUID
    ) -> dict[str, int]:
        """Return count of tasks grouped by category string."""
        stmt = (
            select(
                func.coalesce(AnalyticsTask.category, "Uncategorised").label("cat"),
                func.count().label("cnt"),
            )
            .where(AnalyticsTask.user_id == user_id)
            .group_by("cat")
        )
        result = await db.execute(stmt)
        return {row.cat: row.cnt for row in result.all()}

    @staticmethod
    async def get_tasks_completed_per_day(
        db: AsyncSession, user_id: uuid.UUID, days: int = 7
    ) -> dict[str, int]:
        """
        Return a mapping of ISO date string → completed task count for the
        last `days` days.  Used to build the weekly productivity chart.
        """
        cutoff = (datetime.now(UTC) - timedelta(days=days)).date()
        stmt = (
            select(
                cast(func.date(AnalyticsTask.completed_at), String).label("day"),
                func.count().label("cnt"),
            )
            .where(
                and_(
                    AnalyticsTask.user_id == user_id,
                    AnalyticsTask.status == TaskStatus.COMPLETED,
                    func.date(AnalyticsTask.completed_at) >= cutoff,
                )
            )
            .group_by("day")
        )
        result = await db.execute(stmt)
        return {row.day: row.cnt for row in result.all() if row.day}

    @staticmethod
    async def get_tasks_completed_monthly(
        db: AsyncSession, user_id: uuid.UUID, months: int = 6
    ) -> list[dict[str, Any]]:
        """Return monthly completed task counts for the last `months` months."""
        cutoff = (datetime.now(UTC) - timedelta(days=months * 30)).date()
        stmt = (
            select(
                func.strftime("%Y-%m", AnalyticsTask.completed_at).label("month"),
                func.count().label("cnt"),
            )
            .where(
                and_(
                    AnalyticsTask.user_id == user_id,
                    AnalyticsTask.status == TaskStatus.COMPLETED,
                    func.date(AnalyticsTask.completed_at) >= cutoff,
                )
            )
            .group_by("month")
            .order_by("month")
        )
        result = await db.execute(stmt)
        return [{"month": row.month, "count": row.cnt} for row in result.all()]

    # ------------------------------------------------------------------
    # Habit aggregation
    # ------------------------------------------------------------------

    @staticmethod
    async def get_all_habits(
        db: AsyncSession, user_id: uuid.UUID
    ) -> list[AnalyticsHabit]:
        """Fetch all active habits for a user with completions JSON loaded."""
        stmt = (
            select(AnalyticsHabit)
            .where(
                and_(
                    AnalyticsHabit.user_id == user_id,
                    AnalyticsHabit.is_active.is_(True),
                )
            )
            .order_by(AnalyticsHabit.created_at.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_habit_counts(db: AsyncSession, user_id: uuid.UUID) -> dict[str, int]:
        """Return total and active habit counts."""
        stmt = select(
            func.count().label("total"),
            func.sum(case((AnalyticsHabit.is_active.is_(True), 1), else_=0)).label(
                "active"
            ),
        ).where(AnalyticsHabit.user_id == user_id)
        result = await db.execute(stmt)
        row = result.one()
        return {"total": row.total or 0, "active": row.active or 0}

    # ------------------------------------------------------------------
    # Goal aggregation
    # ------------------------------------------------------------------

    @staticmethod
    async def get_goal_counts(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
        """Return per-status goal counts and average progress."""
        stmt = select(
            func.count().label("total"),
            func.sum(
                case((AnalyticsGoal.status == GoalStatus.ACTIVE, 1), else_=0)
            ).label("active"),
            func.sum(
                case((AnalyticsGoal.status == GoalStatus.COMPLETED, 1), else_=0)
            ).label("completed"),
            func.sum(
                case((AnalyticsGoal.status == GoalStatus.PAUSED, 1), else_=0)
            ).label("paused"),
            func.sum(
                case(
                    (AnalyticsGoal.is_quarterly.is_(True), 1),
                    else_=0,
                )
            ).label("quarterly"),
            func.avg(AnalyticsGoal.progress_pct).label("avg_progress"),
        ).where(AnalyticsGoal.user_id == user_id)
        result = await db.execute(stmt)
        row = result.one()
        return {
            "total": row.total or 0,
            "active": row.active or 0,
            "completed": row.completed or 0,
            "paused": row.paused or 0,
            "quarterly": row.quarterly or 0,
            "avg_progress": float(row.avg_progress or 0.0),
        }

    @staticmethod
    async def get_all_goals(
        db: AsyncSession, user_id: uuid.UUID
    ) -> list[AnalyticsGoal]:
        """Fetch all goals for a user ordered by progress descending."""
        stmt = (
            select(AnalyticsGoal)
            .where(AnalyticsGoal.user_id == user_id)
            .order_by(AnalyticsGoal.progress_pct.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Expense aggregation
    # ------------------------------------------------------------------

    @staticmethod
    async def get_expense_totals(
        db: AsyncSession, user_id: uuid.UUID, year: int, month: int
    ) -> dict[str, Any]:
        """Return total spending and transaction count for a given month."""
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1)
        else:
            month_end = date(year, month + 1, 1)

        stmt = select(
            func.coalesce(func.sum(AnalyticsExpense.amount), 0.0).label("total"),
            func.count().label("count"),
        ).where(
            and_(
                AnalyticsExpense.user_id == user_id,
                AnalyticsExpense.expense_date >= month_start,
                AnalyticsExpense.expense_date < month_end,
            )
        )
        result = await db.execute(stmt)
        row = result.one()
        return {"total": float(row.total), "count": row.count}

    @staticmethod
    async def get_expense_by_category(
        db: AsyncSession, user_id: uuid.UUID, year: int, month: int
    ) -> list[dict[str, Any]]:
        """Return per-category spending for a given month."""
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1)
        else:
            month_end = date(year, month + 1, 1)

        stmt = (
            select(
                AnalyticsExpense.category,
                func.sum(AnalyticsExpense.amount).label("total"),
            )
            .where(
                and_(
                    AnalyticsExpense.user_id == user_id,
                    AnalyticsExpense.expense_date >= month_start,
                    AnalyticsExpense.expense_date < month_end,
                )
            )
            .group_by(AnalyticsExpense.category)
            .order_by(func.sum(AnalyticsExpense.amount).desc())
        )
        result = await db.execute(stmt)
        return [
            {"category": row.category, "amount": float(row.total)}
            for row in result.all()
        ]

    @staticmethod
    async def get_monthly_spending_trend(
        db: AsyncSession, user_id: uuid.UUID, months: int = 6
    ) -> list[dict[str, Any]]:
        """Return per-month spending for the last `months` months."""
        cutoff = (datetime.now(UTC) - timedelta(days=months * 30)).date()
        stmt = (
            select(
                func.strftime("%Y-%m", AnalyticsExpense.expense_date).label("month"),
                func.sum(AnalyticsExpense.amount).label("total"),
            )
            .where(
                and_(
                    AnalyticsExpense.user_id == user_id,
                    AnalyticsExpense.expense_date >= cutoff,
                )
            )
            .group_by("month")
            .order_by("month")
        )
        result = await db.execute(stmt)
        return [
            {"month": row.month, "amount": float(row.total)} for row in result.all()
        ]

    @staticmethod
    async def get_monthly_budget(
        db: AsyncSession, user_id: uuid.UUID, year: int, month: int
    ) -> float:
        """Return the budget limit for the given month, or 0.0 if unset."""
        stmt = select(AnalyticsBudget.monthly_limit).where(
            and_(
                AnalyticsBudget.user_id == user_id,
                AnalyticsBudget.year == year,
                AnalyticsBudget.month == month,
            )
        )
        result = await db.execute(stmt)
        value = result.scalar_one_or_none()
        return float(value) if value is not None else 0.0

    # ------------------------------------------------------------------
    # Knowledge & Memory cross-feature reads
    # ------------------------------------------------------------------

    @staticmethod
    async def get_document_stats(
        db: AsyncSession, user_id: uuid.UUID
    ) -> dict[str, int]:
        """Return document counts per status for the knowledge section."""
        stmt = select(
            func.count().label("total"),
            func.sum(case((Document.status == DocumentStatus.READY, 1), else_=0)).label(
                "ready"
            ),
            func.sum(
                case((Document.status == DocumentStatus.PROCESSING, 1), else_=0)
            ).label("processing"),
            func.sum(
                case((Document.status == DocumentStatus.FAILED, 1), else_=0)
            ).label("failed"),
        ).where(Document.user_id == user_id)
        result = await db.execute(stmt)
        row = result.one()
        return {
            "total": row.total or 0,
            "ready": row.ready or 0,
            "processing": row.processing or 0,
            "failed": row.failed or 0,
        }

    @staticmethod
    async def get_memory_count(db: AsyncSession, user_id: uuid.UUID) -> int:
        """Return total non-archived long-term memory count."""
        stmt = (
            select(func.count())
            .select_from(UserMemory)
            .where(
                and_(
                    UserMemory.user_id == user_id,
                    UserMemory.is_archived.is_(False),
                )
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one() or 0
