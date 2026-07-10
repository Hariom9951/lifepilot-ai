"""Orchestrator combining intent classification, tool calls, planner and persistence."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.assistant.intent import AssistantIntent, IntentClassifier
from app.features.assistant.planner import Planner
from app.features.assistant.prompts import ResponseTemplates
from app.features.assistant.repository import AssistantRepository
from app.features.assistant.schemas import ChatAction, ChatResponse
from app.features.assistant.tools import (
    AnalyticsTool,
    ExpenseTool,
    GoalTool,
    HabitTool,
    TaskTool,
)
from app.features.rag.services import RAGService


class AssistantOrchestrator:
    """Coordinates assistant execution flow and persists histories."""

    @classmethod
    async def process_chat(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        full_name: str,
        message: str,
        conversation_id: uuid.UUID | None = None,
    ) -> ChatResponse:
        # Resolve conversation_id
        session_id = conversation_id or uuid.uuid4()

        # 1. Classify Intent
        intent = IntentClassifier.classify(message)

        # 2. Gather All Context (Parallel-safe queries)
        task_ctx = await TaskTool.run(db, user_id)
        habit_ctx = await HabitTool.run(db, user_id)
        goal_ctx = await GoalTool.run(db, user_id)
        expense_ctx = await ExpenseTool.run(db, user_id)
        analytics_ctx = await AnalyticsTool.run(db, user_id)

        response_md = ""
        recommendations: list[str] = []
        actions: list[dict[str, Any]] = []

        # 3. Retrieve Relevant Context (RAG Search)
        rag_matches = await RAGService.search_knowledge_base(
            db=db,
            user_id=user_id,
            query=message,
            limit=3,
            score_threshold=0.35,
        )

        if rag_matches:
            response_md = (
                "🔍 **Here is what I found in your knowledge base and notes:**\n\n"
            )
            for match in rag_matches:
                doc_name = match.get("document") or "Note"
                score = match.get("score") or 0.0
                content = match.get("content") or ""
                response_md += (
                    f"📄 **Source:** `{doc_name}` (Similarity: {score:.0%})\n"
                )
                response_md += f"> {content.strip()}\n\n"

                # Add action card metadata
                meta = match.get("metadata") or {}
                if "document_id" in meta and meta["document_id"]:
                    actions.append(
                        {
                            "type": "document",
                            "label": f"Open {doc_name}",
                            "payload": {"document_id": meta["document_id"]},
                        }
                    )
                elif "memory_id" in meta and meta["memory_id"]:
                    actions.append(
                        {
                            "type": "memory",
                            "label": "Open memory details",
                            "payload": {"memory_id": meta["memory_id"]},
                        }
                    )
            recommendations.append(
                "📚 Review your knowledge base to add more documents"
            )
        else:
            # 4. Route by Intent (Fallback to standard pipeline)
            if intent == AssistantIntent.GREETING:
                response_md = ResponseTemplates.greeting(full_name)
                # Default recommendations
                if habit_ctx.get("streaks"):
                    best = max(habit_ctx["streaks"], key=lambda h: h["streak"])
                    recommendations.append(
                        f"🔥 Best streak: {best['name']} ({best['streak']}d)"
                    )
                if goal_ctx.get("closest_to_completion"):
                    recommendations.append(
                        f"🎯 Close goal: {goal_ctx['closest_to_completion']['title']}"
                    )

            elif intent in (
                AssistantIntent.PLANNING,
                AssistantIntent.RECOMMENDATION,
            ):
                plan_res = Planner.generate_plan(
                    task_ctx, habit_ctx, goal_ctx, expense_ctx, analytics_ctx
                )
                response_md = plan_res["response"]
                recommendations = plan_res["recommendations"]
                actions = plan_res["actions"]

            elif intent == AssistantIntent.TASK:
                response_md = ResponseTemplates.task(task_ctx)
                # Suggest completing top pending/overdue task
                overdue = task_ctx.get("overdue")
                pending = task_ctx.get("all_pending")
                if overdue:
                    actions.append(
                        {
                            "type": "task",
                            "label": f"Complete overdue: {overdue[0]['title']}",
                            "payload": {"task_title": overdue[0]["title"]},
                        }
                    )
                elif pending:
                    actions.append(
                        {
                            "type": "task",
                            "label": f"Start task: {pending[0]['title']}",
                            "payload": {"task_title": pending[0]["title"]},
                        }
                    )

            elif intent == AssistantIntent.GOAL:
                response_md = ResponseTemplates.goal(goal_ctx)
                closest = goal_ctx.get("closest_to_completion")
                if closest:
                    recommendations.append(
                        f"🎯 Closest: {closest['title']} ({closest['progress']:.0f}%)"
                    )
                    actions.append(
                        {
                            "type": "goal",
                            "label": f"Track progress: {closest['title']}",
                            "payload": {"goal_title": closest["title"]},
                        }
                    )

            elif intent == AssistantIntent.HABIT:
                response_md = ResponseTemplates.habit(habit_ctx)
                missed = habit_ctx.get("missed_today", [])
                for m in missed[:2]:
                    actions.append(
                        {
                            "type": "habit",
                            "label": f"Complete habit: {m}",
                            "payload": {"habit_name": m},
                        }
                    )
                if habit_ctx.get("streaks"):
                    best = max(habit_ctx["streaks"], key=lambda h: h["streak"])
                    recommendations.append(
                        f"🔥 Streak: {best['name']} ({best['streak']}d)"
                    )

            elif intent == AssistantIntent.EXPENSE:
                response_md = ResponseTemplates.expense(expense_ctx)
                spent = expense_ctx.get("total_spent", 0.0)
                budget = expense_ctx.get("monthly_budget", 0.0)
                if budget > 0:
                    util = spent / budget * 100
                    recommendations.append(f"💰 Budget Used: {util:.0f}%")
                    if util >= 0.9:
                        actions.append(
                            {
                                "type": "expense",
                                "label": "Review budget rules",
                                "payload": {"spent": spent, "budget": budget},
                            }
                        )
                if expense_ctx.get("highest_category"):
                    recommendations.append(
                        f"📊 Top spent category: {expense_ctx['highest_category']}"
                    )

            elif intent == AssistantIntent.ANALYTICS:
                response_md = ResponseTemplates.analytics(analytics_ctx)
                health = analytics_ctx.get("overall_health_score", 0.0)
                recommendations.append(f"⚡ Performance Health: {health:.0f}/100")
                if health < 50:
                    actions.append(
                        {
                            "type": "productivity",
                            "label": "Plan priority schedule",
                            "payload": {},
                        }
                    )

            else:
                response_md = ResponseTemplates.general()

        # Fallback recommendations if empty
        if not recommendations:
            recommendations.append("⚡ Use dashboard to track your performance")

        # 4. Convert actions array to typed ChatAction schemas
        typed_actions = [
            ChatAction(type=act["type"], label=act["label"], payload=act["payload"])
            for act in actions
        ]

        # 5. Persist to PostgreSQL Database
        await AssistantRepository.create_chat_exchange(
            db=db,
            user_id=user_id,
            conversation_id=session_id,
            user_message=message,
            assistant_message=response_md,
            recommendations=recommendations,
            actions=actions,  # Stored as json list
        )

        return ChatResponse(
            response=response_md,
            recommendations=recommendations,
            actions=typed_actions,
            conversation_id=session_id,
        )
