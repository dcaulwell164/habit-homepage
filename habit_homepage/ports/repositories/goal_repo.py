from abc import ABC, abstractmethod
from datetime import date

from habit_homepage.domain.goal import Goal


class GoalRepository(ABC):
    """
    Outbound port: the application depends on this interface.
    Infrastructure implements it.
    """

    @abstractmethod
    def get_by_id(self, goal_id: str) -> Goal | None:
        """Retrieve a goal by its ID."""
        ...

    @abstractmethod
    def get_all(self) -> list[Goal]:
        """Retrieve all goals."""
        ...

    @abstractmethod
    def get_by_habit(self, habit_id: str) -> list[Goal]:
        """Retrieve all goals for a specific habit."""
        ...

    @abstractmethod
    def get_active_goals(self, habit_id: str, check_date: date) -> list[Goal]:
        """Retrieve all active goals for a habit on a specific date."""
        ...

    @abstractmethod
    def save(self, goal: Goal) -> None:
        """Save or update a goal."""
        ...

    @abstractmethod
    def delete(self, goal_id: str) -> None:
        """Delete a goal by its ID."""
        ...
