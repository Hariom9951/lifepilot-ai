"""Phase 9: Conversational AI Assistant test suite.

Tests cover:
1. Intent classification logic (IntentClassifier)
2. Response templates formatting (ResponseTemplates)
3. Planner logic (Planner.generate_plan)
4. Context engine tools retrieval (TaskTool, GoalTool, HabitTool, ExpenseTool, AnalyticsTool)
5. API Integration tests (chat query, history list, history clear)
"""

import uuid
from datetime import UTC, date, datetime, timedelta

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
from app.features.assistant.intent import AssistantIntent, IntentClassifier
from app.features.assistant.planner import Planner
from app.features.assistant.prompts import ResponseTemplates
from app.features.assistant.tools import (
    AnalyticsTool,
    ExpenseTool,
    GoalTool,
    HabitTool,
    TaskTool,
)
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
    user = await UserRepository.get_by_username(db_session, "assistant_tester")
    if not user:
        user = await UserRepository.create(
            db_session,
            {
                "full_name": "Assistant Tester",
                "username": "assistant_tester",
                "email": "assistant@example.com",
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


# =============================================================================
# Unit Tests: Intent Classifier & Response Templates & Planner
# =============================================================================


def test_intent_classifier():
    """Verify that user statements are classified to correct intents."""
    assert IntentClassifier.classify("hello there") == AssistantIntent.GREETING
    assert IntentClassifier.classify("hi") == AssistantIntent.GREETING
    assert (
        IntentClassifier.classify("what should i do today?") == AssistantIntent.PLANNING
    )
    assert IntentClassifier.classify("suggest a schedule") == AssistantIntent.PLANNING
    assert (
        IntentClassifier.classify("how can i improve my streaks?")
        == AssistantIntent.RECOMMENDATION
    )
    assert (
        IntentClassifier.classify("summarize my productivity score")
        == AssistantIntent.ANALYTICS
    )
    assert (
        IntentClassifier.classify("how much money did i spend?")
        == AssistantIntent.EXPENSE
    )
    assert IntentClassifier.classify("am i on budget?") == AssistantIntent.EXPENSE
    assert (
        IntentClassifier.classify("which goal am i closest to completing?")
        == AssistantIntent.GOAL
    )
    assert (
        IntentClassifier.classify("what habits am i missing?") == AssistantIntent.HABIT
    )
    assert IntentClassifier.classify("show my tasks") == AssistantIntent.TASK
    assert (
        IntentClassifier.classify("what's the weather like?") == AssistantIntent.GENERAL
    )


def test_response_templates():
    """Verify markdown response formatting works correctly."""
    greeting = ResponseTemplates.greeting("Alice Smith")
    assert "Alice" in greeting
    assert "LifePilot AI Assistant" in greeting

    task_ctx = {
        "total_count": 0,
        "overdue": [],
        "all_pending": [],
        "completed_today": [],
    }
    assert "empty" in ResponseTemplates.task(task_ctx).lower()

    task_ctx = {
        "total_count": 2,
        "overdue": [{"title": "Overdue Homework", "due_date": date.today()}],
        "all_pending": [
            {"title": "Read Book", "priority": 2, "due_date": date.today()}
        ],
        "completed_today": ["Workout"],
    }
    task_res = ResponseTemplates.task(task_ctx)
    assert "Overdue Homework" in task_res
    assert "Read Book" in task_res
    assert "completing **1** task" in task_res

    goal_ctx = {
        "active": [{"title": "Learn FastAPI", "progress": 85.0}],
        "completed": ["Build Web App"],
        "closest_to_completion": {"title": "Learn FastAPI", "progress": 85.0},
    }
    goal_res = ResponseTemplates.goal(goal_ctx)
    assert "Learn FastAPI" in goal_res
    assert "Build Web App" in goal_res
    assert "85%" in goal_res

    habit_ctx = {
        "streaks": [{"name": "Meditation", "streak": 10, "longest": 15}],
        "completed_today": ["Meditation"],
        "missed_today": ["Running"],
    }
    habit_res = ResponseTemplates.habit(habit_ctx)
    assert "Meditation" in habit_res
    assert "Running" in habit_res
    assert "10 days" in habit_res

    expense_ctx = {
        "total_spent": 120.50,
        "monthly_budget": 500.00,
        "remaining_budget": 379.50,
        "highest_category": "Food",
        "highest_category_amount": 80.00,
    }
    expense_res = ResponseTemplates.expense(expense_ctx)
    assert "$120.50" in expense_res
    assert "$500.00" in expense_res
    assert "Food" in expense_res

    analytics_ctx = {
        "productivity_score": 90.0,
        "habit_score": 80.0,
        "goal_score": 70.0,
        "overall_health_score": 80.0,
    }
    analytics_res = ResponseTemplates.analytics(analytics_ctx)
    assert "80/100" in analytics_res
    assert "Productivity Score" in analytics_res
    assert "Habit Score" in analytics_res


def test_planner_engine():
    """Verify that Planner parses context keys and formats schedule recommendations."""
    task_ctx = {
        "overdue": [{"title": "T1", "due_date": date.today()}],
        "all_pending": [{"title": "T2", "priority": 3, "due_date": date.today()}],
    }
    habit_ctx = {
        "streaks": [{"name": "H1", "streak": 5, "longest": 5}],
        "completed_today": [],
        "missed_today": ["H1"],
    }
    goal_ctx = {
        "closest_to_completion": {"title": "G1", "progress": 90.0},
    }
    expense_ctx = {
        "total_spent": 450.00,
        "monthly_budget": 500.00,
    }
    analytics_ctx = {}

    plan = Planner.generate_plan(
        task_ctx, habit_ctx, goal_ctx, expense_ctx, analytics_ctx
    )
    assert "Priorities" in plan["response"]
    assert "Suggested Schedule" in plan["response"]
    assert "T1" in plan["response"]
    assert "T2" in plan["response"]
    assert "H1" in plan["response"]
    assert "G1" in plan["response"]
    assert "Budget Warning" in plan["response"] or "Budget Alert" in plan["response"]

    assert any("G1" in r for r in plan["recommendations"])
    assert any("H1" in r for r in plan["recommendations"])
    assert any("T1" in a["label"] for a in plan["actions"])
    assert any("H1" in a["label"] for a in plan["actions"])


# =============================================================================
# Unit Tests: Database Tools Context Gathering
# =============================================================================


async def test_tools_empty_db(db_session: AsyncSession, test_user: User):
    """Verify tools handle empty database states without crashing."""
    tasks = await TaskTool.run(db_session, test_user.id)
    assert tasks["total_count"] == 0
    assert len(tasks["overdue"]) == 0
    assert len(tasks["all_pending"]) == 0

    goals = await GoalTool.run(db_session, test_user.id)
    assert goals["total_count"] == 0
    assert goals["closest_to_completion"] is None

    habits = await HabitTool.run(db_session, test_user.id)
    assert habits["total_count"] == 0
    assert len(habits["streaks"]) == 0

    expenses = await ExpenseTool.run(db_session, test_user.id)
    assert expenses["monthly_budget"] == 0.0
    assert expenses["total_spent"] == 0.0
    assert expenses["remaining_budget"] == 0.0
    assert expenses["highest_category"] is None

    analytics = await AnalyticsTool.run(db_session, test_user.id)
    assert analytics["productivity_score"] == 0.0
    assert analytics["overall_health_score"] == 0.0


async def test_tools_with_data(db_session: AsyncSession, test_user: User):
    """Verify tools fetch correct database values."""
    today = datetime.now(UTC).date()

    # 1. Seed Task
    db_session.add(
        AnalyticsTask(
            user_id=test_user.id,
            title="Pending Task",
            status=TaskStatus.PENDING,
            priority=3,
            due_date=today,
        )
    )
    db_session.add(
        AnalyticsTask(
            user_id=test_user.id,
            title="Overdue Task",
            status=TaskStatus.OVERDUE,
            priority=2,
            due_date=today - timedelta(days=1),
        )
    )

    # 2. Seed Goal
    db_session.add(
        AnalyticsGoal(
            user_id=test_user.id,
            title="Active Goal",
            status=GoalStatus.ACTIVE,
            progress_pct=75.0,
        )
    )

    # 3. Seed Habit
    db_session.add(
        AnalyticsHabit(
            user_id=test_user.id,
            name="Daily Coding",
            frequency=HabitFrequency.DAILY,
            completions=[today.isoformat()],
            current_streak=5,
            longest_streak=10,
            is_active=True,
            color="indigo",
        )
    )

    # 4. Seed Budget & Expense
    db_session.add(
        AnalyticsBudget(
            user_id=test_user.id,
            monthly_limit=1000.00,
            year=today.year,
            month=today.month,
        )
    )
    db_session.add(
        AnalyticsExpense(
            user_id=test_user.id,
            amount=150.00,
            category="Software",
            description="LifePilot Hosting",
            expense_date=today,
        )
    )

    await db_session.commit()

    # Verify Task Tool
    tasks = await TaskTool.run(db_session, test_user.id)
    assert tasks["total_count"] == 2
    assert any(t["title"] == "Overdue Task" for t in tasks["overdue"])
    assert any(t["title"] == "Pending Task" for t in tasks["all_pending"])

    # Verify Goal Tool
    goals = await GoalTool.run(db_session, test_user.id)
    assert goals["total_count"] == 1
    assert goals["closest_to_completion"]["title"] == "Active Goal"
    assert goals["closest_to_completion"]["progress"] == 75.0

    # Verify Habit Tool
    habits = await HabitTool.run(db_session, test_user.id)
    assert habits["total_count"] == 1
    assert "Daily Coding" in habits["completed_today"]
    assert habits["streaks"][0]["name"] == "Daily Coding"
    assert habits["streaks"][0]["streak"] == 5

    # Verify Expense Tool
    expenses = await ExpenseTool.run(db_session, test_user.id)
    assert expenses["monthly_budget"] == 1000.0
    assert expenses["total_spent"] == 150.0
    assert expenses["remaining_budget"] == 850.0
    assert expenses["highest_category"] == "Software"
    assert expenses["highest_category_amount"] == 150.0


# =============================================================================
# Integration Tests: API Endpoints
# =============================================================================


async def test_assistant_api_flow(
    client: AsyncClient, test_user: User, auth_headers: dict[str, str]
):
    """Test standard flow of chat messages, history pagination, and deletion."""
    conversation_id = uuid.uuid4()

    # 1. Submit query to Assistant chat
    payload = {
        "message": "hello assistant, what should i do today?",
        "conversation_id": str(conversation_id),
    }
    response = await client.post(
        "/api/v1/assistant/chat", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert "today" in res_json["data"]["response"].lower()
    assert len(res_json["data"]["recommendations"]) >= 1
    assert res_json["data"]["conversation_id"] == str(conversation_id)

    # 2. Get chat history logs
    history_res = await client.get("/api/v1/assistant/history", headers=auth_headers)
    assert history_res.status_code == 200
    hist_json = history_res.json()
    assert hist_json["success"] is True
    assert len(hist_json["data"]["items"]) == 1
    assert (
        hist_json["data"]["items"][0]["user_message"]
        == "hello assistant, what should i do today?"
    )
    assert hist_json["data"]["items"][0]["conversation_id"] == str(conversation_id)

    # 3. Clear history logs
    delete_res = await client.delete("/api/v1/assistant/history", headers=auth_headers)
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

    # 4. Get history again (should be empty)
    history_res_empty = await client.get(
        "/api/v1/assistant/history", headers=auth_headers
    )
    assert history_res_empty.status_code == 200
    assert len(history_res_empty.json()["data"]["items"]) == 0
