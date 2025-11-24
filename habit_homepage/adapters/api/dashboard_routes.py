"""API routes for dashboard aggregated data."""

from datetime import date, timedelta

from fastapi import APIRouter, Query

from habit_homepage.application.analytics_service import AnalyticsService
from habit_homepage.application.daily_log_service import DailyLogService
from habit_homepage.application.goal_service import GoalService


def create_dashboard_router(
    log_service: DailyLogService,
    analytics_service: AnalyticsService,
    goal_service: GoalService,
) -> APIRouter:
    """Create dashboard router with dependency injection."""
    router = APIRouter()

    @router.get("/dashboard")
    def get_dashboard(
        target_date: date = Query(
            default_factory=date.today, description="Date for dashboard metrics"
        )
    ) -> dict:
        """
        Get aggregated dashboard metrics for a specific date.

        Returns:
            Comprehensive dashboard data including:
            - Daily summary (habits logged vs total)
            - Active goals and their progress
            - Current streaks for all habits
            - Weekly summary
            - Top performing habits

        This endpoint provides all key metrics needed for a frontend dashboard
        in a single request, reducing the number of API calls required.
        """
        # 1. Get daily summary
        daily_summary = analytics_service.get_daily_summary(target_date)

        # 2. Get all active goals for today
        all_goals = goal_service.get_all_goals()
        active_goals_progress = []

        for goal in all_goals:
            if goal.is_active(target_date):
                progress = goal_service.check_goal_progress(goal.id, target_date)
                active_goals_progress.append(
                    {
                        "goal_id": goal.id,
                        "habit_id": goal.habit_id,
                        "description": goal.description,
                        "target_value": goal.target_value,
                        "comparison": goal.comparison.value,
                        "period": goal.period.value,
                        "progress": progress,
                    }
                )

        # 3. Get current streaks for all logged habits
        current_streaks = []
        for habit_id in daily_summary["logged_habit_ids"]:
            streak = analytics_service.get_current_streak(habit_id, target_date)
            current_streaks.append({"habit_id": habit_id, "streak": streak})

        # Sort by streak length (descending)
        current_streaks.sort(key=lambda x: x["streak"], reverse=True)

        # 4. Get weekly summary (last 7 days)
        week_start = target_date - timedelta(days=6)
        week_end = target_date

        weekly_logs = log_service.get_by_date_range(week_start, week_end)
        weekly_habit_counts = {}

        for log in weekly_logs:
            for habit_id in log.entries.keys():
                weekly_habit_counts[habit_id] = (
                    weekly_habit_counts.get(habit_id, 0) + 1
                )

        # 5. Calculate top habits (most logged in past 7 days)
        top_habits = [
            {"habit_id": habit_id, "days_logged": count}
            for habit_id, count in sorted(
                weekly_habit_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]
        ]

        # 6. Goals met today count
        goals_met_today = sum(
            1
            for goal_progress in active_goals_progress
            if goal_progress["progress"].get("is_met") is True
        )

        return {
            "date": target_date.isoformat(),
            "daily_summary": {
                "total_habits": daily_summary["total_habits"],
                "logged_habits": daily_summary["logged_habits"],
                "completion_percentage": round(
                    (daily_summary["logged_habits"] / daily_summary["total_habits"])
                    * 100
                    if daily_summary["total_habits"] > 0
                    else 0,
                    1,
                ),
            },
            "goals": {
                "active_count": len(active_goals_progress),
                "met_today": goals_met_today,
                "details": active_goals_progress,
            },
            "streaks": {
                "current": current_streaks[:5],  # Top 5 current streaks
            },
            "weekly_summary": {
                "period": f"{week_start.isoformat()} to {week_end.isoformat()}",
                "top_habits": top_habits,
                "total_logs": sum(weekly_habit_counts.values()),
            },
        }

    @router.get("/dashboard/quick")
    def get_quick_dashboard() -> dict:
        """
        Get quick dashboard metrics (minimal data for fast loading).

        Returns only the most essential metrics for today.
        """
        target_date = date.today()

        # Get today's summary
        daily_summary = analytics_service.get_daily_summary(target_date)

        # Get active goals count
        all_goals = goal_service.get_all_goals()
        active_goals_count = sum(
            1 for goal in all_goals if goal.is_active(target_date)
        )

        # Get goals met today
        goals_met_count = 0
        for goal in all_goals:
            if goal.is_active(target_date):
                progress = goal_service.check_goal_progress(goal.id, target_date)
                if progress.get("is_met") is True:
                    goals_met_count += 1

        return {
            "date": target_date.isoformat(),
            "habits_logged": daily_summary["logged_habits"],
            "total_habits": daily_summary["total_habits"],
            "completion_percentage": round(
                (daily_summary["logged_habits"] / daily_summary["total_habits"]) * 100
                if daily_summary["total_habits"] > 0
                else 0,
                1,
            ),
            "active_goals": active_goals_count,
            "goals_met_today": goals_met_count,
        }

    return router
