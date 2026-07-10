"""Analytics models: lightweight domain models for Phase 8 analytics aggregation.

These models exist specifically to give the analytics engine real DB tables to
query and aggregate from. They will be superseded/merged when full Tasks,
Habits, Goals and Expenses CRUD modules are implemented in a future phase.
"""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import Base, TimestampMixin, UUIDMixin

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class HabitFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


class GoalStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class AnalyticsTask(Base, UUIDMixin, TimestampMixin):
    """
    Lightweight task record used by the analytics engine to calculate
    completion rates, overdue counts and weekly productivity trends.
    """

    __tablename__ = "analytics_tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        server_default=TaskStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    priority: Mapped[int] = mapped_column(
        Integer, default=2, nullable=False
    )  # 1=low, 2=medium, 3=high
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationship back to User (lazy noload to avoid circular import)
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates=None, lazy="noload"
    )


class AnalyticsHabit(Base, UUIDMixin, TimestampMixin):
    """
    Habit record with completion history stored as a JSON list of ISO date strings.
    The analytics engine derives streaks and weekly heatmaps from this data.
    """

    __tablename__ = "analytics_habits"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    frequency: Mapped[HabitFrequency] = mapped_column(
        Enum(HabitFrequency),
        default=HabitFrequency.DAILY,
        nullable=False,
    )
    # Ordered list of ISO date strings on which the habit was completed
    completions: Mapped[list[str]] = mapped_column(
        JSON, default=list, server_default="[]", nullable=False
    )
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    color: Mapped[str] = mapped_column(
        String(20), default="#6366f1", nullable=False
    )  # CSS hex for UI

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates=None, lazy="noload"
    )


class AnalyticsGoal(Base, UUIDMixin, TimestampMixin):
    """
    Goal record with a numeric progress percentage and deadline.
    """

    __tablename__ = "analytics_goals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[GoalStatus] = mapped_column(
        Enum(GoalStatus),
        default=GoalStatus.ACTIVE,
        server_default=GoalStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )
    progress_pct: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # 0.0–100.0
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_quarterly: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates=None, lazy="noload"
    )


class AnalyticsExpense(Base, UUIDMixin, TimestampMixin):
    """
    Expense entry used for budget analytics, category distribution and
    monthly trend computation.
    """

    __tablename__ = "analytics_expenses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    is_recurring: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates=None, lazy="noload"
    )


class AnalyticsBudget(Base, UUIDMixin, TimestampMixin):
    """
    Monthly budget ceiling per user.  The analytics engine uses this to
    compute spending utilisation and remaining budget.
    """

    __tablename__ = "analytics_budgets"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    monthly_limit: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0.0
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-12

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates=None, lazy="noload"
    )
