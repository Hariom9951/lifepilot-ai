"""Response templates for generating markdown messages based on extracted context."""

from typing import Any


class ResponseTemplates:
    """Contains formatters for structured rule-based responses."""

    @staticmethod
    def greeting(full_name: str) -> str:
        first_name = full_name.split()[0] if full_name else "there"
        return (
            f"Hello, {first_name}! 👋 I am your **LifePilot AI Assistant**.\n\n"
            "I have real-time access to your tasks, habits, goals, and budgets. "
            "Here are a few things you can ask me:\n"
            '- *"What should I do today?"*\n'
            '- *"How is my budget?"*\n'
            '- *"Show my habits."*\n'
            '- *"Summarize my productivity."*\n\n'
            "How can I help you navigate your day?"
        )

    @staticmethod
    def task(context: dict[str, Any]) -> str:
        total = context["total_count"]
        overdue = context["overdue"]
        pending = context["all_pending"]
        completed = context["completed_today"]

        if total == 0:
            return (
                "📅 **Tasks & Schedule**\n\n"
                "Your task list is completely empty! You can start by creating tasks in your dashboard."
            )

        reply = "📅 **Tasks & Schedule**\n\n"
        reply += f"You have **{len(pending)}** pending tasks. "
        if completed:
            reply += f"Great job on completing **{len(completed)}** task(s) today!\n"
        else:
            reply += "No tasks completed yet today.\n"

        if overdue:
            reply += f"\n### ⚠️ Overdue Items ({len(overdue)})\n"
            for t in overdue:
                reply += f"- **{t['title']}** (Due: {t['due_date']})\n"

        if pending:
            reply += f"\n### 📋 Pending Items ({len(pending)})\n"
            for t in pending:
                due = f" (Due: {t['due_date']})" if t["due_date"] else ""
                priority_emoji = (
                    "🔴" if t["priority"] == 3 else "🟡" if t["priority"] == 2 else "🟢"
                )
                reply += f"- {priority_emoji} **{t['title']}**{due}\n"

        return reply

    @staticmethod
    def goal(context: dict[str, Any]) -> str:
        active = context["active"]
        completed = context["completed"]
        closest = context["closest_to_completion"]

        if not active and not completed:
            return (
                "🎯 **Goal Progress**\n\n"
                "You haven't set any goals yet. Defining clear goals helps align your day-to-day work!"
            )

        reply = "🎯 **Goal Progress**\n\n"
        if closest:
            reply += (
                f"You are closest to achieving **\"{closest['title']}\"** which is currently at "
                f"**{closest['progress']:.0f}%** completion.\n\n"
            )

        if active:
            reply += "### 🏃 Active Goals\n"
            for g in active:
                reply += f"- **{g['title']}** — {g['progress']:.0f}% complete\n"

        if completed:
            reply += "\n### 🏆 Completed Goals\n"
            for g in completed:
                reply += f"- **{g}** (100% complete) 🎉\n"

        return reply

    @staticmethod
    def habit(context: dict[str, Any]) -> str:
        streaks = context["streaks"]
        completed = context["completed_today"]
        missed = context["missed_today"]

        if not streaks:
            return (
                "🔥 **Habit Streaks**\n\n"
                "You haven't set up any active habits. Build positive routines by adding habits."
            )

        reply = "🔥 **Habit Streaks & Checklist**\n\n"

        if completed:
            reply += f"Nice! You've checked off **{len(completed)}** habit(s) today: {', '.join([f'*{h}*' for h in completed])}.\n"

        if missed:
            reply += f"You have **{len(missed)}** active habit(s) remaining for today: {', '.join([f'**{h}**' for h in missed])}.\n"

        reply += "\n### 📈 Active Habits Streaks\n"
        for h in streaks:
            reply += f"- **{h['name']}** — Streak: **{h['streak']} days** (Longest: {h['longest']}d)\n"

        return reply

    @staticmethod
    def expense(context: dict[str, Any]) -> str:
        spent = context["total_spent"]
        budget = context["monthly_budget"]
        remaining = context["remaining_budget"]
        highest_cat = context["highest_category"]

        if budget == 0.0 and spent == 0.0:
            return (
                "💰 **Budget & Expenses**\n\n"
                "No budget limit or expenses recorded for this month. Set a budget in your settings."
            )

        reply = "💰 **Budget & Expense Summary**\n\n"
        reply += f"- **Spent this month**: ${spent:.2f}\n"
        if budget > 0:
            pct = (spent / budget) * 100
            reply += f"- **Monthly Budget**: ${budget:.2f} ({pct:.1f}% utilized)\n"
            reply += f"- **Remaining**: ${remaining:.2f}\n"
        else:
            reply += "- **Monthly Budget**: Not set\n"

        if highest_cat:
            reply += f"- **Highest Category**: **{highest_cat}** (${context['highest_category_amount']:.2f})\n"

        return reply

    @staticmethod
    def analytics(context: dict[str, Any]) -> str:
        prod = context["productivity_score"]
        habit = context["habit_score"]
        goal = context["goal_score"]
        health = context["overall_health_score"]

        reply = "⚡ **Productivity Summary**\n\n"
        reply += f"Your overall health score is **{health:.0f}/100**.\n\n"
        reply += "### 📊 Performance Breakdown\n"
        reply += (
            f"- **Productivity Score**: **{prod:.0f}/100** (Tasks + Goal Progress)\n"
        )
        reply += f"- **Habit Score**: **{habit:.0f}/100** (7-day streaks tracking)\n"
        reply += f"- **Goal Progress**: **{goal:.0f}/100** (Completion rate)\n\n"

        if health >= 80:
            reply += "🚀 **Verdict**: Outstanding! Your daily patterns show high discipline. Keep it up!"
        elif health >= 50:
            reply += "📈 **Verdict**: Good progress, but there's room to grow. Rescheduling overdue tasks will boost your scores."
        else:
            reply += "🎯 **Verdict**: Focus on completing one high-priority task and your daily habits to build momentum."

        return reply

    @staticmethod
    def general() -> str:
        return (
            "🤖 **LifePilot Assistant**\n\n"
            "I couldn't identify a specific category in your question. "
            "I can help you monitor your productivity, tasks, habits, and budgets. "
            "Please try asking something like:\n"
            '- *"What should I prioritize today?"*\n'
            '- *"How are my habits looking?"*\n'
            '- *"Am I on budget?"*\n'
            '- *"Which goal is closest to completion?"*'
        )
