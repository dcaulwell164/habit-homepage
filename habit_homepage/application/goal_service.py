from datetime import date

from habit_homepage.config.logging import get_logger
from habit_homepage.domain.exceptions import (
    DuplicateResourceError,
    GoalNotFoundError,
    HabitNotFoundError,
    InvalidGoalConfigError,
)
from habit_homepage.domain.goal import Goal, GoalComparison, GoalPeriod
from habit_homepage.ports.repositories.daily_log_repo import DailyLogRepository
from habit_homepage.ports.repositories.goal_repo import GoalRepository
from habit_homepage.ports.repositories.habit_repo import HabitRepository

logger = get_logger(__name__)


class GoalService:
    """
    Application service for goal management.

    Business rules:
    - Goals are user-defined targets for habits
    - Goals can be daily, weekly, or monthly
    - Goals have start/end dates for time-bound tracking
    - Goal progress is calculated from daily log entries

    Follows hexagonal architecture:
    - Application layer orchestrates domain entities
    - Depends on ports (interfaces), not concrete implementations
    """

    def __init__(
        self,
        goal_repo: GoalRepository,
        habit_repo: HabitRepository,
        log_repo: DailyLogRepository,
    ):
        self.goal_repo = goal_repo
        self.habit_repo = habit_repo
        self.log_repo = log_repo

    def create_goal(
        self,
        goal_id: str,
        habit_id: str,
        target_value: float,
        comparison: GoalComparison,
        period: GoalPeriod,
        start_date: date,
        end_date: date | None = None,
        description: str = "",
    ) -> Goal:
        """
        Create a new goal.

        Validates that:
        - The habit exists
        - The goal ID is unique
        - Start date is before end date (if provided)
        """
        # Verify habit exists
        habit = self.habit_repo.get_by_id(habit_id)
        if not habit:
            raise HabitNotFoundError(habit_id)

        # Verify goal ID is unique
        existing_goal = self.goal_repo.get_by_id(goal_id)
        if existing_goal:
            raise DuplicateResourceError("Goal", goal_id)

        # Validate dates
        if end_date and start_date > end_date:
            raise InvalidGoalConfigError("Start date must be before end date")

        goal = Goal(
            id=goal_id,
            habit_id=habit_id,
            target_value=target_value,
            comparison=comparison,
            period=period,
            start_date=start_date,
            end_date=end_date,
            description=description,
        )

        self.goal_repo.save(goal)
        logger.info(f"Created goal: {goal_id} for habit {habit_id}")
        return goal

    def update_goal(
        self,
        goal_id: str,
        target_value: float | None = None,
        comparison: GoalComparison | None = None,
        end_date: date | None = None,
        description: str | None = None,
    ) -> Goal:
        """
        Update an existing goal.

        Only updates fields that are provided (not None).
        """
        goal = self.goal_repo.get_by_id(goal_id)
        if not goal:
            raise GoalNotFoundError(goal_id)

        # Update only provided fields
        if target_value is not None:
            goal.target_value = target_value
        if comparison is not None:
            goal.comparison = comparison
        if end_date is not None:
            if end_date < goal.start_date:
                raise ValueError("End date must be after start date")
            goal.end_date = end_date
        if description is not None:
            goal.description = description

        self.goal_repo.save(goal)
        logger.info(f"Updated goal: {goal_id}")
        return goal

    def delete_goal(self, goal_id: str) -> None:
        """Delete a goal."""
        goal = self.goal_repo.get_by_id(goal_id)
        if not goal:
            raise GoalNotFoundError(goal_id)

        self.goal_repo.delete(goal_id)
        logger.info(f"Deleted goal: {goal_id}")

    def get_goal(self, goal_id: str) -> Goal | None:
        """Retrieve a goal by ID."""
        return self.goal_repo.get_by_id(goal_id)

    def get_goals_for_habit(self, habit_id: str) -> list[Goal]:
        """Get all goals for a specific habit."""
        return self.goal_repo.get_by_habit(habit_id)

    def get_all_goals(self) -> list[Goal]:
        """Get all goals."""
        return self.goal_repo.get_all()

    def get_active_goals(self, habit_id: str, check_date: date) -> list[Goal]:
        """Get all active goals for a habit on a specific date."""
        return self.goal_repo.get_active_goals(habit_id, check_date)

    def check_goal_progress(
        self, goal_id: str, check_date: date
    ) -> dict[str, bool | float | None]:
        """
        Check if a goal is met for a specific date/period.

        Returns:
            dict with:
            - is_active: bool
            - actual_value: float | None
            - is_met: bool (only if active and value available)
        """
        goal = self.goal_repo.get_by_id(goal_id)
        if not goal:
            raise GoalNotFoundError(goal_id)

        # Check if goal is active on this date
        if not goal.is_active(check_date):
            return {"is_active": False, "actual_value": None}

        # Get actual value based on period
        actual_value = self._get_actual_value(goal, check_date)

        if actual_value is None:
            return {"is_active": True, "actual_value": None}

        return {
            "is_active": True,
            "actual_value": actual_value,
            "is_met": goal.is_met(actual_value),
            "target_value": goal.target_value,
            "comparison": goal.comparison.value,
        }

    def _get_actual_value(self, goal: Goal, check_date: date) -> float | None:
        """
        Get the actual value for a goal based on its period.

        For DAILY: returns value from that single day
        For WEEKLY: returns sum of values for the week
        For MONTHLY: returns sum of values for the month
        """
        from datetime import timedelta

        if goal.period == GoalPeriod.DAILY:
            # Get single day's value
            entries = self.log_repo.get_entries_by_habit(
                goal.habit_id, check_date, check_date
            )
            if not entries:
                return None
            return sum(e.value for e in entries)

        elif goal.period == GoalPeriod.WEEKLY:
            # Get week's values (Monday to Sunday)
            # Find Monday of the week
            days_since_monday = check_date.weekday()
            week_start = check_date - timedelta(days=days_since_monday)
            week_end = week_start + timedelta(days=6)

            entries = self.log_repo.get_entries_by_habit(
                goal.habit_id, week_start, week_end
            )
            if not entries:
                return None
            return sum(e.value for e in entries)

        elif goal.period == GoalPeriod.MONTHLY:
            # Get month's values
            month_start = check_date.replace(day=1)
            # Get last day of month
            if check_date.month == 12:
                month_end = check_date.replace(day=31)
            else:
                next_month = check_date.replace(month=check_date.month + 1, day=1)
                month_end = next_month - timedelta(days=1)

            entries = self.log_repo.get_entries_by_habit(
                goal.habit_id, month_start, month_end
            )
            if not entries:
                return None
            return sum(e.value for e in entries)

        return None
