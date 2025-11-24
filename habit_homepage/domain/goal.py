from dataclasses import dataclass
from datetime import date
from enum import Enum


class GoalComparison(Enum):
    """Comparison operator for goal evaluation."""

    GREATER_THAN_OR_EQUAL = ">="  # e.g., at least 10k steps
    LESS_THAN_OR_EQUAL = "<="  # e.g., resting HR below 60
    EQUAL = "=="  # e.g., exactly 8 hours sleep


class GoalPeriod(Enum):
    """Time period for goal evaluation."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class Goal:
    """
    Domain entity: represents a target/goal for a habit.
    Examples:
    - Walk 10,000 steps daily (>=)
    - Keep resting HR below 60 bpm (<=)
    - Read 30 pages per day (>=)

    Contains pure business data with no infrastructure dependencies.
    """

    id: str  # Unique identifier
    habit_id: str  # Reference to the habit this goal is for
    target_value: float  # The target value to achieve
    comparison: GoalComparison  # How to compare actual vs target
    period: GoalPeriod  # Daily, weekly, or monthly
    start_date: date  # When this goal becomes active
    end_date: date | None = None  # Optional end date (None = ongoing)
    description: str = ""  # Optional description

    def is_met(self, actual_value: float) -> bool:
        """Check if the goal is met given an actual value."""
        if self.comparison == GoalComparison.GREATER_THAN_OR_EQUAL:
            return actual_value >= self.target_value
        elif self.comparison == GoalComparison.LESS_THAN_OR_EQUAL:
            return actual_value <= self.target_value
        elif self.comparison == GoalComparison.EQUAL:
            return actual_value == self.target_value
        return False

    def is_active(self, check_date: date) -> bool:
        """Check if this goal is active on a given date."""
        if check_date < self.start_date:
            return False
        if self.end_date and check_date > self.end_date:
            return False
        return True
