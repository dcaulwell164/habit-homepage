from abc import ABC, abstractmethod

from habit_homepage.domain.habit import Habit


class HabitRepository(ABC):
    """
    Outbound port: the application depends on this interface.
    Infrastructure implements it.
    Follows hexagonal architecture - domain defines the contract.
    """

    @abstractmethod
    def get_by_id(self, habit_id: str) -> Habit | None:
        """Retrieve a habit by its ID."""
        ...

    @abstractmethod
    def get_all(self) -> list[Habit]:
        """Retrieve all habits."""
        ...

    @abstractmethod
    def save(self, habit: Habit) -> None:
        """Save or update a habit."""
        ...

    @abstractmethod
    def delete(self, habit_id: str) -> None:
        """Delete a habit by its ID."""
        ...
