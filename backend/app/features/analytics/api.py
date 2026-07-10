"""Analytics API — all 5 analytics endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses.schemas import SuccessResponse
from app.core.database.session import get_db_session
from app.features.analytics.dependencies import get_current_user
from app.features.analytics.schemas import (
    DashboardResponse,
    ExpenseAnalyticsResponse,
    GoalAnalyticsResponse,
    HabitAnalyticsResponse,
    TaskAnalyticsResponse,
)
from app.features.analytics.service import AnalyticsService
from app.features.auth.models import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/dashboard",
    response_model=SuccessResponse[DashboardResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve full holistic analytics dashboard composite",
)
async def get_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[DashboardResponse]:
    """
    Returns a single composite payload covering productivity score, task
    summary, habit metrics, goal overview, expense snapshot, weekly trend
    data and rule-based AI insights.  Result is Redis-cached for 60 s.
    """
    data = await AnalyticsService.get_dashboard(db, current_user.id)
    return SuccessResponse(
        message="Analytics dashboard computed successfully.",
        data=data,
    )


@router.get(
    "/tasks",
    response_model=SuccessResponse[TaskAnalyticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve detailed task analytics breakdown",
)
async def get_task_analytics(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[TaskAnalyticsResponse]:
    """
    Provides completion rates, overdue analysis, priority distribution,
    category breakdown and monthly trend data for all user tasks.
    """
    data = await AnalyticsService.get_task_analytics(db, current_user.id)
    return SuccessResponse(
        message="Task analytics retrieved successfully.",
        data=data,
    )


@router.get(
    "/habits",
    response_model=SuccessResponse[HabitAnalyticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve habit analytics with streaks and heatmap",
)
async def get_habit_analytics(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[HabitAnalyticsResponse]:
    """
    Returns streak data, 7-day completion rates, per-habit heatmaps and
    overall weekly habit consistency scores.
    """
    data = await AnalyticsService.get_habit_analytics(db, current_user.id)
    return SuccessResponse(
        message="Habit analytics retrieved successfully.",
        data=data,
    )


@router.get(
    "/goals",
    response_model=SuccessResponse[GoalAnalyticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve goal progress and milestone analytics",
)
async def get_goal_analytics(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[GoalAnalyticsResponse]:
    """
    Returns per-goal progress, status breakdown, quarterly goal count and
    the goal closest to completion.
    """
    data = await AnalyticsService.get_goal_analytics(db, current_user.id)
    return SuccessResponse(
        message="Goal analytics retrieved successfully.",
        data=data,
    )


@router.get(
    "/expenses",
    response_model=SuccessResponse[ExpenseAnalyticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve expense analytics with budget utilisation",
)
async def get_expense_analytics(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SuccessResponse[ExpenseAnalyticsResponse]:
    """
    Returns current-month spending totals, category distribution, monthly
    trend and budget utilisation metrics.
    """
    data = await AnalyticsService.get_expense_analytics(db, current_user.id)
    return SuccessResponse(
        message="Expense analytics retrieved successfully.",
        data=data,
    )
