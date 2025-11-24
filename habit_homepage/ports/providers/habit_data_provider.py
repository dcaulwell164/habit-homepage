from abc import ABC, abstractmethod

from habit_homepage.domain.habit import Habit


class HabitDataProvider(ABC):
    """
    Outbound port: interface for fetching habit data from external sources.
    This is a key port for automatic habit tracking.

    Follows hexagonal architecture:
    - Domain/Application layer defines the contract
    - Infrastructure adapters implement it (e.g., GoodreadsProvider, StravaProvider)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this provider (e.g., 'garmin', 'goodreads')."""
        ...

    @abstractmethod
    def fetch_data(self, habit: Habit, date: str) -> float | None:
        """
        Fetch habit value for a specific date from external source.

        Args:
            habit: The habit configuration (includes provider_config)
            date: ISO format date string (YYYY-MM-DD)

        Returns:
            The habit value for that date, or None if unavailable
        """
        ...
