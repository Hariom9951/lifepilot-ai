"""Intent classification layer for assistant messages."""

import enum


class AssistantIntent(enum.StrEnum):
    """Supported user message intents."""

    TASK = "task"
    GOAL = "goal"
    HABIT = "habit"
    EXPENSE = "expense"
    ANALYTICS = "analytics"
    GREETING = "greeting"
    PLANNING = "planning"
    RECOMMENDATION = "recommendation"
    GENERAL = "general"


class IntentClassifier:
    """Lightweight keyword-based pattern classifier for detecting user intents."""

    @staticmethod
    def classify(message: str) -> AssistantIntent:
        msg = message.strip().lower()

        # 1. Greetings
        greetings = [
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "greetings",
        ]
        if any(g in msg for g in greetings) and len(msg.split()) <= 3:
            return AssistantIntent.GREETING

        # 2. Planning (prioritization, schedules, what to do)
        planning_keywords = [
            "what should i do",
            "prioritize",
            "what to do",
            "today's priorities",
            "priority",
            "schedule",
            "suggested schedule",
        ]
        if any(k in msg for k in planning_keywords):
            return AssistantIntent.PLANNING

        # 3. Recommendations
        recommendation_keywords = [
            "recommend",
            "suggest",
            "how to improve",
            "improvement",
            "improve",
            "tips",
        ]
        if any(k in msg for k in recommendation_keywords):
            return AssistantIntent.RECOMMENDATION

        # 4. Analytics & Productivity
        analytics_keywords = [
            "analytics",
            "productivity",
            "score",
            "health",
            "performance",
            "summarize my",
        ]
        if any(k in msg for k in analytics_keywords):
            return AssistantIntent.ANALYTICS

        # 5. Expenses / Budget
        expense_keywords = [
            "expense",
            "spend",
            "money",
            "budget",
            "cost",
            "price",
            "transaction",
            "how much",
        ]
        if any(k in msg for k in expense_keywords):
            return AssistantIntent.EXPENSE

        # 6. Goals
        goal_keywords = [
            "goal",
            "target",
            "milestone",
            "closest to completing",
            "closest goal",
        ]
        if any(k in msg for k in goal_keywords):
            return AssistantIntent.GOAL

        # 7. Habits
        habit_keywords = ["habit", "streak", "routine", "missing", "daily checklist"]
        if any(k in msg for k in habit_keywords):
            return AssistantIntent.HABIT

        # 8. Task specifics (fallback from planning if query is simple, e.g. "show tasks")
        task_keywords = ["task", "todo", "to-do", "pending items"]
        if any(k in msg for k in task_keywords):
            return AssistantIntent.TASK

        return AssistantIntent.GENERAL
