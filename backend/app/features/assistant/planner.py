"""Planner engine to compile priorities, schedule, and reminders from user data."""

from typing import Any


class Planner:
    """Planning engine producing schedules, priorities and warnings."""

    @staticmethod
    def generate_plan(
        task_ctx: dict[str, Any],
        habit_ctx: dict[str, Any],
        goal_ctx: dict[str, Any],
        expense_ctx: dict[str, Any],
        analytics_ctx: dict[str, Any],
    ) -> dict[str, Any]:
        # 1. Priorities
        priorities = []
        overdue_list = task_ctx.get("overdue", [])
        pending_list = task_ctx.get("all_pending", [])

        # Priority 1: High priority pending/overdue tasks
        for item in overdue_list:
            priorities.append(f"⚠️ Complete overdue: {item['title']}")
        for item in pending_list:
            if item["priority"] == 3:
                priorities.append(f"🔥 High Priority: {item['title']}")

        # Fallback to general pending tasks if we have fewer than 3
        if len(priorities) < 3:
            for item in pending_list:
                if (
                    item["priority"] == 2
                    and f"🔥 High Priority: {item['title']}" not in priorities
                ):
                    priorities.append(f"📋 Medium Priority: {item['title']}")

        # Trim to top 3 priorities
        top_priorities = priorities[:3]
        if not top_priorities:
            top_priorities = ["🌱 Set new priorities or tasks for today"]

        # 2. Suggested Schedule
        schedule_blocks = {
            "Morning (09:00 - 12:00)": [],
            "Afternoon (12:00 - 17:00)": [],
            "Evening (17:00 - 21:00)": [],
        }

        # Distribute pending tasks and habits into blocks
        tasks_to_schedule = [t["title"] for t in pending_list[:3]]
        habits_to_schedule = habit_ctx.get("missed_today", [])[:2]

        if habits_to_schedule:
            schedule_blocks["Morning (09:00 - 12:00)"].append(
                f"Habit: Complete '{habits_to_schedule[0]}'"
            )
        if len(tasks_to_schedule) > 0:
            schedule_blocks["Morning (09:00 - 12:00)"].append(
                f"Task: Focus on '{tasks_to_schedule[0]}'"
            )

        if len(tasks_to_schedule) > 1:
            schedule_blocks["Afternoon (12:00 - 17:00)"].append(
                f"Task: Progress on '{tasks_to_schedule[1]}'"
            )

        if len(habits_to_schedule) > 1:
            schedule_blocks["Evening (17:00 - 21:00)"].append(
                f"Habit: Close out '{habits_to_schedule[1]}'"
            )
        if len(tasks_to_schedule) > 2:
            schedule_blocks["Evening (17:00 - 21:00)"].append(
                f"Task: Review '{tasks_to_schedule[2]}'"
            )

        # Fallback for empty schedules
        for block, items in schedule_blocks.items():
            if not items:
                schedule_blocks[block] = ["Rest & Planning time"]

        # 3. Reminders & Warnings
        reminders = []
        if overdue_list:
            reminders.append(
                f"You have {len(overdue_list)} overdue task(s) needing immediate attention."
            )

        spent = expense_ctx.get("total_spent", 0.0)
        budget = expense_ctx.get("monthly_budget", 0.0)
        if budget > 0:
            util = spent / budget
            if util >= 0.9:
                reminders.append(
                    "🚨 Budget Alert: You have used over 90% of your monthly budget limit!"
                )
            elif util >= 0.7:
                reminders.append(
                    "⚠️ Budget Warning: Monthly spending has exceeded 70% of your budget."
                )

        closest_goal = goal_ctx.get("closest_to_completion")
        if closest_goal:
            reminders.append(
                f"🎯 Keep pushing \"{closest_goal['title']}\" (Progress: {closest_goal['progress']:.0f}%)."
            )

        if not reminders:
            reminders = ["No immediate reminders. Your cockpit is completely clear!"]

        # 4. Formatted Markdown Response
        response_md = "📅 **Today's Priorities & Schedule**\n\n"
        response_md += "### 🎯 Top Priorities\n"
        for p in top_priorities:
            response_md += f"- {p}\n"

        response_md += "\n### 🕒 Suggested Schedule\n"
        for block, items in schedule_blocks.items():
            response_md += f"**{block}**\n"
            for item in items:
                response_md += f"- {item}\n"
            response_md += "\n"

        response_md += "### 💡 Important Reminders\n"
        for r in reminders:
            response_md += f"- {r}\n"

        # 5. Extract Actions & Recommendations
        recommendations = []
        if closest_goal:
            recommendations.append(
                f"🎯 Push Goal: {closest_goal['title']} ({closest_goal['progress']:.0f}%)"
            )
        for streak in habit_ctx.get("streaks", [])[:2]:
            recommendations.append(
                f"🔥 Habit Streak: {streak['name']} ({streak['streak']}d)"
            )

        if budget > 0:
            pct = spent / budget * 100
            recommendations.append(f"💰 Spending: {pct:.0f}% of budget limit")

        actions = []
        for item in overdue_list[:2]:
            actions.append(
                {
                    "type": "task",
                    "label": f"Fix overdue: {item['title']}",
                    "payload": {"task_title": item["title"]},
                }
            )
        for habit_name in habits_to_schedule[:2]:
            actions.append(
                {
                    "type": "habit",
                    "label": f"Complete habit: {habit_name}",
                    "payload": {"habit_name": habit_name},
                }
            )

        return {
            "response": response_md,
            "recommendations": recommendations,
            "actions": actions,
        }
