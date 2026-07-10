"""Phase 8: Analytics feature test suite.

Tests cover:
1. Repository unit tests (in-memory SQLite via conftest.py)
2. Service computation tests (scoring formulas, insight generation)
3. API integration tests for all 5 GET endpoints
4. Empty-data edge cases
5. Authentication protection (401 without token)
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.analytics.models import (
    AnalyticsBudget,
    AnalyticsExpense,
    AnalyticsGoal,
    AnalyticsHabit,
    AnalyticsTask,
    GoalStatus,
    HabitFrequency,
    TaskStatus,
)
from app.features.analytics.repository import AnalyticsRepository
from app.features.analytics.service import AnalyticsService
from app.features.auth.models import Role, User
from app.features.auth.repositories import RoleRepository, UserRepository
from app.features.auth.security import create_access_token

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
async def seed_role(db_session: AsyncSession):
    role = await RoleRepository.get_by_name(db_session, "USER")
    if not role:
        role = await RoleRepository.create(
            db_session, name="USER", description="Standard user"
        )
    await db_session.commit()
    return role


@pytest.fixture
async def test_user(db_session: AsyncSession, seed_role: Role) -> User:
    user = await UserRepository.get_by_username(db_session, "analytics_tester")
    if not user:
        user = await UserRepository.create(
            db_session,
            {
                "full_name": "Analytics Tester",
                "username": "analytics_tester",
                "email": "analytics@example.com",
                "hashed_password": "fakehash",
                "role_id": seed_role.id,
            },
        )
        await db_session.commit()
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    token = create_access_token(
        subject=str(test_user.id), expires_delta=timedelta(hours=1)
    )
    return {"Authorization": f"Bearer {token}"}


async def _seed_tasks(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Seed 5 tasks: 3 completed, 1 pending, 1 overdue."""
    now = datetime.now(UTC)
    today = now.date()

    tasks = [
        AnalyticsTask(
            user_id=user_id,
            title="Task A",
            status=TaskStatus.COMPLETED,
            completed_at=now - timedelta(hours=2),
            priority=3,
            category="Work",
        ),
        AnalyticsTask(
            user_id=user_id,
            title="Task B",
            status=TaskStatus.COMPLETED,
            completed_at=now - timedelta(days=1),
            priority=2,
            category="Work",
        ),
        AnalyticsTask(
            user_id=user_id,
            title="Task C",
            status=TaskStatus.COMPLETED,
            completed_at=now - timedelta(days=2),
            priority=1,
            category="Personal",
        ),
        AnalyticsTask(
            user_id=user_id,
            title="Task D",
            status=TaskStatus.PENDING,
            due_date=today + timedelta(days=3),
            priority=2,
        ),
        AnalyticsTask(
            user_id=user_id,
            title="Task E",
            status=TaskStatus.OVERDUE,
            due_date=today - timedelta(days=1),
            priority=3,
        ),
    ]
    for t in tasks:
        db.add(t)
    await db.flush()


