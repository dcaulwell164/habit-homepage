from datetime import date, timedelta

from habit_homepage.config.logging import get_logger
from habit_homepage.ports.repositories.daily_log_repo import DailyLogRepository
from habit_homepage.ports.repositories.habit_repo import HabitRepository

logger = get_logger(__name__)


class AnalyticsService:
    """
    Application service for habit analytics and insights.

    Provides statistics, trends, and streak tracking for habits.

    Follows hexagonal architecture:
    - Application layer orchestrates analytics calculations
    - Depends on ports (interfaces), not concrete implementations
    """

    def __init__(self, log_repo: DailyLogRepository, habit_repo: HabitRepository):
        self.log_repo = log_repo
        self.habit_repo = habit_repo

    def get_habit_statistics(
        self, habit_id: str, start_date: date, end_date: date
    ) -> dict[str, float | int]:
        """
        Calculate statistics for a habit over a date range.

        Returns:
            dict with min, max, average, total, count, days_logged
        """
        # Verify habit exists
        habit = self.habit_repo.get_by_id(habit_id)
        if not habit:
            raise ValueError(f"Habit '{habit_id}' not found")

        entries = self.log_repo.get_entries_by_habit(habit_id, start_date, end_date)

        if not entries:
            return {
                "min": 0.0,
                "max": 0.0,
                "average": 0.0,
                "total": 0.0,
                "count": 0,
                "days_logged": 0,
                "days_in_range": (end_date - start_date).days + 1,
            }

        values = [e.value for e in entries]
        return {
            "min": min(values),
            "max": max(values),
            "average": sum(values) / len(values),
            "total": sum(values),
            "count": len(entries),
            "days_logged": len(entries),
            "days_in_range": (end_date - start_date).days + 1,
        }

    def get_current_streak(self, habit_id: str, as_of_date: date | None = None) -> int:
        """
        Calculate the current streak for a habit.

        A streak is the number of consecutive days the habit was logged
        going backwards from as_of_date (or today).

        Returns:
            Number of consecutive days with entries
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Verify habit exists
        habit = self.habit_repo.get_by_id(habit_id)
        if not habit:
            raise ValueError(f"Habit '{habit_id}' not found")

        streak = 0
        check_date = as_of_date

        # Look back up to 365 days (reasonable limit)
        for _ in range(365):
            entries = self.log_repo.get_entries_by_habit(
                habit_id, check_date, check_date
            )
            if not entries:
                break
            streak += 1
            check_date = check_date - timedelta(days=1)

        return streak

    def get_longest_streak(
        self, habit_id: str, start_date: date, end_date: date
    ) -> dict[str, int | str | None]:
        """
        Find the longest streak within a date range.

        Returns:
            dict with:
            - length: number of days
            - start_date: when streak started (ISO string)
            - end_date: when streak ended (ISO string)
        """
        # Verify habit exists
        habit = self.habit_repo.get_by_id(habit_id)
        if not habit:
            raise ValueError(f"Habit '{habit_id}' not found")

        entries = self.log_repo.get_entries_by_habit(habit_id, start_date, end_date)

        if not entries:
            return {"length": 0, "start_date": None, "end_date": None}

        # Create a set of dates with entries for fast lookup
        logged_dates = {e.date for e in entries}

        max_streak = 0
        max_start = None
        max_end = None

        current_streak = 0
        current_start = None

        # Iterate through all dates in range
        check_date = start_date
        while check_date <= end_date:
            if check_date in logged_dates:
                if current_streak == 0:
                    current_start = check_date
                current_streak += 1

                # Update max if current is longer
                if current_streak > max_streak:
                    max_streak = current_streak
                    max_start = current_start
                    max_end = check_date
            else:
                # Streak broken
                current_streak = 0
                current_start = None

            check_date = check_date + timedelta(days=1)

        return {
            "length": max_streak,
            "start_date": max_start.isoformat() if max_start else None,
            "end_date": max_end.isoformat() if max_end else None,
        }

    def get_calendar_data(
        self, habit_id: str, year: int, month: int
    ) -> list[dict[str, str | float]]:
        """
        Get habit data for a calendar month (useful for heatmaps).

        Returns:
            List of dicts with date and value for each day in the month
        """
        # Verify habit exists
        habit = self.habit_repo.get_by_id(habit_id)
        if not habit:
            raise ValueError(f"Habit '{habit_id}' not found")

        # Get first and last day of month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year, 12, 31)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        entries = self.log_repo.get_entries_by_habit(habit_id, start_date, end_date)

        # Create lookup dict
        entry_map = {e.date: e.value for e in entries}

        # Build result for all days in month
        result = []
        check_date = start_date
        while check_date <= end_date:
            result.append(
                {
                    "date": check_date.isoformat(),
                    "value": entry_map.get(check_date, 0.0),
                }
            )
            check_date = check_date + timedelta(days=1)

        return result

    def get_daily_summary(self, check_date: date) -> dict[str, int | list[str]]:
        """
        Get a summary of all habits for a specific day.

        Returns:
            dict with:
            - total_habits: total number of habits defined
            - logged_habits: number of habits logged
            - logged_habit_ids: list of habit IDs that were logged
        """
        all_habits = self.habit_repo.get_all()
        log = self.log_repo.get_by_date(check_date)

        logged_habit_ids = []
        if log:
            logged_habit_ids = list(log.entries.keys())

        return {
            "total_habits": len(all_habits),
            "logged_habits": len(logged_habit_ids),
            "logged_habit_ids": logged_habit_ids,
        }

    def get_habit_trend(
        self, habit_id: str, start_date: date, end_date: date
    ) -> list[dict[str, str | float]]:
        """
        Get time series data for a habit (useful for line charts).

        Returns:
            List of dicts with date and value for each day in range
        """
        # Verify habit exists
        habit = self.habit_repo.get_by_id(habit_id)
        if not habit:
            raise ValueError(f"Habit '{habit_id}' not found")

        entries = self.log_repo.get_entries_by_habit(habit_id, start_date, end_date)

        # Create lookup dict
        entry_map = {e.date: e.value for e in entries}

        # Build result for all days in range
        result = []
        check_date = start_date
        while check_date <= end_date:
            result.append(
                {
                    "date": check_date.isoformat(),
                    "value": entry_map.get(check_date, 0.0),
                }
            )
            check_date = check_date + timedelta(days=1)

        return result

    def get_completion_rate(
        self, habit_id: str, start_date: date, end_date: date, threshold: float = 0.0
    ) -> dict[str, float | int]:
        """
        Calculate completion rate for a habit.

        A day is considered "complete" if the value is > threshold.

        Returns:
            dict with:
            - completion_rate: percentage (0-100)
            - days_completed: number of days above threshold
            - total_days: total days in range
        """
        # Verify habit exists
        habit = self.habit_repo.get_by_id(habit_id)
        if not habit:
            raise ValueError(f"Habit '{habit_id}' not found")

        entries = self.log_repo.get_entries_by_habit(habit_id, start_date, end_date)

        total_days = (end_date - start_date).days + 1
        days_completed = sum(1 for e in entries if e.value > threshold)

        completion_rate = (days_completed / total_days * 100) if total_days > 0 else 0.0

        return {
            "completion_rate": round(completion_rate, 2),
            "days_completed": days_completed,
            "total_days": total_days,
        }