async def _seed_habits(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Seed 2 habits with completions over the last 7 days."""
    today = datetime.now(UTC).date()
    last_7 = [(today - timedelta(days=i)).isoformat() for i in range(7)]

    habits = [
        AnalyticsHabit(
            user_id=user_id,
            name="Morning Run",
            frequency=HabitFrequency.DAILY,
            completions=last_7,  # Completed every day
            current_streak=7,
            longest_streak=14,
            color="#6366f1",
        ),
        AnalyticsHabit(
            user_id=user_id,
            name="Meditation",
            frequency=HabitFrequency.DAILY,
            completions=last_7[:4],  # 4 of 7 days
            current_streak=4,
            longest_streak=8,
            color="#8b5cf6",
        ),
    ]
    for h in habits:
        db.add(h)
    await db.flush()


async def _seed_goals(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Seed 2 goals: 1 active at 60%, 1 completed."""
    today = datetime.now(UTC).date()
    goals = [
        AnalyticsGoal(
            user_id=user_id,
            title="Learn Spanish",
            status=GoalStatus.ACTIVE,
            progress_pct=60.0,
            deadline=today + timedelta(days=90),
            category="Self-Improvement",
        ),
        AnalyticsGoal(
            user_id=user_id,
            title="Read 12 books",
            status=GoalStatus.COMPLETED,
            progress_pct=100.0,
            category="Education",
        ),
    ]
    for g in goals:
        db.add(g)
    await db.flush()


async def _seed_expenses(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Seed 3 expenses across 2 categories for the current month."""
    today = datetime.now(UTC).date()
    expenses = [
        AnalyticsExpense(
            user_id=user_id,
            amount=45.00,
            category="Food",
            expense_date=today,
        ),
        AnalyticsExpense(
            user_id=user_id,
            amount=120.00,
            category="Transport",
            expense_date=today - timedelta(days=1),
        ),
        AnalyticsExpense(
            user_id=user_id,
            amount=35.50,
            category="Food",
            expense_date=today - timedelta(days=2),
        ),
    ]
    for e in expenses:
        db.add(e)

    now = datetime.now(UTC)
    budget = AnalyticsBudget(
        user_id=user_id,
        monthly_limit=500.00,
        year=now.year,
        month=now.month,
    )
    db.add(budget)
    await db.flush()


# =============================================================================
# Repository Unit Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_task_counts_empty(db_session: AsyncSession, test_user: User):
    """Empty-data edge case: should return all zeros gracefully."""
    counts = await AnalyticsRepository.get_task_counts(db_session, test_user.id)
    assert counts["total"] == 0
    assert counts["completed"] == 0
    assert counts["overdue"] == 0


@pytest.mark.asyncio
async def test_get_task_counts_with_data(db_session: AsyncSession, test_user: User):
    await _seed_tasks(db_session, test_user.id)
    await db_session.commit()

    counts = await AnalyticsRepository.get_task_counts(db_session, test_user.id)
    assert counts["total"] == 5
    assert counts["completed"] == 3
    assert counts["pending"] == 1
    assert counts["overdue"] == 1
    assert counts["completed_today"] == 1  # Task A completed ~2 hours ago


@pytest.mark.asyncio
async def test_get_tasks_by_category(db_session: AsyncSession, test_user: User):
    await _seed_tasks(db_session, test_user.id)
    await db_session.commit()

    by_cat = await AnalyticsRepository.get_tasks_by_category(db_session, test_user.id)
    assert "Work" in by_cat
    assert by_cat["Work"] == 2
    assert by_cat.get("Personal") == 1


@pytest.mark.asyncio
async def test_get_habit_counts(db_session: AsyncSession, test_user: User):
    await _seed_habits(db_session, test_user.id)
    await db_session.commit()

    counts = await AnalyticsRepository.get_habit_counts(db_session, test_user.id)
    assert counts["total"] == 2
    assert counts["active"] == 2


@pytest.mark.asyncio
async def test_get_all_habits(db_session: AsyncSession, test_user: User):
    await _seed_habits(db_session, test_user.id)
    await db_session.commit()

    habits = await AnalyticsRepository.get_all_habits(db_session, test_user.id)
    assert len(habits) == 2
    # Both should be active
    assert all(h.is_active for h in habits)


@pytest.mark.asyncio
async def test_get_goal_counts(db_session: AsyncSession, test_user: User):
    await _seed_goals(db_session, test_user.id)
    await db_session.commit()

    counts = await AnalyticsRepository.get_goal_counts(db_session, test_user.id)
    assert counts["total"] == 2
    assert counts["active"] == 1
    assert counts["completed"] == 1
    assert counts["avg_progress"] == pytest.approx(80.0, abs=1.0)


@pytest.mark.asyncio
async def test_get_expense_totals(db_session: AsyncSession, test_user: User):
    await _seed_expenses(db_session, test_user.id)
    await db_session.commit()

    now = datetime.now(UTC)
    totals = await AnalyticsRepository.get_expense_totals(
        db_session, test_user.id, now.year, now.month
    )
    assert totals["total"] == pytest.approx(200.50, abs=0.01)
    assert totals["count"] == 3


@pytest.mark.asyncio
async def test_get_expense_by_category(db_session: AsyncSession, test_user: User):
    await _seed_expenses(db_session, test_user.id)
    await db_session.commit()

    now = datetime.now(UTC)
    cats = await AnalyticsRepository.get_expense_by_category(
        db_session, test_user.id, now.year, now.month
    )
    assert len(cats) == 2
    # Highest should be Transport (120.00)
    assert cats[0]["category"] == "Transport"
    assert cats[0]["amount"] == pytest.approx(120.0, abs=0.01)


@pytest.mark.asyncio
async def test_get_monthly_budget(db_session: AsyncSession, test_user: User):
    await _seed_expenses(db_session, test_user.id)
    await db_session.commit()

    now = datetime.now(UTC)
    budget = await AnalyticsRepository.get_monthly_budget(
        db_session, test_user.id, now.year, now.month
    )
    assert budget == pytest.approx(500.0, abs=0.01)


@pytest.mark.asyncio
async def test_get_document_stats_empty(db_session: AsyncSession, test_user: User):
    stats = await AnalyticsRepository.get_document_stats(db_session, test_user.id)
    assert stats["total"] == 0
    assert stats["ready"] == 0


# =============================================================================
# Service Computation Tests
# =============================================================================


def test_compute_task_score_full_completion():
    counts = {"total": 10, "completed": 10, "overdue": 0, "pending": 0}
    score = AnalyticsService._compute_task_score(counts)
    assert score == pytest.approx(100.0, abs=0.1)


def test_compute_task_score_with_overdue_penalty():
    counts = {"total": 10, "completed": 8, "overdue": 4, "pending": 2}
    score = AnalyticsService._compute_task_score(counts)
    # (8 - 4 * 0.5) / 10 * 100 = (8-2)/10 * 100 = 60
    assert score == pytest.approx(60.0, abs=0.1)


def test_compute_task_score_empty():
    counts = {"total": 0, "completed": 0, "overdue": 0, "pending": 0}
    score = AnalyticsService._compute_task_score(counts)
    assert score == 0.0


def test_compute_habit_score_all_complete():
    """All habits completed every day for last 7 days → score = 100."""
    today = datetime.now(UTC).date()
    last_7 = [(today - timedelta(days=i)).isoformat() for i in range(7)]

    class FakeHabit:
        completions = last_7

    score = AnalyticsService._compute_habit_score([FakeHabit()], today)
    assert score == pytest.approx(100.0, abs=0.1)


def test_compute_habit_score_no_habits():
    today = datetime.now(UTC).date()
    score = AnalyticsService._compute_habit_score([], today)
    assert score == 0.0


def test_compute_goal_score():
    counts = {"total": 4, "completed": 2, "avg_progress": 75.0}
    score = AnalyticsService._compute_goal_score(counts)
    # 60% * (2/4) + 40% * (75/100) = 30 + 30 = 60
    assert score == pytest.approx(60.0, abs=0.5)


def test_generate_insights_productivity():
    insights = AnalyticsService._generate_insights(
        task_counts={"total": 10, "completed": 9, "overdue": 0, "pending": 1},
        habit_rate=0.95,
        longest_streak=14,
        best_habit="Morning Run",
        goal_counts={"total": 3, "completed": 2, "active": 1, "avg_progress": 80.0},
        budget_utilisation=0.6,
        total_spent=300.0,
        highest_cat="Food",
        doc_stats={"total": 5, "ready": 4, "processing": 0, "failed": 0},
        memory_count=12,
        productivity_score=88.0,
    )
    assert len(insights) > 0
    categories = {i.category for i in insights}
    # Should cover at least 2 different domains
    assert len(categories) >= 2
    # Should have positive insights for high completion rate
    severities = {i.severity for i in insights}
    assert "positive" in severities


def test_generate_insights_warning_overdue():
    insights = AnalyticsService._generate_insights(
        task_counts={"total": 10, "completed": 3, "overdue": 5, "pending": 2},
        habit_rate=0.3,
        longest_streak=0,
        best_habit=None,
        goal_counts={"total": 2, "completed": 0, "active": 2, "avg_progress": 25.0},
        budget_utilisation=0.95,
        total_spent=475.0,
        highest_cat="Shopping",
        doc_stats={"total": 0, "ready": 0, "processing": 0, "failed": 0},
        memory_count=0,
        productivity_score=22.0,
    )
    # Warning insights should be present
    warning_insights = [i for i in insights if i.severity == "warning"]
    assert len(warning_insights) > 0


def test_build_habit_summary():
    today = datetime.now(UTC).date()
    last_7 = [(today - timedelta(days=i)).isoformat() for i in range(7)]

    class FakeHabit:
        id = uuid.uuid4()
        name = "Running"
        completions = last_7[:5]  # 5/7 days
        current_streak = 5
        longest_streak = 10
        frequency = HabitFrequency.DAILY
        color = "#6366f1"

    summary = AnalyticsService._build_habit_summary(FakeHabit(), today)
    assert summary.name == "Running"
    assert summary.completion_rate_7d == pytest.approx(5 / 7, abs=0.01)
    assert len(summary.heatmap) == 7


@pytest.mark.asyncio
async def test_get_task_analytics_service(db_session: AsyncSession, test_user: User):
    await _seed_tasks(db_session, test_user.id)
    await db_session.commit()

    result = await AnalyticsService.get_task_analytics(db_session, test_user.id)
    assert result.total_tasks == 5
    assert result.completed_tasks == 3
    assert result.overdue_tasks == 1
    assert result.completion_rate == pytest.approx(0.6, abs=0.01)


@pytest.mark.asyncio
async def test_get_habit_analytics_service(db_session: AsyncSession, test_user: User):
    await _seed_habits(db_session, test_user.id)
    await db_session.commit()

    result = await AnalyticsService.get_habit_analytics(db_session, test_user.id)
    assert result.total_habits == 2
    assert result.active_habits == 2
    assert result.longest_streak >= 8  # Second habit has longest_streak=8
    assert result.best_habit is not None


@pytest.mark.asyncio
async def test_get_expense_analytics_service(db_session: AsyncSession, test_user: User):
    await _seed_expenses(db_session, test_user.id)
    await db_session.commit()

    result = await AnalyticsService.get_expense_analytics(db_session, test_user.id)
    assert result.total_spending == pytest.approx(200.50, abs=0.01)
    assert result.monthly_budget == pytest.approx(500.0, abs=0.01)
    assert result.budget_utilisation == pytest.approx(0.401, abs=0.01)
    assert result.transaction_count == 3
    assert result.highest_category == "Transport"


# =============================================================================
# API Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_dashboard_unauthenticated(client: AsyncClient):
    """Dashboard must return 401 without auth token."""
    res = await client.get("/api/v1/analytics/dashboard")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_authenticated_empty(client: AsyncClient, auth_headers: dict):
    """Empty user should get a valid (zeroed) dashboard response."""
    res = await client.get("/api/v1/analytics/dashboard", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["productivity_score"] == 0.0
    assert data["total_tasks"] == 0
    # Since productivity is 0.0, the insight engine will add a warning insight
    assert len(data["ai_insights"]) == 1
    assert data["ai_insights"][0]["category"] == "productivity"
    assert data["ai_insights"][0]["severity"] == "warning"


@pytest.mark.asyncio
async def test_dashboard_with_data(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
):
    await _seed_tasks(db_session, test_user.id)
    await _seed_habits(db_session, test_user.id)
    await _seed_goals(db_session, test_user.id)
    await _seed_expenses(db_session, test_user.id)
    await db_session.commit()

    res = await client.get("/api/v1/analytics/dashboard", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_tasks"] == 5
    assert data["completed_tasks"] == 3
    assert data["total_goals"] == 2
    assert len(data["weekly_productivity"]) == 7
    assert len(data["ai_insights"]) > 0


@pytest.mark.asyncio
async def test_tasks_endpoint(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
):
    await _seed_tasks(db_session, test_user.id)
    await db_session.commit()

    res = await client.get("/api/v1/analytics/tasks", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_tasks"] == 5
    assert data["completion_rate"] == pytest.approx(0.6, abs=0.01)
    assert "Work" in data["by_category"]


@pytest.mark.asyncio
async def test_habits_endpoint(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
):
    await _seed_habits(db_session, test_user.id)
    await db_session.commit()

    res = await client.get("/api/v1/analytics/habits", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_habits"] == 2
    assert len(data["habits"]) == 2
    # Each habit should have a 7-element heatmap
    for habit in data["habits"]:
        assert len(habit["heatmap"]) == 7


@pytest.mark.asyncio
async def test_goals_endpoint(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
):
    await _seed_goals(db_session, test_user.id)
    await db_session.commit()

    res = await client.get("/api/v1/analytics/goals", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_goals"] == 2
    assert data["completed_goals"] == 1
    assert data["active_goals"] == 1
    assert data["closest_to_completion"] is not None
    assert data["closest_to_completion"]["title"] == "Learn Spanish"


@pytest.mark.asyncio
async def test_expenses_endpoint(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
):
    await _seed_expenses(db_session, test_user.id)
    await db_session.commit()

    res = await client.get("/api/v1/analytics/expenses", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_spending"] == pytest.approx(200.50, abs=0.01)
    assert data["monthly_budget"] == pytest.approx(500.0, abs=0.01)
    assert len(data["category_distribution"]) == 2
    assert data["highest_category"] == "Transport"


@pytest.mark.asyncio
async def test_all_endpoints_unauthenticated(client: AsyncClient):
    """All analytics endpoints must reject unauthenticated requests."""
    endpoints = [
        "/api/v1/analytics/dashboard",
        "/api/v1/analytics/tasks",
        "/api/v1/analytics/habits",
        "/api/v1/analytics/goals",
        "/api/v1/analytics/expenses",
    ]
    for endpoint in endpoints:
        res = await client.get(endpoint)
        assert res.status_code == 401, f"{endpoint} should return 401"
